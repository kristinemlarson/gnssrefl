# -*- coding: utf-8 -*-
"""
extracts coordinates for stations that were in the UNR
database (when I downloaded it ;-)
input four character station name, lowercase

2021 November 2
modified to use UNR database. Downloads it if you don't have it.

"""
import argparse
import wget
import sys
import os
import gnssrefl.gps as g


def main():
    """
    command line interface for query_unr
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name - 4 char - lowercase ", type=str)

    args = parser.parse_args()

    station = args.station
    if len(station) != 4:
        print('illegal station name-must be 4 characters')
        sys.exit()
    alat,alon,ht=g.queryUNR_modern(station)
    if (alat+alon+ht) != 0:
        x,y,z=g.llh2xyz(alat,alon,ht)
        print('XYZ', round(x,4),round(y,4),round(z,4) )

if __name__ == "__main__":
    main()