import datetime
import numpy as np
import sys

import gnssrefl.gps as g
import gnssrefl.sd_libs as sd

# https://tides.gc.ca/en/stations/00270
# https://tides.gc.ca/en/stations/00270/2025-10-17?tz=UTC&unit=m

def read_predicts(f):
    """
    reads canadian government csv file and returns 
    mjd and tide 

    Parameters
    ----------
    f : str
        filename

    Returns
    -------
    mjd : numpy array of floats
        modified julian day
    tide : numpy array of floats
        water level in meters

    """
    data = np.genfromtxt(f, comments='%', skip_header=1,skip_footer=1,dtype='str',delimiter=',')
    data = np.char.replace(data,' UTC','')
    mjd = []
    tide = []
    for i in range(0,len(data)):
        o=datetime.datetime.fromisoformat(data[i,0])
        ts = datetime.datetime.utctimetuple(o)
        year = ts.tm_year ; mm  = ts.tm_mon ; dd =  ts.tm_mday
        hh = ts.tm_hour ; minutes = ts.tm_min ; sec = 0
        m, f = g.mjd(year, mm, dd, hh, minutes, sec)
        mjd.append(m+f)
        tide.append(float(data[i,1]))

    mjd = np.asarray(mjd)
    tide = np.asarray(tide)

    return mjd, tide


def apply_new_azim_mask(file1):
    """
    Parameters
    ----------
    file1 : str
        observation file created by first part of subdaily

    Returns
    -------
    fout : str
        name of edited obseration file to be used by second
        part of subdaily 
    """
    # read in the first results file created by subdaily
    gnss = np.loadtxt(file1, comments='%')

    N = len(gnss)
    keep = np.empty(shape=[0, 22])


# read in the predicts from canada
    f='predicts_2025-10-17.csv'
    mjd, tide = read_predicts(f)

    x1 = int(min(mjd))
    x2 = int(max(mjd)) + 1
    print(x1,x2)
    bad_indices = []
    for m in range(x1, x2):
        tf1 = np.logical_and(mjd > m, mjd < (m+0.5))
        tf2 = np.logical_and(mjd > m+0.5, mjd < (m+1))
        if len(tide[tf1]) > 0 & len(tide[tf2]) & 0 : 
            i = np.argmin(tide[tf1])
            j = np.argmin(tide[tf2])
            print('low tide 1',  mjd[tf1][i], min(tide[tf1]) )
            print('low tide 2',  mjd[tf2][j], min(tide[tf2]) ) 
            bad_indices.append(mjd[tf1][i])
            bad_indices.append(mjd[tf2][j])

    BI = len(bad_indices)
    ijk = 0
    # loop thru the observations 
    for i in range(0,N):
    # so for each one check if it is near a low tide
    # and if so, check if azimuth is ok
        azim = gnss[i,5]
        mjd = gnss[i,15]
        newl = gnss[i,:]
        if azim < 240: # this could be 250 - dunno
            lowtide = False
            for w in range(0, BI):# check low tides
                if (mjd > bad_indices[w] - 2/24) &  (mjd < bad_indices[w]+2/24):
                    print('Excluding',round(mjd,3), 'Azimuth ', azim)
                    lowtide = True
                    ijk = ijk + 1

            if not lowtide:
                keep = np.vstack((keep, newl))
     
        else:
            keep = np.vstack((keep, newl))

    print('originally had ', N,  ' observations,  now ' , len(keep))
    # this is meant to be a temporay file
    # but someone should add a header - 
    fo  = "%4.0f %3.0f %7.3f %3.0f %6.3f %6.2f %6.2f %6.2f %6.2f %4.0f %3.0f "
    fo2 = "%2.0f %8.5f %6.2f %7.2f %12.6f %1.0f %2.0f %2.0f %2.0f %2.0f %2.0f"
    fm = fo + fo2
    fout = 'newone.txt'
    np.savetxt(fout, keep, fmt=fo+fo2)

    return fout

