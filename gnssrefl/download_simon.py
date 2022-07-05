# -*- coding: utf-8 -*-
"""
downloads Simon williams GNSS-IR sea level files
kristine larson

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

def quickp(station,t,sealevel):
    """
    station name
    t - time - in datetime format
    sealevel in meters (relative - not defined in a datum)
    
    """
    fs = 10
    if (len(t) > 0):
        fig,ax=plt.subplots()
        ax.plot(t, sealevel, '-')
        plt.title('Tides at ' + station)
        plt.xticks(rotation =45,fontsize=fs);
        plt.ylabel('meters')
        plt.grid()
        fig.autofmt_xdate()
        plt.show()
    else:
        print('no data found - so no plot')
    return

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
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
        Downloads IOC tide gauge files
        Downloads HTML (?????)  and converts it to plain txt with columns!

        Parameters:
        ___________
        station : string

        output : string, optional
            Optional output filename
            default is None

        plt: boolean, optional
            plot comes to the screen
            default is None

    """

    csv = False
    if output is None:
    # use the default
        outfile = station + '_' + 'simon.txt'
    else:
        outfile = output
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
        quickp('PMSL ' + station,obs,sl)


def main():
    args = parse_arguments()
    download_simon(**args)


if __name__ == "__main__":
    main()
