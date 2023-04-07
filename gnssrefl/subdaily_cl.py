import argparse
import numpy as np
import matplotlib.pyplot as mplt

import os
import sys
import subprocess

import gnssrefl.gps as g
import gnssrefl.subdaily as t

from gnssrefl.utils import str2bool


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", default=None, type=int, help="for now one year at a time")
    parser.add_argument("-txtfile_part1", default=None, type=str, help="optional filename,first section of code (gross outlier detection), must be in gnssir output format") 
    parser.add_argument("-txtfile_part2", default=None, type=str, help="optional filename,second section of code (Rhdot calculation, splines), must be gnssir output format ") 
    parser.add_argument("-csvfile", default=None, type=str, help="set to True if you prefer csv to plain txt")
    parser.add_argument("-plt", default=None, type=str, help="set to False to suppress plots")
    parser.add_argument("-spline_outlier1", default=None, type=float, help="outlier criterion used in first splinefit (meters)")
    parser.add_argument("-spline_outlier2", default=None, type=float, help="outlier criterion used in second splinefit (meters)")
    parser.add_argument("-knots", default=None, type=int, help="Knots per day, spline fit only (default is 8)")
    parser.add_argument("-sigma", default=None, type=float, help="simple sigma outlier criterion (e.g. 1 for 1sigma, 3 for 3sigma)")
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
    parser.add_argument("-delta_out", default=None, type=int, help="Output interval for spline fit, seconds (default is 1800)")
    parser.add_argument("-if_corr", default=None, type=str, help="Interfrequency correction applied, optional")
    parser.add_argument("-knots_test", default=None, type=int, help="test knots")

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['csvfile', 'plt', 'rhdot', 'testing','kplt','if_corr']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def subdaily(station: str, year: int, txtfile_part1: str = '', txtfile_part2: str = None, csvfile: bool = False, 
        plt: bool = True, spline_outlier1: float = None, spline_outlier2: float = None, 
        knots: int = 8, sigma: float = 2.5, extension: str = '', rhdot: bool = True, doy1: int = 1, 
        doy2: int = 366, testing: bool = True, ampl: float = 0, h1: float=0.0, h2: float=300.0, 
        azim1: int=0, azim2: int = 360, peak2noise: float = 0, kplt: bool = False, 
        subdir: str = None, delta_out : int = 1800, if_corr: bool = True, knots_test: int = 0):
    """
    subdaily combines multiple day gnssir solutions and applies relevant corrections. 
    It works on one year at a time; you can restricts time periods within a year with -doy1 and -doy2

    Examples
    --------

    subdaily at01 2023 -plt F
        for station at01, all solutions in 2023  but no plots to the screen

    subdaily at01 2023 -doy1 15 -doy2 45
        for all solutions in 2023 between days of year 15 through 45

    subdaily at01 2023 -h2 14 -if_corr F
        for all solutions in 2023 but with max RH set to 14 meters and interfrequency correction not applied 

    The code has two sections. 

    I. Summarize the retrievals (how many retrievals per constellation), identify and remove gross outliers.
    provide plots to allow a user to evaluate Quality Control parameters. The solutions can further be edited from
    the command line (i.e. restrict the RH using -h1 and -h2, in meters, or azimuths using -azim1 and -azim2)

    II. This section has the following goals:

    - removes more outliers based on a spline fit to the RH retrievals

    - calculates and applies RHdot

    - removes an interfrequency (IF) bias. All solutions are then relative to GPS L1.

    txtfile_part1 is optional input if you want to skip part 1 and use your own file (but in the same format).

    txtfile_part2 is optional input to the second part of the code.


    Parameters
    ----------

    station : str
        4 character id of the station.
    year : int
        full year
    txtfile_part1 : str, optional
        input File name.
    txtfile_part2 : str, optional
        Input filename for rhdot/spline fitting
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
    extension : string, optional
        Solution subdirectory.
        default is empty string.
    rhdot : boolean, optional
        Set to True to turn on spline fitting for RHdot correction.
        default is True.
    doy1 : integer, optional
        Initial day of year
        default is 1.
    doy2 : integer, optional
        End day of year.
        default is 366.
    testing : boolean, optional
        Set to False for older code.
        default is now True.
    ampl : float, optional
        New amplitude constraint
        default is 0.
    azim1: int, optional
        New min azimuth
        default is 0.
    azim2: int, optional
        New max azimuth
        default is 360.
    h1: float optional 
        lowest allowed reflector height
        default is 0
    h2: float optional 
        highest allowed reflector height
        default is 300
    peak2noise: float, optional
        New peak to noise constraint
        default is 0.
    kplt: boolean, optional
        plot for kristine
    subdir : str, optional
        name for output subdirectory in REFL_CODE/Files

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
    g.set_subdir(subdir)

    txtdir = xdir + '/Files/' + subdir

    #create the subdaily file
    writecsv = False
    if (h1 > h2):
        print('h1 must be less than h2. You submitted ', h1, ' and ', h2)
        sys.exit()
    if csvfile:
        print('>>>> WARNING: csvfile option is currently turned off.  We are working to add it back.')
        csvfile = False

    if csvfile:
        writecsv = True

    if txtfile_part2 is None:
        if txtfile_part1 == '':
            print('Will pick up and concatenate daily result files')
        else:
            print('Using ', txtfile_part1)
        # if txtfile provided, you can use that as your starting dataset 
        
        default_usage = True
        ntv, obstimes, fname, fname_new = t.readin_and_plot(station, year, doy1, doy2, plt, 
                extension, sigma, writecsv, azim1, azim2, ampl, peak2noise, txtfile_part1,h1,h2,kplt,txtdir,default_usage)
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
    input2spline = fname_new; output4spline = fname_new + '.withrhdot'

    # not sure why tv and corr are being returned.
    if rhdot:
       tv, corr = t.rhdot_correction2(station, input2spline, output4spline, plt, spline_outlier1, spline_outlier2, 
                   knots=knots,txtdir=txtdir,testing=testing,delta_out=delta_out,if_corr=if_corr,knots_test=knots_test)
       if plt:
           mplt.show()

def main():
    args = parse_arguments()
    subdaily(**args)


if __name__ == "__main__":
    main()
