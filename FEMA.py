## FEMA.py 
#
# Create text files for use in FEMA d3 visualization at http://www.libertyhamilton.com/fema/fema.html
# 
# Liberty Hamilton 2013
# Email liberty@libertyhamilton.com with questions or comments

import matplotlib
matplotlib.use('Agg')

## Import things we need ##
from matplotlib.pyplot import figure, show
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon
from matplotlib import cm
from mpl_toolkits.basemap import Basemap as Basemap
from matplotlib.colors import rgb2hex

import scipy.io as sio
from scipy import sparse
import numpy as np
import tables
import os
import shutil
import datetime as dt
from getFIPS import getFIPS
import csv
import locale

locale.setlocale(locale.LC_ALL, 'en_US')

convertfunc = lambda x: dt.datetime.strptime(x, '%m/%d/%Y')

if "femadata" not in locals():
    femadata = np.genfromtxt(file("FEMAp3.txt","U"), delimiter="\t", skip_header=0, dtype = None, names=True, converters={"Declaration_Date": convertfunc})
    FIPS = list()
    for fi, f in enumerate(femadata):
        FIPS.append(getFIPS(f[4], f[3]))


unique_counties = np.unique(FIPS)
dyears = np.array([femadata['Declaration_Date'][c].year for c in np.arange(len(femadata))])
dmonths = np.array([femadata['Declaration_Date'][c].month for c in np.arange(len(femadata))])
unique_years = np.unique(dyears)
#countysums = np.array([[femadata['Federal_Share_Obligated'][(FIPS==c) & (dyears==y)].sum() for c in unique_counties] for y in unique_years])
unique_incidents = np.unique(femadata['Incident_Type'])
incident_groups = dict({'Coastal Storm': 2, 
                       'Dam/Levee Break': 3,
                       'Drought': 0, 
                       'Earthquake': 1, 
                       'Fire': 0,
                       'Flood': 3, 
                       'Freezing': 4, 
                       'Hurricane': 2, 
                       'Other': 'Other', 
                       'Severe Ice Storm': 4,
                       'Severe Storm(s)': 2, 
                       'Snow': 4, 
                       'Terrorist': 5, 
                       'Tornado': 1, 
                       'Tsunami': 2,
                       'Typhoon': 2})


yearcountysums = []
yearcountyincidents = []
for y in unique_years:
    ydata = femadata['Federal_Share_Obligated'][dyears==y]
    idata = femadata['Incident_Type'][dyears==y]
    ycounties = np.array(FIPS)[dyears==y]
    countysums = []
    countyincidents = []
    for c in unique_counties:
        countysums.append(ydata[(ycounties==c)].sum())
        arr = idata[(ycounties==c)]
        u, indices = np.unique(arr, return_inverse=True)
        if len(u)>0:
            mostcommonind = u[np.argmax(np.bincount(indices))]
            countyincidents.append(incident_groups[mostcommonind])
        else:
            countyincidents.append('')
        
    yearcountyincidents.append(countyincidents)
    yearcountysums.append(countysums)

yearcountysumarray = np.array(yearcountysums)
yearcountyincidentsarray = np.array(yearcountyincidents)

for y in unique_years:
    ydata = femadata[dyears==y]
    ycounties = np.array(FIPS)[dyears==y]
    for c in np.unique(ycounties):
        txt2write = ydata[ycounties==c]
        fname = "countydata/%d_%d.tsv"%(y,c)
        with open(fname, 'wb') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter='\t',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
            spamwriter.writerow(['Date']+['Incident Type']+['Applicant Name']+['Education Applicant']+['Number of Projects']+['Federal Share Obligated'])
            for t in txt2write:
                spamwriter.writerow([str(t[1])[:10]]+[t[2]]+[t[5]]+[t[6]]+[t[7]]+["$"+locale.format("%.2f", t[8], grouping=True)])

monthyearcountysums = []
for y in unique_years:
    for m in range(1,13):
        ydata = femadata['Federal_Share_Obligated'][(dyears==y) & (dmonths==m)]
        ycounties = np.array(FIPS)[(dyears==y) & (dmonths==m)]
        countysums = []
        for c in unique_counties:
            countysums.append(ydata[(ycounties==c)].sum())

        monthyearcountysums.append(countysums)

monthyearcountysumarray = np.array(monthyearcountysums)

valmin = np.log(np.min(countysums[countysums>0]))
valmax = np.log(np.max(countysums))

with open('FEMA_by_year.tsv', 'wb') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter='\t',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(['id']+unique_years.tolist())
    for d in np.arange(yearcountysumarray.shape[1]):
        f_amt = np.log(1+yearcountysumarray.T[d])
        spamwriter.writerow([np.int(unique_counties[d])] + f_amt.tolist())

with open('Incident_by_county.tsv', 'wb') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter='\t',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(['id']+unique_years.tolist())
    for d in np.arange(yearcountyincidentsarray.shape[1]):
        f_amt = yearcountyincidentsarray.T[d]
        spamwriter.writerow([np.int(unique_counties[d])] + f_amt.tolist())

with open('FEMA_by_month_year.tsv', 'wb') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter='\t',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(['id']+range(1,181))
    for d in np.arange(monthyearcountysumarray.shape[1]):
        f_amt = np.log(1+monthyearcountysumarray.T[d])
        spamwriter.writerow([np.int(unique_counties[d])] + f_amt.tolist())
    
# Lambert Conformal map of lower 48 states.
m = Basemap(llcrnrlon=-119,llcrnrlat=22,urcrnrlon=-64,urcrnrlat=49,
            projection='lcc',lat_1=33,lat_2=45,lon_0=-95)

# Read county boundary lines from shapefile
shp_info = m.readshapefile('UScounties/UScounties','counties',drawbounds=True,color='none')
cmap = plt.cm.jet_r # use 'hot' colormap

colors ={}
countynames=[]
statenames = []

#print m.counties_info[0].keys()
for shapedict in m.counties_info:
    countyname = shapedict['NAME']
    statename = shapedict['STATE_NAME']
    countynames.append(countyname)
    statenames.append(statename)
    
# cycle through state names, color each one.
ax = plt.gca() # get current axes instance
for nshape,seg in enumerate(m.counties):
    if np.any(counties == countynames[nshape]): # if this county is in the FEMA DB
        if countysums[counties==countynames[nshape]]>0:
            f_amt = np.log(countysums[counties==countynames[nshape]])
            #print "County %s received %d in assistance"%(countynames[nshape], f_amt)
            c = (f_amt-valmin)/(valmax-valmin)
            
            color = rgb2hex(cmap(1-c)[0][:3]) 
            poly = Polygon(seg,facecolor=color,edgecolor=color)
            ax.add_patch(poly)
# draw meridians and parallels.
#plt.colorbar()
#m.drawparallels(np.arange(25,65,20),labels=[1,0,0,0])
#m.drawmeridians(np.arange(-120,-40,20),labels=[0,0,0,1])
plt.title('FEMA assistance by county')
plt.show()

femadata['Declaration_Date'] = numpy.array([datetime.datetime.strptime(s, '%m/%d/%Y') for s in femadata['Declaration_Date'].view("S10")])
