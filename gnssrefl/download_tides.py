# -*- coding: utf-8 -*-
import argparse
import datetime
import wget
import os
import requests
import subprocess
import sys
import gnssrefl.gps as g

from gnssrefl.utils import validate_input_datatypes, str2bool

import gnssrefl.download_noaa as download_noaa
import gnssrefl.download_ioc as download_ioc
import gnssrefl.download_wsv as download_wsv
import gnssrefl.download_psmsl as download_psmsl

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name, e.g. 8768094", type=str)
    parser.add_argument("network", help="tidegauge network (noaa,ioc,psmsl,wsv)", type=str)
    parser.add_argument("-date1", help="start-date, 20150101", type=str, default=None)
    parser.add_argument("-date2", help="end-date, 20150110", type=str, default=None)
    parser.add_argument("-output", default=None, help="Optional output filename", type=str)
    parser.add_argument("-plt", default=None, help="quick plot to screen", type=str)
    parser.add_argument("-datum", default=None, help="datum for NOAA", type=str)
    parser.add_argument("-sensor", default=None, help="sensor type for IOC", type=str)
    parser.add_argument("-subdir", default=None, help="optional subdirectory name for output", type=str)
    parser.add_argument("-year", default=None, help="year for archive QLD data", type=str)
    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['plt']
    args = str2bool(args, boolean_args)


    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}

def download_tides(station: str, network : str, date1: str = None, date2: str = None, output: str = None, plt: bool = False, datum: str = 'mllw', subdir: str = None, year: int=None):
    """
    Downloads tide gauge data from four different networks (see below)

    Output is written to REFL_CODE/Files/ unless subdir optional input is set. Plot is sent to the screen if requested.

    Examples
    --------

    download_tides 8768094 noaa 20210101 20210131
        NOAA station 876094

    download_tides thul ioc 20210101 20210131
        IOC station thul

    download_tides 5970026 wsv 
        WSV station 5970026

    download_tides 10313 psmsl
        PSMSL station 10313 (downloads one file)

    Parameters 
    ----------
    station : str
        station name
    network : str
        name of tide network. Options:

            noaa : US NOAA

            ioc : UNESCO

            wsv : Germany, Wasserstrassen-und Schifffahrtsverwaltung

            psmsl : Permanent Service Mean Sea Level

    date1 : str, optional
        start date, 20150101, needed for NOAA/IOC
    date2 : str,optional
        end date, 20150110, needed for NOAA/IOC
    output : str, optional
        Optional output filename
    plt : bool, optional
        plot comes to the screen
    datum: str, optional
        NOAA input, default is mllw
    sensor: str, optional
        setting for IOC
    subdir : str, optional
        subdirectory for output in the $REFL_CODE/Files area

    """
    g.check_environ_variables()

    xdir = os.environ['REFL_CODE']
    outdir = xdir  + '/Files/'
    if not os.path.exists(outdir) :
        subprocess.call(['mkdir', outdir])
    if (network == 'noaa') or (network == 'ioc'):
        if (date1 is None):
            print('You need to enter a starting date YYYYMMDD') ; sys.exit()
        if (date2 is None):
            print('You need to enter a ending date YYYYMMDD'); sys.exit()
        if len(date1) != 8:
            print('date1 must have 8 characters', date1); sys.exit()
        if len(date2) != 8:
            print('date2 must have 8 characters', date2); sys.exit()

    print(station, network, date1,date2,output,plt)
    if network == 'noaa':
        datum = 'mllw'; subdir = None
        download_noaa.download_noaa(station, date1, date2, output, plt, datum, subdir)
    elif network == 'ioc':
        outliers = False; sensor = None
        download_ioc.download_ioc(station, date1, date2, output, plt, outliers, sensor, subdir)
    elif network == 'wsv':
        download_wsv.download_wsv(station, plt, output)
    elif network == 'psmsl':
        download_psmsl.download_psmsl(station, output,plt )
    elif network == 'qld':
        download_noaa.download_qld(station,year,plt)
    else:
        print('I do not recognize your tide gauge network')


def main():
    args = parse_arguments()
    download_tides(**args)


if __name__ == "__main__":
    main()

