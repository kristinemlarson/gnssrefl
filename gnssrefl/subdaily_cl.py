import argparse
import numpy as np
import matplotlib.pyplot as mplt

import os
import subprocess
import sys

import gnssrefl.gps as g
import gnssrefl.subdaily as t

from gnssrefl.utils import str2bool


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", default=None, type=int, help="year of data")
    parser.add_argument("-year_end", default=None, type=int, help="Allow multiple years of inputs by specifying last year")
    parser.add_argument("-txtfile_part1", default=None, type=str, help="optional filename (part1), must be in gnssir output format") 
    parser.add_argument("-txtfile_part2", default=None, type=str, help="optional filename (part2), must be gnssir output format ") 
    parser.add_argument("-csvfile", default=None, type=str, help="set to True if you prefer csv to plain txt")
    parser.add_argument("-plt", default=None, type=str, help="set to False to suppress plots")
    parser.add_argument("-spline_outlier1", default=None, type=float, help="outlier criterion used in first splinefit (meters)")
    parser.add_argument("-spline_outlier2", default=None, type=float, help="outlier criterion used in second splinefit (meters)")
    parser.add_argument("-knots", default=None, type=int, help="Knots per day, spline fit only (default is 8)")
    parser.add_argument("-sigma", default=None, type=float, help="part1 outlier criterion, float, default is 2.5 (sigma)")
    parser.add_argument("-extension", default=None, type=str, help="solution subdirectory")
    parser.add_argument("-rhdot", default=None, type=str, help="set to False if you want to stop after section 1 of the QC code")
    parser.add_argument("-doy1", default=None, type=int, help="initial day of year")
    parser.add_argument("-doy2", default=None, type=int, help="end day of year")
    parser.add_argument("-testing", default=None, type=str, help="set to False for old code ")
    parser.add_argument("-ampl", default=None, type=float, help="new amplitude constraint")
    parser.add_argument("-azim1", default=None, type=int, help="new min azimuth")
    parser.add_argument("-azim2", default=None, type=int, help="new max azimuth")
    parser.add_argument("-h1", default=None, type=float, help="min RH (m)")
    parser.add_argument("-h2", default=None, type=float, help="max RH (m)")
    parser.add_argument("-peak2noise", default=None, type=float, help="new peak2noise constraint")
    parser.add_argument("-kplt", default=None, type=str, help="special plot for kristine")
    parser.add_argument("-subdir", default=None, type=str, help="non-default subdirectory for output")
    parser.add_argument("-delta_out", default=None, type=int, help="Output interval for final spline fit, seconds (default is 1800)")
    parser.add_argument("-if_corr", default=None, type=str, help="Whether interfrequency correction is applied, optional")
    parser.add_argument("-knots_test", default=None, type=int, help="test knots")
    parser.add_argument("-hires_figs", default=None, type=str, help="hi-resolution eps figures, default is False")
    parser.add_argument("-apply_rhdot", default=None, type=str, help="apply rhdot, default is True")
    parser.add_argument("-fs", default=None, type=int, help="fontsize for figures. default is 10")
    parser.add_argument("-alt_sigma", default=None, type=str, help="boolean test for alternate Nievinski sigma definition. default is False")
    parser.add_argument("-gap_min_val", default=None, type=float, help="min gap allowed in splinefit output file. default is 6 hours")
    parser.add_argument("-knots2", default=None, type=int, help="Secondary knots value for final fit. default is to use original knots value.")

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['csvfile', 'plt', 'rhdot', 'testing','kplt','if_corr','hires_figs','apply_rhdot','alt_sigma']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def subdaily(station: str, year: int, txtfile_part1: str = '', txtfile_part2: str = None, csvfile: bool = False, 
        plt: bool = True, spline_outlier1: float = None, spline_outlier2: float = None, 
        knots: int = 8, sigma: float = 2.5, extension: str = '', rhdot: bool = True, doy1: int = 1, 
        doy2: int = 366, testing: bool = True, ampl: float = 0, h1: float=0.4, h2: float=300.0, 
        azim1: int=0, azim2: int = 360, peak2noise: float = 0, kplt: bool = False, 
        subdir: str = None, delta_out : int = 1800, if_corr: bool = True, knots_test: int = 0, 
             hires_figs : bool=False, apply_rhdot : bool=True, fs: int = 10, alt_sigma: bool= False, gap_min_val: float=6.0,
             year_end: int=None, knots2 : int=None):
    """
    Subdaily combines gnssir solutions and applies relevant corrections needed to measure water levels (tides). 
    As of January 2024, it will allow multiple years. You can also specify which day of year to start with, i.e.
    -doy1 300 and -doy2 330 will do that range in a single year, or you could specific doy1 and doy2 as linked to 
    the start and stop year (year and year_end)

    In general this code is meant to be used at sites with tidal signals. If you have a site 
    without tidal signals, you should consider using daily_avg instead. If you would still 
    like to use this code for rivers and lakes, you should change the defaults for the spline 
    fits. For tidal sites, 8 knots per day is the default. For nearly stationary surfaces, as you 
    would expect for a lake or river, you should use many fewer knots per day.

    This code calculates and applies various corrections. New Reflector Height values are added 
    to the output files as new columns. If you run the code but continue to assume the "good answers" are
    in still in column 3, you are essentially not using the code at all.

    As of version 2.0.0:

    The final output of subdaily is a smooth spline fit to reflector heights (RH) which has been 
    adjusted to mean sea level (meters). For this to be accurate, the user is asked to provide the orthometric height
    of the L1 GPS antenna phase center. This value should be stored as Hortho in the gnssir analysis strategy file
    (ssss.json where ssss is the 4 character station name). The output water levels are then defined as Hortho minus RH. 
    If the user does not provide Hortho, one is computed from the station ellipsoidal height stored in the gnssir 
    analysis strategy file and EGM96.

    The subdaily code has two main sections. 

    I. Summarize the retrievals (how many retrievals per constellation), identify and remove 
    gross outliers, provide plots to allow a user to evaluate Quality Control parameters. The 
    solutions can further be edited from the command line (i.e. restrict the RH using 
    -h1 and -h2, in meters, or azimuths using -azim1 and -azim2)

    II. This section has the following goals:

    - removes more outliers based on a spline fit to the RH retrievals

    - calculates and applies RHdot correction

    - removes an interfrequency (IF) bias. All solutions are then relative to GPS L1.

    txtfile_part1 is optional input if you want to skip concatenating daily gnssir output files 
    and use your own file. Make sure results are in the same format.

    txtfile_part2 is optional input that skips part 1 and uses this file as input to 
    the second part of the code.

    Examples
    --------
    subdaily at01 2023 -plt F
        for station at01, all solutions in 2023  but no plots to the screen

    subdaily at01 2023 -doy1 15 -doy2 45
        for all solutions in 2023 between days of year 15 through 45

    subdaily at01 2023 -h2 14 -if_corr F
        for all solutions in 2023 but with max RH set to 14 meters and interfrequency correction not applied 

    subdaily at01 2022 -year_end 2023
        analyze all data for years 2022 and 2023

    subdaily at03 2022 -azim1 180 -azim2 270
        restrict solutions to azimuths between 180 and 270

    Parameters
    ----------
    station : str
        4 character id of the station.
    year : int
        full year
    txtfile_part1 : str, optional
        input File name for part 1.
    txtfile_part2 : str, optional
        Input filename for part 2.
    csvfile: boolean, optional
        Set to True if you prefer csv to plain txt.
        default is False.
    plt : bool, optional
        To print plots to screen or not.
        default is TRUE.
    spline_outlier1 : float, optional
        Outlier criterion used in first splinefit, before RHdot  (m)
    spline_outlier2 : float, optional
        Outlier criterion used in second splinefit, after IF & RHdot (meters)
    knots : integer, optional
        Knots per day, spline fit only.
        default is 8.
    sigma : float, optional
        Simple sigma outlier criterion (e.g. 1 for 1sigma, 3 for 3sigma)
        default is 2.5
    extension : str, optional
        Solution subdirectory.
        default is empty string.
    rhdot : bool, optional
        Set to True to turn on spline fitting for RHdot correction.
        default is True.
    doy1 : int, optional
        Initial day of year, default is 1.
    doy2 : int, optional
        End day of year. Default is 366.
    testing : bool, optional
        Set to False for older code.
        default is now True.
    ampl : float, optional
        New amplitude constraint. Default is 0.
    azim1: int, optional
        minimum azimuth. Default is 0.
    azim2: int, optional
        Max azimuth. Default is 360.
    h1: float, optional 
        lowest allowed reflector height in meters. Default is 0.4
    h2: float, optional 
        highest allowed reflector height in meters. Default is 300
    peak2noise: float, optional
        New peak to noise constraint. Default is 0.
    kplt: bool, optional
        plot for kristine
    subdir : str, optional
        name for output subdirectory in REFL_CODE/Files
    delta_out : int, optional
        how frequently - in seconds - you want smooth spline model output written
        default is 1800 seconds
    if_corr : bool, option
        whether you want the inter-frequency removed
        default is true
    hires_figs : bool, optional
        whether high resolution figures are made
    apply_rhdot : bool, optional
        whether you want the RH dot correction applied
        for a lake or river you would not want it to be.
    fs : int, optional
        fontsize for Figures. default is 10 for now.
    alt_sigma : bool, optional
        whether you want to use Nievinski definition for outlier criterion.
        in part 1 of the code (the crude outlier detector)
    gap_min_val : float, optional
        removes splinefit values from output txt and plot for gaps 
        bigger than this value, in hours
    year_end : int, optional
        last year of analysis period.  

    """

    if len(station) != 4:
        print('station names must be four characters long')
        sys.exit()

    # make surer environment variables are set
    g.check_environ_variables()
    xdir = os.environ['REFL_CODE']

    # default subdirectory is the station name
    if subdir == None:
        subdir = station
    # this makes sure the directory exists
    g.set_subdir(subdir)

    g.checkFiles(station, extension)

    # this should no longer be needed
    if extension == '':
        txtdir = xdir + '/Files/' + subdir
    else:
        txtdir = xdir + '/Files/' + subdir + '/' + extension

    print('Using this directory for output: ', txtdir)


    #create the subdaily file
    writecsv = False
    if (h1 > h2):
        print('h1 must be less than h2. You submitted ', h1, ' and ', h2)
        sys.exit()
    if csvfile:
        print('>>>> WARNING: csvfile option is currently turned off.  We are working to add it back.')
        csvfile = False

    outputs = [] # this is for multiple years

    if csvfile:
        writecsv = True
    if year_end is None: 
        year_end = year

    year_start = year

    multiyear = True
    if year_start == year_end:
        multiyear = False

    year_list = list(range(year, year_end+1))

    if txtfile_part2 is None:
        if txtfile_part1 == '':
            print('Will pick up and concatenate daily result files')
        else:
            print('Using ', txtfile_part1)
        # if txtfile provided, you can use that as your starting dataset 
        
        default_usage = True

        for y in range(year,year_end+1):
            dec31 = g.dec31(y)  # find doy for dec 31
            if not multiyear:
                doy_st = doy1
                doy_en = doy2
            else:
                if (y == year_end):
                    doy_st = 1
                    doy_en = doy2
                elif (y == year_start): 
                    doy_st = doy1
                    doy_en = dec31
                else:
                # in between year
                    doy_st = 1
                    doy_en = dec31

            print('Reading in the results for year: ', y, ' and doys ',  doy_st, ':', doy_en)

            ntv, obstimes, fname, fname_new = t.readin_and_plot(station, y, doy_st, doy_en, plt, \
                    extension, sigma, writecsv, azim1, azim2, ampl, peak2noise, txtfile_part1, \
                    h1,h2,kplt,txtdir,default_usage,hires_figs,fs,alt_sigma=alt_sigma)
            outputs.append(fname_new)

        haveObstimes = True
    else:
        haveObstimes = False
        fname_new = txtfile_part2
        if not os.path.isfile(fname_new):
            print('Input subdaily RH file you provided does not exist:', fname_new)
            sys.exit()

    # if you are not going to the second part of the code, display the plots, if requested. 
    if not rhdot:
        if plt:
            mplt.show()
    # only read in one year
    if year_end == year:
        input2spline = [fname_new]; output4spline = fname_new + '.withrhdot'

    # this is for multiyaer
    else:
        # this is a bit of a kluge - send it names of the yearly files
        input2spline = outputs 
        output4spline = txtdir + '/' + station + '_' + str(year) + '_' + str(year_end) + '.withrhdot'

    # not sure why tv and corr are being returned.
    if rhdot:
       tv, corr = t.rhdot_correction2(station, input2spline, output4spline, plt, spline_outlier1, spline_outlier2, 
                   knots=knots,txtdir=txtdir,testing=testing,delta_out=delta_out,
                   if_corr=if_corr,knots_test=knots_test,hires_figs=hires_figs,
                   apply_rhdot=apply_rhdot,fs=fs,gap_min_val=gap_min_val,year=year,extension=extension,knots2=knots2)
       if plt:
           mplt.show()

def main():
    args = parse_arguments()
    subdaily(**args)


if __name__ == "__main__":
    main()
