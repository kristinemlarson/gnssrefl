# preliminary water analysis to apply RHdot correction
# originally called prelim-tides - now subdaily_cl.py
# kristine larson, modified may 2021
import argparse
import numpy as np
import os
import sys
import subprocess


# my code
import gnssrefl.gps as g
import gnssrefl.subdaily as t

from gnssrefl.utils import str2bool


def parse_arguments():
    # must input start and end year
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", default=None, type=int, help="for now one year at a time")
    parser.add_argument("-txtfile", default=None, type=str, help="Filename for editing") 
    parser.add_argument("-splinefile", default=None, type=str, help="Input filename for rhdot/spline fitting (optional)") 
    parser.add_argument("-csvfile", default=None, type=str, help="set to True if you prefer csv to plain txt")
    parser.add_argument("-plt", default=None, type=str, help="set to False to suppress plots")
    parser.add_argument("-spline_outlier", default=None, type=float, help="outlier criterion used in splinefit (meters)")
    parser.add_argument("-knots", default=None, type=int, help="Knots per day, spline fit only (default is 8)")
    parser.add_argument("-sigma", default=None, type=float, help="simple sigma outlier criterion (e.g. 1 for 1sigma, 3 for 3sigma)")
    parser.add_argument("-extension", default=None, type=str, help="soln subdirectory")
    parser.add_argument("-rhdot", default=None, type=str, help="set to True to turn on spline fitting for RHdot correction")
    parser.add_argument("-doy1", default=None, type=int, help="initial day of year")
    parser.add_argument("-doy2", default=None, type=int, help="end day of year")
    parser.add_argument("-testing", default=None, type=str, help="set to True for testing mode")
    parser.add_argument("-ampl", default=None, type=float, help="new amplitude constraint")
    parser.add_argument("-azim1", default=None, type=int, help="new min azimuth")
    parser.add_argument("-azim2", default=None, type=int, help="new max azimuth")
    parser.add_argument("-h1", default=None, type=float, help="min RH (m)")
    parser.add_argument("-h2", default=None, type=float, help="max RH (m)")
    parser.add_argument("-peak2noise", default=None, type=float, help="new peak2noise constraint")

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['csvfile', 'plt', 'rhdot', 'testing']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def subdaily(station: str, year: int, txtfile: str = '', splinefile: str = None, csvfile: bool = False, plt: bool = True,
             spline_outlier: float = 1.0, knots: int = 8, sigma: float = 2.5, extension: str = '', rhdot: bool = False,
             doy1: int = 1, doy2: int = 366, testing: bool = False, ampl: float = 0, 
             h1: float=0.0, h2: float=300.0, azim1: int=0, azim2: int = 360, peak2noise: float = 0):
    """
        Parameters:
            ___________
            station : string
                4 or 9 character ID of the station.
            year : integer
                Year
            txtfile : string, optional
                File name.
                default is None - will set name for you.
            splinefile: string, optional
                Input filename for rhdot/spline fitting
                default is None
            csvfile: boolean, optional
                Set to True if you prefer csv to plain txt.
                default is False.
            plt : boolean, optional
                To print plots to screen or not.
                default is False.
            spline_outlier : float, optional
                Outlier criterion used in splinefit (meters)
                default is 1.0
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
                default is False.
            doy1 : integer, optional
                Initial day of year
                default is 1.
            doy2 : integer, optional
                End day of year.
                default is 366.
            testing : boolean, optional
                Set to True for testing mode.
                default is False.
            ampl : float, optional
                New amplitude constraint
                default is 0.
            azim1: int, optional
                New min azimuth
                default is 0.
            azim2: int, optional
                New max azimuth
                default is 360.
            h1: integer optional (should really be a float)
                lowest allowed reflector height
                default is 0
            h2: integer optional (should really be a float)
                highest allowed reflector height
                default is 300
            peak2noise: float, optional
                New peak to noise constraint
                default is 0.
    """

    # make surer environment variables are set
    g.check_environ_variables()
    xdir = os.environ['REFL_CODE']

    txtdir = xdir + '/Files'
    if not os.path.exists(txtdir):
        subprocess.call(['mkdir', txtdir])

#   these are optional output options
    #create the subdaily file
    writecsv = False
    if (h1 > h2):
        print('h1 must be less than h2. You submitted ', h1, ' and ', h2)
        sys.exit()
    if csvfile:
        writecsv = True
    if splinefile is None:
        if txtfile == '':
            print('Will pick up and concatenate daily result files')
        else:
            print('Using ', txtfile)
        # if txtfile provided, you can use that as your starting dataset 
        ntv, obstimes, fname, fname_new = t.readin_and_plot(station, year, doy1, doy2, plt, extension, sigma, writecsv,
                                                            azim1, azim2, ampl, peak2noise, txtfile,h1,h2)
        haveObstimes = True
    else:
        haveObstimes = False
        fname_new = splinefile
        if not os.path.isfile(fname_new):
            print('Input subdaily RH file you provided does not exist:', fname_new)
            sys.exit()

    # testing added so that if it crashes, only effects me.  and I get more useful error messages
    # added spline input 2021 oct 27. It was not coded well enough for gaps etc.
    # only allow plaint text?  i think that is what is really going on here
    input2spline = fname_new; output4spline = fname_new + '.withrhdot'

    if rhdot:
        if testing is None:
            try:
                if haveObstimes:
                    tv, corr = t.rhdot_correction(station, input2spline, output4spline, plt, spline_outlier,
                                                  obstimes=obstimes,knots=knots)
                else:
                    tv, corr = t.rhdot_correction(station, input2spline, output4spline, plt, spline_outlier,
                                                  knots=knots)
            except: 
                print('Exited the spline code for unknown reasons. Run with testing as True if you want more info')
        else:
            if haveObstimes:
                tv, corr = t.rhdot_correction(station, input2spline, output4spline, plt, spline_outlier,
                                              obstimes=obstimes, knots=knots)
            else:
                tv, corr = t.rhdot_correction(station, input2spline, output4spline, plt, spline_outlier, knots=knots)


def main():
    args = parse_arguments()
    subdaily(**args)


if __name__ == "__main__":
    main()
