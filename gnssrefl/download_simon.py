# -*- coding: utf-8 -*-
"""
downloads Simon Williams PSMSL GNSS-IR sea level files

"""
import argparse
import datetime
import numpy as np
import os
import requests
import sys
import gnssrefl.gps as g
import matplotlib.pyplot as plt
import subprocess
import urllib

from gnssrefl.utils import validate_input_datatypes, str2bool


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name, e.g. 10313", type=str)
    parser.add_argument("-output", default=None, help="Optional output filename", type=str)
    parser.add_argument("-plt", default=None, help="Optional plot to screen variable, boolean", type=str)
    args = parser.parse_args().__dict__


    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['plt']
    args = str2bool(args, boolean_args)


    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def download_simon(station: str, output: str = None, plt: bool = False):
    """
    Downloads PSMSL tide gauge files created by Simon Williams 
    in json format, converts it to plain txt or csv format

    Parameters
    ----------

    station : str
        4 ch station name

    output : str, optional
        Optional output filename
        default is None

    plt: bool, optional
        plot comes to the screen
        default is None

    """
    g.check_environ_variables()
    xdir = os.environ['REFL_CODE']
    outdir = xdir  + '/Files/'
    if not os.path.exists(outdir) :
        subprocess.call(['mkdir', outdir])


    csv = False
    if output is None:
    # use the default
        outfile = outdir + station + '_' + 'simon.txt'
    else:
        outfile = outdir + output
        if output[-3:] == 'csv':
            csv = True

    filename = station + '.zip'
    cfilename = station + '.csv'
    url = 'https://psmsl.org/data/gnssir/data/main/' + filename
    print(url)

    # remove old files 
    if os.path.exists(filename):
        subprocess.call(['rm', '-f',filename])
    if os.path.exists(cfilename):
        subprocess.call(['rm', '-f',cfilename])

    print('Pick up the files')

    try:
        urllib.request.urlretrieve(url, filename)
        subprocess.call(['unzip', filename])
        subprocess.call(['rm', '-f', filename])
        # this should produce a csv file - cfilename
    except:
        print('Some problem with the download. Perhaps the station does not exist')
        sys.exit()

    if os.path.exists(cfilename):
       # read the file
        obs, simon_mjdish, sl,sprn,sfr, simon_az = g.read_simon_williams(cfilename,outfile)
    else:
        print('some problem with the download')
        sys.exit()
    

    NV = len(obs)

    if NV < 1:
        print('No data found')
        sys.exit()

    if plt:
        g.quickp('PSMSL ' + station,obs,sl)

def main():
    args = parse_arguments()
    download_simon(**args)


if __name__ == "__main__":
    main()
