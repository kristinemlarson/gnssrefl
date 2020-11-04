# -*- coding: utf-8 -*-
"""
converts XYZ to latlonht
kristine larson
"""
import argparse
import sys

import gnssrefl.gps as g

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("lat", help="latitude (deg) ", type=float)
    parser.add_argument("lon", help="longitude (deg) ", type=float)
    parser.add_argument("height", help="ellipsoidal height (m) ", type=float)
    args = parser.parse_args()

    lat=args.lat; lon=args.lon; height=args.height
    x,y,z = g.llh2xyz(lat,lon,height)
    print("XYZ %15.4f %15.4f %15.4f " % ( x,y,z) )

if __name__ == "__main__":
    main()
