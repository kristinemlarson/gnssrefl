# -*- coding: utf-8 -*-
"""
extracts coordinates for stations that were in the UNR
database (when I downloaded it ;-)
author: kristine larson
input four character station name, lowercase

2021 November 2
modified to use UNR database. Downloads it if you don't have it.
Hopefully

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
    a,b,c=g.queryUNR_modern(station)
    #a,b,c=g.queryUNR(station)

if __name__ == "__main__":
    main()
