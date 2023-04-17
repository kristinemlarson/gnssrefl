# -*- coding: utf-8 -*-
import argparse
import sys

import gnssrefl.gps as g

def main():
    """
    Converts Cartesian coordinates to latitude, longitude, ellipsoidal height.
    Prints to screen

    Example
    -------
    xyz2llh -1283634.1615 -4726427.8931 4074798.0429
        returns 39.949492042 -105.194266387  1728.856

    Parameters
    ----------
    x : float
        X coordinate (m)
    y : float
        Y coordinate (m)
    z : float
        Z coordinate (m)

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("x", help="X coordinate (m) ", type=float)
    parser.add_argument("y", help="Y coordinate (m) ", type=float)
    parser.add_argument("z", help="Z coordinate (m) ", type=float)

    args = parser.parse_args()

    x=args.x; y=args.y; z=args.z
    xyz = [x, y, z]
    lat,lon,h = g.xyz2llhd(xyz)
    print("Lat Lon Ht (deg deg m) %14.9f %14.9f %9.3f " % (lat, lon, h) )

if __name__ == "__main__":
    main()
