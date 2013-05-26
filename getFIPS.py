import numpy as np
FIPSdata = np.genfromtxt(file("FIPS.csv","U"), delimiter=",", skip_header=0, dtype = None, names=True)

def getFIPS(county, state):
    FIPS = FIPSdata['FIPS'][(FIPSdata['State']==state) & (FIPSdata['County']==county)]
    if FIPS:
        return FIPS[0]
    else:
        raise IndexError("No such county/state (%s %s)"%(county, state))