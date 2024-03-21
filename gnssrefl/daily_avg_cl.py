import argparse
import matplotlib.pyplot as matplt
import os
import sys

import gnssrefl.daily_avg as da
import gnssrefl.gps as g
import gnssrefl.gnssir_v2 as guts2

from gnssrefl.utils import str2bool

def parse_arguments():
    # must input start and end year
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name (4 ch only)", type=str)
    parser.add_argument("medfilter", help="Median filter for daily RH (m). Start with 0.25 ", type=float)
    parser.add_argument("ReqTracks", help="required number of tracks", type=int)
    parser.add_argument("-txtfile", default=None, type=str, help="Set your own output filename")
    parser.add_argument("-plt", default=None, type=str, help="plt to screen: True or False")
    parser.add_argument("-extension", default=None, type=str, help="extension for solution names")
    parser.add_argument("-year1", default=None, type=int, help="restrict to years starting with")
    parser.add_argument("-year2", default=None, type=int, help="restrict to years ending with")
    parser.add_argument("-fr", default=0, type=int, help="frequency, default is to use all")
    parser.add_argument("-csv", default=None, type=str, help="True if you want csv instead of plain text")
    parser.add_argument("-azim1", default=None, type=int, help="minimum azimuth (deg)")
    parser.add_argument("-azim2", default=None, type=int, help="maximum azimuth (deg)")
    parser.add_argument("-test", default=None, type=str, help="augmentation to plot")
    parser.add_argument("-subdir", default=None, type=str, help="non-default subdirectory for output ")
    parser.add_argument("-plot_limits", default=None, type=str, help="add median value and limits to plot, default is False ")
    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['plt', 'csv','test','plot_limits']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def daily_avg(station: str , medfilter: float, ReqTracks: int, txtfile: str = None, plt: bool = True, 
        extension: str = '', year1: int = 2005, year2: int = 2030, fr: int = 0, csv: bool = False, 
        azim1: int = 0, azim2: int = 360, test: bool = False, subdir: str=None,plot_limits: bool=False):
    """
    The goal of this code is to consolidate individual RH results into a single file consisting of 
    daily averaged RH without outliers. These daily average values are nominally associated 
    with the time of 12 hours UTC.


    There are two required parameters - medfilter and ReqTracks. These are quality control parameters.
    They are applied in two steps. The code first calculates the median value each day - and keeps
    only the RH that are within medfilter (meters) of this median value. If there are at least "ReqTracks"
    number of RH left after that step, a daily average is computed for that day.


    As of version 3.1.3 users may store the required input parameters to daily_avg 
    in the json used by gnssir. The names of these parameters are:
    daily_avg_reqtracks and  daily_avg_medfilter.  For those making a new json, 
    the parameters will be set to None if you don't choose a value on the command line. 
    You can also hand edit or add it. This would be helpful in not having to rerun gnssir_input and 
    risk losing some of your other specialized selections.

    If you are unfamiliar with what a median filter does in this code, please see 
    https://gnssrefl.readthedocs.io/en/latest/pages/README_dailyavg.html

    The outputs are stored in $REFL_CODE/Files/station by default.  If you want to specify a new
    subdirectory, I believe that is an allowed option.  You can also specify specific years to analyze 
    and apply fairly simple azimuth constraints.
    
    In summary, three text files are created

    1. individual RH values with no QC applied
    
    2. individual RH values with QC applied

    3. daily average RH 

    Examples
    -------- 
    daily_avg p041 0.25 10 
        consolidates results for p041 with median filter of 0.25 meters and at least 10 solutions per day
    daily_avg p041 0.25 10 -plot_limits T
        the same as above but with plot_limits to help you see where the median filter is applied
    daily_avg p041 0.25 10  -year1 2015 -year2 2020
        consolidates results for p041 with median filter of 0.25 meters and at least 10 solutions per day
        and restricts it to years between 2015 and 2020
    daily_avg p041 0.25 10  -year1 2015 -year2 2020 -azim1 0 -azim2 180
        consolidates results for p041 with median filter of 0.25 meters and at least 10 solutions per day
        and restricts it to years between 2015 and 2020 and azimuths between 0 and 180 degrees
    daily_avg p041 0.25 10 -extension NV
        consolidates results which were created using the extension NV when you ran gnssir.


    Parameters
    ----------
    station : str
        4 ch station name, generally lowercase

    medfilter : float
        Median filter for daily reflector height (m). Start with 0.25 for surfaces where you expect no significant 
        subdaily change (snow/lakes).

    ReqTracks : int
        Required number of daily satellite tracks to save the daily average value.

    txtfile : str, optional
        Use this parameter to set your own output filename.
        default is to let the code choose.

    plt : bool, optional
        whether to print plots to screen or not.
        default is True.

    extension : str, optional
        extension for solution names.
        default is ''. (empty string)

    year1 : int, optional
        restrict to years starting with.
        default is 2005.

    year2 : int, optional
        restrict to years ending with.
        default is 2030.

    fr : int, optional
        GNSS frequency. If none input, all are used. Value options:

            1 : GPS L1

            2 : GPS L2

            20 : GPS L2C

            5 : GPS L5

            101 : GLONASS L1

            102 : GLONASS L2

            201 : GALILEO E1

            205 : GALILEO E5a

            206 : GALILEO E6

            207 : GALILEO E5b

            208 : GALILEO E5

            302 : BEIDOU B1

            306 : BEIDOU B3

            307 : BEIDOU B2

    csv : boolean, optional
        Whether you want csv instead of a plain text file.
        default is False.

    azim1 : int, optional
        minimum azimuth, degrees
        note: should be modified to allow negative azimuth

    azim2 : int, optional
        maximum azimuth, degrees

    test : bool, optional
        not sure what this does

    subdir: str, optional
        non-default subdirectory for Files output

    plot_limits: bool, optional
        adds the median value and median filter limits to the plot.
        default is False

    """
    if len(station) != 4:
        print('Station names must have four characters. Exiting.')
        sys.exit()

    plt2screen = plt # since variable was originally this name 
    # make sure environment variables are set
    g.check_environ_variables()
    if subdir is None:
        subdir = station
    g.set_subdir(subdir)

# where the summary files will be written to
    xdir = os.environ['REFL_CODE']
    txtdir = xdir + '/Files/'  + subdir

    # read in potential medfilter and reqtracks values
    # set noexit to True because I want to look for the json but 
    # don't want to require it
    lsp = guts2.read_json_file(station, extension,noexit=True)
    # if valeus not found, then set them to None
    if 'daily_avg_medfilter' not in lsp:
        lsp['daily_avg_medfilter'] = None
    if 'daily_avg_reqtracks' not in lsp:
        lsp['daily_avg_reqtracks'] = None

    # if these required values are zero, then the code 
    # looks to see if you set them in the json
    if ReqTracks == 0:
        if  lsp['daily_avg_reqtracks'] is not None:
            print('Using ReqTracks value from json')
            ReqTracks = lsp['daily_avg_reqtracks']
        else:
            print('Zero is an invalid value for ReqTracks. Change value on command line')
            print('or in gnssir_input created json. Exiting.')
            sys.exit()
    if medfilter == 0:
        if  lsp['daily_avg_medfilter'] is not None:
            print('Using medfilter value from json')
            medfilter = lsp['daily_avg_medfilter']
        else:
            print('Zero is an invalid value for medfilter parameter. Change value on command ')
            print('line or in gnssir_input created json. Exiting.')
            sys.exit()

    # set the name of the output format
    if csv:
        alldatafile = txtdir + '/' + station + '_allRH.csv' 
    else:
        alldatafile = txtdir + '/' + station + '_allRH.txt' 

    # read in the files
    tv, obstimes = da.readin_plot_daily(station, extension, year1, year2, fr, 
            alldatafile, csv, medfilter, ReqTracks,azim1,azim2,test,subdir,plot_limits)

    # default is to show the plots
    nr,nc = tv.shape
    if plt2screen & (nr > 0):
        matplt.show()

    # now write out the result file:

    if txtfile is None:
        if csv:
            outfile = txtdir + '/' + station + '_dailyRH.csv' 
        else:
        # use default  filename for the average
            outfile = txtdir + '/' + station + '_dailyRH.txt' 
    else:
        # use filename provided by the user
        outfile = txtdir + '/' + txtfile

    if (nr > 0):
        da.write_out_RH_file(obstimes, tv, outfile, csv,station,extension)


def main():
    args = parse_arguments()
    daily_avg(**args)


if __name__ == "__main__":
    main()
