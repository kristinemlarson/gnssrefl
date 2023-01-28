import argparse
import numpy as np
import datetime 
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
    parser.add_argument("-longer", help="plot longer series", type=str, default=None)
    parser.add_argument("-plt", help="whether you want the plot to come to the screen", type=str, default=None)
    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    #boolean_args = ['plt', 'csv','test']
    boolean_args = ['longer','plt']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def snow_depth(station: str, year: int, minS: float=None, maxS: float=None, doy1:int=None, doy2:int=None, longer:bool=False, plt:bool=True):
    """
    Calculates snow depth for a given station and water year.
    Currently set for northern hemisphere constraints. This could easily be fixed for 
    the southern hemisphere by reading the json input file

    Default values use median of September to set "bare soil value"

    Eventually this will be command line driven (or will use json settings)

    Output is currently plain text and a png file

    Parameters
    ----------
    station : str
        4 character station name
    year : int
        water year (i.e. jan-june of that year and oct-dec of the previous year)
    minS : float
        minimum snow depth for y-axis limit (m)
    maxS : float
        maximum snow depth for y-axis limit (m)
    doy1 : int
        minimum day of year used to set bare soil value
    doy2 : int 
        maximum day of year used to set bare soil value
    longer : bool
        whether you want to plot longer time series (useful for Alaskan sites)
    plt : bool
        whether you want the plot to come to the screen

    """

    # default days of year used for bare soil
    if doy1 is None:
        doy1 = 244 
    if doy2 is None:
        doy2 = 274

    xdir = os.environ['REFL_CODE']
    direc = xdir + '/Files/' + station  + '/' 

# read in the daily average RH file
# define names of outputs
    gpsfile = direc + station + '_dailyRH.txt'
    outputfile = direc + 'SnowAvg_' + str(year) +'.txt'
    outputpng = direc + 'water_' + str(year) +'AV.png'
    print('Input file',gpsfile)
    print('Output file: ',outputfile)
    print('Output png: ',outputpng)

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
    if longer:
        startdoy, cdoy, cyyyy, cyy = g.ymd2doy(year-1,8,1)
        # for plot
        left = datetime.datetime(year=year-1, month=8, day = 1)
    else:
        startdoy, cdoy, cyyyy, cyy = g.ymd2doy(year-1,10,1)
        left = datetime.datetime(year=year-1, month=10, day = 1) 

    # xaxis limit for the plot
    right = datetime.datetime(year=year, month=6, day = 30)

    enddoy, cdoy, cyyyy, cyy = g.ymd2doy(year,6,30)

    # simple minded extracting the data for given limits
    starting = year-1 + startdoy/365.25
    ending = year + enddoy/365.25
    #print(starting, ending)

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
    # error bar is just the std about the mean.  so it is likely bigger than needed.
    yerr = usegps[:,6]

    fout = open(outputfile, 'w+')
    line1 = '% snow depth for station ' + station
    line2 = '% year   doy  snowD(m) Std(m) Month Day '
    line3 = '%  (1)   (2)    (3)     (4)   (5)   (6)'
    fout.write("{0:s}  \n".format(line1))
    fout.write("{0:s}  \n".format(line2))
    fout.write("{0:s}  \n".format(line3))


# make a datetime array for plotting the gps results
    gobst = np.empty(shape=[0, 1])
    for i in range(0,len(usegps)):
        y=int(usegps[i,0])
        m=int(usegps[i,4])
        d=int(usegps[i,5])
        doy=int(usegps[i,1])
        # this is what we did in pboh2o
        if snowAccum[i] < 0.05:
            snowAccum[i] = 0

        gobst = np.append(gobst, datetime.datetime(year=y, month=m, day=d) )
        fout.write("{0:4.0f} {1:3.0f}  {2:8.3f}  {3:8.3f}  {4:2.0f}  {5:2.0f} \n".format(y,doy,snowAccum[i], yerr[i], m, d))

    fout.close()

    # make a plot
    g.snowplot(station,gobst,snowAccum,yerr,left,right,minS,maxS,outputpng,plt)

def main():
    args = parse_arguments()
    snow_depth(**args)


if __name__ == "__main__":
    main()

