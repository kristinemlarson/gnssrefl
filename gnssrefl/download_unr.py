# -*- coding: utf-8 -*-
"""
downloads nevada reno blewitt files
kristine larson
"""
import argparse
import wget
import sys
import os


def main():
    """
    command line interface for download_blewitt
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)

    args = parser.parse_args()

#   make sure environment variables exist.  set to current directory if not

    station = args.station
    if len(station) != 4:
        print('illegal name-must be 4 characters')
        sys.exit()
    station = station.upper()
#    http://geodesy.unr.edu/gps_timeseries/tenv3/IGS14/P101.tenv3
    url= 'http://geodesy.unr.edu/gps_timeseries/tenv3/IGS14/'
         # http://geodesy.unr.edu/gps_timeseries/tenv3/IGS14/P101.tenv3
    fname = station + '.tenv3'
    url = url + fname
    print(url)
    try:
        wget.download(url, out=fname)
    except:
        print('\n download failed:', fname)

    if os.path.exists(fname):
        print('\n SUCCESS:', fname)
    else:


if __name__ == "__main__":
    main()
