import argparse
import matplotlib.pyplot as matplt
import numpy as np
import datetime 
import os
import sys

import gnssrefl.gps as g
import gnssrefl.snow_functions as sf
import gnssrefl.daily_avg_cl as da

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
    parser.add_argument("-plt_enddate", help="end date for the plot/snow solns, yyyy-mm-dd", type=str, default=None)
    parser.add_argument("-plt", help="whether you want the plot to come to the screen", type=str, default=None)
    parser.add_argument("-simple", help="use simple algorithm (default is false)", type=str, default=None)
    parser.add_argument("-medfilter", help="median filter for daily average(m)", type=float, default=None)
    parser.add_argument("-ReqTracks", help="how many arcs needed for daily average)", type=int, default=None)
    parser.add_argument("-fr", help="if you want to restrict to a single frequency", type=int, default=None)
    parser.add_argument("-barereq_days", help="how many bare soil values req (default is 15)", type=int, default=None)
    parser.add_argument("-hires_figs", help="if you want eps instead of png plots", type=str, default=None)

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['longer','plt','simple','hires_figs']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def snowdepth(station: str, year: int, minS: float=None, maxS: float=None,
        longer:bool=False, plt:bool=True, bare_date1:str=None, bare_date2:str=None, plt_enddate:str=None, simple:bool=False, 
              medfilter:float = None, ReqTracks: int = None, barereq_days: int = 15, 
              fr: int = None, hires_figs : bool = False):
    """
    Calculates snow depth for a given station and water year.
    Before you run this code you must have run gnssir for each day of interest.  

    You can then run daily_avg to concatenate the results or you can input appropriate 
    values to optional inputs medfilter and ReqTracks.  

    Currently set for northern hemisphere constraints. This could easily be fixed for 
    the southern hemisphere by reading the json input file.
    Default values use the median of September results to set "bare soil value"
    These can be overriden with bare_date1 and bare_date2 (as one would do in Alaska)

    Output is currently written to a plain text file and a plot is written to a png file.
    Both are located in the $REFL_CODE/Files/station directory

    If simple is set to true, the algorithms computes bare soil (and thus snow depth), using
    all values together.  The default defines bare soil values every 10 degrees in azimuth.  

    2024 Feb 6 : stopped the code from setting snowdepth values < 5 cm to zero. This means that
    "negative" snowdepth will be in the files, but it should not be interpreted to be a new
    form of snow.

    Examples
    --------
    snowdepth p101 2022
        would use results from a previous run of daily_avg

    snowdepth p101 2022 -medfilter 0.25 -ReqTracks 50
        would run daily_avg for you using 50 tracks/0.25 meter median filter

    Parameters
    ----------
    station : str
        4 character station name
    year : int
        water year (i.e. jan-june of that year and oct-dec of the previous year)
    minS : float, optional
        minimum snow depth for y-axis limit (m), optional
    maxS : float, optional
        maximum snow depth for y-axis limit (m), optional
    longer : bool, optional
        whether you want to plot longer time series (useful for Alaskan sites)
    plt : bool, optional
        whether you want the plot to come to the screen
    bare_date1: str, optional
        an override for start bare soil definition 
    bare_date2: str, optional
        an override for end bare soil definition 
    plt_enddate: str, optional
        an override for where you want the plot to end earlier than default
    simple: bool, optional
        whether you want to use simple algoirthm. Default is False
        which means you use azimuth corrected bare soil values
    medfilter: float, optional
        to avoid running daily_avg, you can set median filter in meters;
        this is used to remove large outliers
    ReqTracks: int, optional
        to avoid running daily_avg, you can set required number of tracks 
        to create a daily average RH
    barereq_days: int, optional
        how many bare soil days are required to trust the result, default is 15
    fr : int, optional
        if you want to restrict to a single frequency at the daily-avg stage (1, 20, etc)
    hires_figs :  bool, optional
        whether you want eps instead of png plots

    """
    if (medfilter is not None) and (ReqTracks is not None):
        print('Running daily average')
        txtfile=None; pltit = False
        if fr is not None:
            da.daily_avg(station, medfilter, ReqTracks,  txtfile,pltit,'',2005,2030,fr,False,0,360,False,None)
        else:
            da.daily_avg(station, medfilter, ReqTracks,  txtfile,pltit,'',2005,2030,0,False,0,360,False,None)
        # do not display these plots
        matplt.close ('all')

    # default days of year used for bare soil
    # september from the fall
    doy1 = 244 
    doy2 = 274
    bs = year - 1

    xdir = os.environ['REFL_CODE']
    g.checkFiles(station,'')
    direc = xdir + '/Files/' + station  + '/' 

#   read input file
    if simple:
        gpsfile = direc + station + '_dailyRH.txt'
    else:
        gpsfile = direc + station + '_AllRH.txt'

#   define output files
    outputfile = direc + 'SnowAvg_' + str(year) +'.txt'
    if hires_figs : 
        outputpng = direc + 'water_' + str(year) +'AV.eps'
    else:
        outputpng = direc + 'water_' + str(year) +'AV.png'

    if os.path.exists(gpsfile):
        gps = np.loadtxt(gpsfile,comments='%')
    else:
        print('The input file needed for this code does not exist', gpsfile)
        print('You either need to run daily_avg manually or provide optional inputs here for medfilter and ReqTracks. Exiting')
        sys.exit()

    print('Input file',gpsfile)
    print('Output file: ',outputfile)
    print('Output png: ',outputpng)

    if plt_enddate is not None:
        pyear = int(plt_enddate[0:4])
        pmonth = int(plt_enddate[5:7])
        pday = int(plt_enddate[8:10])
        yend, end_doy = g.cdate2ydoy(plt_enddate)

        end_dt = datetime.datetime(year=pyear, month=pmonth, day = pday)
    else:
        end_doy = None
        end_dt = None


    # this overrides other ways of doing things.
    if bare_date1 is not None:
        bs, doy1 = g.cdate2ydoy(bare_date1)
    if bare_date2 is not None:
        rrrr, doy2 = g.cdate2ydoy(bare_date2)

    if simple:
        sf.snow_simple(station,gps,year,longer, doy1,doy2,bs,plt, end_dt,outputpng,
                outputfile,minS,maxS,barereq_days,end_doy)
    else:
        sf.snow_azimuthal(station,gps,year,longer, doy1,doy2,bs,plt, end_dt,
                outputpng,outputfile,minS,maxS,barereq_days,end_doy)

def main():
    args = parse_arguments()
    snowdepth(**args)


if __name__ == "__main__":
    main()

