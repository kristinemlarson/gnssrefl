# -*- coding: utf-8 -*-
import argparse
import wget
import sys
import os
import gnssrefl.gps as g


def main():
    """
    Extracts coordinates for stations that were in the UNR database 
    in late 2021. Prints both geodetic and cartesian values, and height
    above sea level.


    Parameters
    ----------
    station : str
        four character station name

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="4-ch station name (lowercase)", type=str)

    args = parser.parse_args()

    station = args.station
    if len(station) != 4:
        print('illegal station name-must be 4 characters')
        sys.exit()
    alat,alon,ht=g.queryUNR_modern(station.lower())
    coords_found = True
    if (alat+alon+ht) == 0:
        coords_found = False

    if coords_found:
        x,y,z=g.llh2xyz(alat,alon,ht)
        print('XYZ (m):', round(x,4),round(y,4),round(z,4) )
        print('LLH (deg,deg,m):', round(alat,6),round(alon,6),round(ht,3) )

    # attempt to find height above sea level
    foundfile = g.checkEGM()
    if (foundfile) and (coords_found):
        geoidC = g.geoidCorrection(alat,alon)
        sealevel = ht - geoidC
        print('Sea Level (m): ', round(sealevel,3))


if __name__ == "__main__":
    main()
