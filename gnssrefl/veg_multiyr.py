# -*- coding: utf-8 -*-
"""
kristine larson
combine multiple years of teqc multipath metrics, 
write a file, and make a plot
"""
import argparse
import matplotlib.pyplot as plt
import numpy as np
import os
import subprocess
import sys
import time
import wget

import gnssrefl.gps as g
import gnssrefl.computemp1mp2 as veg

def vegoutfile(station):
    """
    make sure directories exist for prelim veg output file
    returns name of the otuput file
    """
    vegdir = os.environ['REFL_CODE'] + '/Files'
    if not os.path.isdir(vegdir):
        subprocess.call(['mkdir',vegdir])
    vegdir = vegdir + '/veg'
    if not os.path.isdir(vegdir):
        subprocess.call(['mkdir',vegdir])
    vegout =  vegdir + '/' + station + '_veg.txt'
    print('File will be written to: ', vegout)

    return vegout 


def main():
    """
    command line interface for download_rinex
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year1", help="beginning year", type=int)
    parser.add_argument("year2", help="end year", type=int)
    parser.add_argument("-rcvtype", default = None, help="Receiver type", type=str)
    parser.add_argument("-winter", default = None, help="Removes winter points", type=str)



    args = parser.parse_args()

#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

#   assign to normal variables
    station = args.station
    if len(station) != 4:
        print('illegal station - must be 4 char')
        sys.exit()

    vegout = vegoutfile(station)

    y1 = args.year1
    y2 = args.year2 + 1

    if args.rcvtype == None:
        # do not restrict as the default
        rcvtype = 'NONE'
    else:
        rcvtype = args.rcvtype

    # should add a header
    vegid = open(vegout,'w+')

    k = 0
    for y in range(y1,y2):
        for d in range(1,367):
            sfile = veg.sfilename(station, y, d)
            if os.path.isfile(sfile):
                mp1, mp2,requested_rcv=veg.readoutmp(sfile,rcvtype)
                if requested_rcv:
                    k+=1
                    vegid.write("{0:4.0f} {1:3.0f} {2:s} {3:s} \n".format(y,d,mp1[0:6],mp2[0:6]))
    vegid.close()
    print(k)
    tv = np.loadtxt(vegout)
    if len(tv) > 0:
        veg.vegplt(station, tv,args.winter)

if __name__ == "__main__":
    main()
