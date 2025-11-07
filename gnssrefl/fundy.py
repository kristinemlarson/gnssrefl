import datetime
import numpy as np
import os
import sys

from scipy.signal import find_peaks

import gnssrefl.gps as g
import gnssrefl.sd_libs as sd



# https://tides.gc.ca/en/stations/00270
# https://tides.gc.ca/en/stations/00270/2025-10-17?tz=UTC&unit=m
# web service
# https://tides.gc.ca/en/web-services-offered-canadian-hydrographic-service
# https://api.iwls-sine.azure.cloud-nuage.dfo-mpo.gc.ca/swagger-ui/index.html

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
    print(f)
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


def apply_new_azim_mask(station,file1,predictf,timeOffset):
    """
    Parameters
    ----------
    station : str
        4 ch station name
    file1 : str
        observation file created by first part of subdaily
    predictf : str
        file of predicts downloaded from Canadian tide gauge site
    timeOffset : float
        how much time (in hours) from low tide triggers data deletion

    Returns
    -------
    fout : str
        name of edited obseration file to be used by second
        part of subdaily 
    """
    # read in the first results file created by subdaily
    if os.path.isfile(file1):
        gnss = np.loadtxt(file1, comments='%')
    else:
        print('I could not find the gnssir observation file needed by the Fundy module.')
        print(file1)
        print('This should have been created by the first section of the subdaily code.')
        sys.exit()

    N = len(gnss)
    keep = np.empty(shape=[0, 22])


    # will look at current directory and this directory for hte prediction file
    xf1 = os.environ['REFL_CODE'] + '/input/' + station + '/' + predictf

    if os.path.isfile(predictf):
        mjd, tide = read_predicts(predictf)
    elif os.path.isfile(xf1):
        mjd, tide = read_predicts(xf1)
    else:
        print('I cannot find the file that you indicated had the tidal predictions in it. Exiting.')
        sys.exit()


    actual_low_indices,actual_high_indices = better_high_low_tide(mjd,tide)
    bad_low_indices = mjd[actual_low_indices]
    bad_high_indices = mjd[actual_high_indices]


    BI = len(bad_low_indices)
    BI_high = len(bad_high_indices)
    ijk = 0
    # loop thru the observations 
    #removeCrit = 2.25 # hours
    # now an input variable
    removeCrit = timeOffset
    for i in range(0,N):
    # so for each one check if it is near a low tide
    # and if so, check if azimuth is ok
        azim = gnss[i,5]
        mjd = gnss[i,15]
        newl = gnss[i,:]
        e1 = gnss[i,7]
        e2 = gnss[i,8]
        if azim < 240: # this could be 250 - dunno
            lowtide = False
            for w in range(0, BI):# check low tides
                if (mjd > bad_low_indices[w] - removeCrit/24) &  (mjd < bad_low_indices[w]+removeCrit/24):
                    #print('Excluding',round(mjd,3), 'Azimuth ', azim)
                    lowtide = True
                    ijk = ijk + 1
            if not lowtide:
                keep = np.vstack((keep, newl))

        else:
            # only do this for the 5-10 elevation angle bins
            if (e2 > 6):
                hightide = False
                for w in range(0, BI_high):# check high tides
                    if (mjd > bad_high_indices[w] - removeCrit/24) &  (mjd < bad_high_indices[w]+removeCrit/24):
                        hightide = True
                if hightide:
                    keep = np.vstack((keep, newl))

                # only keep at high tide
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

def better_high_low_tide(mjd,water_level):
    """
    """

    # Find high tides (peaks in the original data)
    high_tide_indices, _ = find_peaks(water_level, distance=730)
    # Find low tides (peaks in the inverted data)
    low_tide_indices, _ = find_peaks(-water_level, distance=730)

    high_tide_times = mjd[high_tide_indices]
    high_tide_levels = water_level[high_tide_indices]
    low_tide_times = mjd[low_tide_indices]
    low_tide_levels = water_level[low_tide_indices]

    for i in range(0,len(low_tide_times)):
        print('low tide ',  sd.mjd_to_obstimes(low_tide_times[i]),  low_tide_levels[i])

    return low_tide_indices, high_tide_indices


def dumb_high_low_tide(mjd,tide):
    """
    goofy way i was originally getting daily high/low tides ...

    """
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
            lowtide1 =  sd.mjd_to_obstimes(mjd[tf1][i])
            lowtide2 =  sd.mjd_to_obstimes(mjd[tf2][j])
            print('low tide 1',  lowtide1,  min(tide[tf1]) )
            #print('low tide 1',  lowtide1, mjd[tf1][i], min(tide[tf1]) )
            print('low tide 2',  lowtide2,  min(tide[tf2]) )
            #print('low tide 2',  lowtide2, mjd[tf2][j], min(tide[tf2]) )
            bad_indices.append(mjd[tf1][i])
            bad_indices.append(mjd[tf2][j])

    return bad_indices

