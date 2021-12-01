# -*- coding: utf-8 -*-
"""
extracts coordinates for stations that were in the UNR
database (when I downloaded it ;-)
author: kristine larson
input four character station name, lowercase

2021 November 2
modified to use UNR database. Downloads it if you don't have it.
Hopefully
2021 November 26
prints out XYZ too cause why not!

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
    x,y,z=g.llh2xyz(alat,alon,ht)
    print('XYZ', round(x,4),round(y,4),round(z,4) )
    #a,b,c=g.queryUNR(station)

if __name__ == "__main__":
    main()
