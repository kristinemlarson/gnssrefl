import argparse
import numpy as np
import datetime 
import matplotlib.pyplot as plt
import os
import sys

import gnssrefl.gps as g

from gnssrefl.utils import str2bool

def parse_arguments():
    # must input start and end year
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name (4 ch only)", type=str)
    parser.add_argument("year", help="Northern Hemisphere water year", type=int)
    parser.add_argument("-minS", help="y-axis minimum snow depth (m)", type=float,default=None)
    parser.add_argument("-maxS", help="y-axis maximum snow depth (m)", type=float,default=None)
    parser.add_argument("-doy1", help="min day of year for bare soil definition", type=int, default=None)
    parser.add_argument("-doy2", help="max day of year for bare soil definition", type=int, default=None)
    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    #boolean_args = ['plt', 'csv','test']
    boolean_args = []
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def snow_depth(station: str, year: int, minS: float=None, maxS: float=None, doy1:int=None, doy2:int=None ):
    """
    Calculates snow depth for a give station and water year.
    Currently set for northern hemisphere constraints.
    Default uses median of September to set "bare soil value"

    Eventually this will be command line driven (or will use json settings)

    Parameters
    ----------
    station : str
        4 character station name
    year : int
        water year (i.e. jan-june of that year and oct-dec of the previous year)
    minS : float

    maxS : float

    doy1 : int

    doy2 : int 

    """

    # default days of year used for bare soil
    if doy1 is None:
        doy1 = 245
    if doy2 is None:
        doy2 = 274

    xdir = os.environ['REFL_CODE']
    direc = xdir + '/Files/' + station  + '/' 

# read in the daily average RH file
    gpsfile = direc + station + '_dailyRH.txt'
    print(gpsfile)

    gps = np.loadtxt(gpsfile,comments='%')


# going to use august and mid-september to determine "no snow level"
# for other sites, you might be able to use all of september ...
# doy 213 through doy 258
# RH is stored in column 2, doy is in column 1
    ii = (gps[:,1] >= doy1) & ((gps[:,1] <= doy2) & (gps[:,0] == year-1))

    baresoil = gps[ii,2]
    if len(baresoil) == 0:
        print('No values in the bare soil definition. Exiting')
        print('Current settings are ', year-1, ' and ', doy1, doy2)
        sys.exit()

    # require at least 15 values
    NB = 15
    if len(baresoil) < NB:
        print('Not enough values to define baresoil: ', NB)
        sys.exit()

    noSnowRH = np.mean(baresoil)
    print('Bare Soil RH: ', '{0:7.3f}'.format( noSnowRH),'(m)' )

    # now compute snow depth
    startdoy, cdoy, cyyyy, cyy = g.ymd2doy(year-1,10,1)
    enddoy, cdoy, cyyyy, cyy = g.ymd2doy(year,6,30)

    starting = year-1 + startdoy/365.25
    ending = year + enddoy/365.25

    t = gps[:,0] + gps[:,1]/365.25
    ii = (t >= starting) & (t <=ending)
    usegps = gps[ii,:]
    if len(usegps) == 0:
        print('No data in this water year. Exiting')
        sys.exit()

    snowAccum = noSnowRH - usegps[:,2]
    # we do not allow negative snow depth ... or at least not < -0.025
    ii = (snowAccum > -0.025)
    usegps = usegps[ii,:]
    snowAccum = snowAccum[ii]


# make a datetime array for plotting the gps results
    gobst = np.empty(shape=[0, 1])
    for i in range(0,len(usegps)):
        gobst = np.append(gobst, datetime.datetime(year=int(usegps[i,0]), month=int(usegps[i,4]), day=int(usegps[i,5])))


    fig,ax=plt.subplots()
    # method does a poor job of measuring snow depth < 5 cm, so zero it out. 
    ii = (snowAccum < 0.05)
    snowAccum[ii] = 0
    plt.plot(gobst, snowAccum, 'b.',label='GPS-IR')
    plt.title('Snow Depth: ' + station) 
    plt.ylabel('meters')
    plt.grid()
    left = datetime.datetime(year=year-1, month=10, day = 1)
    right = datetime.datetime(year=year, month=6, day = 30)
    plt.xlim((left, right))
    fig.autofmt_xdate()
    if (minS is not None) and (maxS is not None):
        plt.ylim((-0.05+minS,maxS))

    plt.show()

def main():
    args = parse_arguments()
    snow_depth(**args)


if __name__ == "__main__":
    main()

