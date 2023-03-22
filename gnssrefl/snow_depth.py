import argparse
import numpy as np
import datetime 
import os
import sys

import gnssrefl.gps as g
import gnssrefl.snow_functions as sf

from gnssrefl.utils import str2bool

def parse_arguments():
    # must input start and end year
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name (4 ch only)", type=str)
    parser.add_argument("year", help="Northern Hemisphere water year", type=int)
    parser.add_argument("-minS", help="y-axis minimum snow depth (m)", type=float,default=None)
    parser.add_argument("-maxS", help="y-axis maximum snow depth (m)", type=float,default=None)
    parser.add_argument("-longer", help="plot longer series", type=str, default=None)
    parser.add_argument("-bare_date1", help="bare soil start yyyy-mm-dd", type=str, default=None)
    parser.add_argument("-bare_date2", help="bare soil end yyyy-mm-dd", type=str, default=None)
    parser.add_argument("-plt_enddate", help="end date for the plot, yyyy-mm-dd", type=str, default=None)
    parser.add_argument("-plt", help="whether you want the plot to come to the screen", type=str, default=None)
    parser.add_argument("-simple", help="use simple algorithm (default is false)", type=str, default=None)
    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    #boolean_args = ['plt', 'csv','test']
    boolean_args = ['longer','plt','simple']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def snow_depth(station: str, year: int, minS: float=None, maxS: float=None,
        longer:bool=False, plt:bool=True, bare_date1:str=None, bare_date2:str=None, plt_enddate:str=None,simple:bool=False):
    """
    Calculates snow depth for a given station and water year.
    Currently set for northern hemisphere constraints. This could easily be fixed for 
    the southern hemisphere by reading the json input file

    Default values use median of September to set "bare soil value"

    Eventually this will be command line driven (or will use json settings)

    Output is currently written to a plain text file and a png file
    Both are located in the $REFL_CODE/Files/station directory

    Parameters
    ----------
    station : str
        4 character station name
    year : int
        water year (i.e. jan-june of that year and oct-dec of the previous year)
    minS : float
        minimum snow depth for y-axis limit (m), optional
    maxS : float
        maximum snow depth for y-axis limit (m), optional
    longer : bool
        whether you want to plot longer time series (useful for Alaskan sites)
    plt : bool
        whether you want the plot to come to the screen
    bare_date1: str
        an override for start bare soil definition (used when data are unavailable for default settings )
    bare_date2: str
        an override for end bare soil definition (used when data are unavailable for default settings )
    plt_enddate: str
        an override for where you want the plot to end 
    simple: bool
        whether you want to use simple algoirthm. Default is False
        which means you use azimuth corrected bare soil values

    """

    # default days of year used for bare soil
    # september from the fall
    doy1 = 244 
    doy2 = 274
    bs = year - 1

    xdir = os.environ['REFL_CODE']
    direc = xdir + '/Files/' + station  + '/' 

#   read input file
    if simple:
        gpsfile = direc + station + '_dailyRH.txt'
    else:
        gpsfile = direc + station + '_AllRH.txt'

#   define output files
    outputfile = direc + 'SnowAvg_' + str(year) +'.txt'
    outputpng = direc + 'water_' + str(year) +'AV.png'
    print('Input file',gpsfile)
    print('Output file: ',outputfile)
    print('Output png: ',outputpng)

    if os.path.exists(gpsfile):
        gps = np.loadtxt(gpsfile,comments='%')
    else:
        print('Input file does not exist. Exiting')
        print(gpsfile)
        sys.exit()


    if plt_enddate is not None:
        pyear = int(plt_enddate[0:4])
        pmonth = int(plt_enddate[5:7])
        pday = int(plt_enddate[8:10])

        end_dt = datetime.datetime(year=pyear, month=pmonth, day = pday)
    else:
        end_dt = None

    # this overrides other ways of doing things.
    if bare_date1 is not None:
        bs, doy1 = g.cdate2ydoy(bare_date1)
    if bare_date2 is not None:
        rrrr, doy2 = g.cdate2ydoy(bare_date2)

    if simple:
        sf.snow_simple(station,gps,year,longer, doy1,doy2,bs,plt, end_dt,outputpng,outputfile,minS,maxS)
    else:
        sf.snow_azimuthal(station,gps,year,longer, doy1,doy2,bs,plt, end_dt,outputpng,outputfile,minS,maxS)

def main():
    args = parse_arguments()
    snow_depth(**args)


if __name__ == "__main__":
    main()

