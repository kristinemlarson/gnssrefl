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
    parser.add_argument("-csvfile", default=None, type=str, help="set to True if you prefer csv to plain txt")
    parser.add_argument("-plt", default=None, type=str, help="set to False to suppress plots")
    parser.add_argument("-extension", default=None, type=str, help="solution subdirectory")
    parser.add_argument("-doy1", default=None, type=int, help="initial day of year")
    parser.add_argument("-doy2", default=None, type=int, help="end day of year")
    parser.add_argument("-ampl", default=None, type=float, help="new amplitude constraint")
    parser.add_argument("-azim1", default=None, type=int, help="new min azimuth")
    parser.add_argument("-azim2", default=None, type=int, help="new max azimuth")
    parser.add_argument("-h1", default=None, type=float, help="min RH (m)")
    parser.add_argument("-h2", default=None, type=float, help="max RH (m)")
    parser.add_argument("-peak2noise", default=None, type=float, help="new peak2noise constraint")

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['csvfile', 'plt' ]
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def rh_plot(station: str, year: int, csvfile: bool = False, plt: bool = True,
             extension: str = '', doy1: int = 1, doy2: int = 366, ampl: float = 0, 
             h1: float=0.0, h2: float=300.0, azim1: int=0, azim2: int = 360, 
             peak2noise: float = 0 ) :
    """
    Parameters
    ----------

    station : string
        4 character id of the station.
    year : integer
        Year
    csvfile: boolean, optional
        Set to True if you prefer csv to plain txt.
        default is False.
    plt : boolean, optional
        To print plots to screen or not.
        default is TRUE.
    extension : string, optional
        Solution subdirectory.
        default is empty string.
    doy1 : integer, optional
        Initial day of year
        default is 1.
    doy2 : integer, optional
        End day of year.
        default is 366.
    ampl: float 
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

    """

    if len(station) != 4:
        print('station names must be four characters long')
        sys.exit()

    # make surer environment variables are set
    g.check_environ_variables()
    xdir = os.environ['REFL_CODE']

    # set subdirectory for results
    subdir = station
    g.set_subdir(subdir)

    txtdir = xdir + '/Files/' + subdir
    print(txtdir)

    #does not currently allow this - but should
    writecsv = False

    if (h1 > h2):
        print('h1 must be less than h2. You submitted ', h1, ' and ', h2)
        sys.exit()

    # these are things not needed by rh_plot - but the code expects it
    sigma = 3; txtfile = ''; kplt=False
    default_usage = False
    hires_figs = True ; fs = 12
    ntv, obstimes, fname, fname_new = t.readin_and_plot(station, year, doy1, doy2, plt, extension, sigma,
            writecsv, azim1, azim2, ampl, peak2noise, txtfile,h1,h2,kplt,txtdir,default_usage, hires_figs,fs)

def main():
    args = parse_arguments()
    rh_plot(**args)


if __name__ == "__main__":
    main()
