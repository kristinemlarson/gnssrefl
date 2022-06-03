# -*- coding: utf-8 -*-
"""
kristine larson
download a year of teqc logs from unavco
can do multiple years as well
"""
import argparse
import os
import subprocess
import sys

import wget

import gnssrefl.gps as g
import gnssrefl.computemp1mp2 as veg


def mpfile_unavco(station, year, doy):
    """
    picks up teqc log from unavco if it exists
    """
    cdoy = '{:03d}'.format(doy)
    cyyyy = str(year)
    cyy = cyyyy[2:4]

    # info for unavco
    fdir = 'ftp://data-out.unavco.org/pub/rinex/qc/'
    fdir = fdir + cyyyy + '/' + cdoy + '/'
    fname = station + cdoy + '0.' + cyy + 'S'
    url = fdir + fname

    # local directory info
    ddir = os.environ['REFL_CODE'] + '/' + cyyyy + '/mp/' + station + '/'
    if os.path.isfile(ddir + fname):
        print('file already exists', ddir+fname)
    else:
        try:
            wget.download(url,out=fname)
        except:
            print('download failed for ', fname)
        if os.path.isfile(fname):
           subprocess.call(['mv', fname, ddir])
           print('\n SUCCESS', ddir + '/' + fname)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("-year_end", default=None, help="end year", type=int)

    args = parser.parse_args().__dict__

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def download_teqc(station: str, year: int, year_end: int = None):
    """
        Download teqc logs from UNAVCO per year.
        Parameters:
        ___________
        station : string
                4 character ID of the station

        year : integer
            Year

        year_end : int, optional
            end year. This is to create a range from year to year_end to get the snr files for more than one year.
            Default is None.
    """

#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

    if len(station) != 4:
        print('illegal station - must be 4 char')
        sys.exit()

    y1 = year; 
    if year_end is None:
        y2 = year + 1
    else:
        y2 = year_end + 1
    for y in range(y1, y2):
        veg.check_directories(station, y)
        # life is short - assume it is always a leap year
        for d in range(1, 367):
            mpfile_unavco(station, y, d)


def main():
    args = parse_arguments()
    download_teqc(**args)


if __name__ == "__main__":
    main()
