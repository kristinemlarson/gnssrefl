# preliminary water analysis to apply RHdot correction
import argparse
import datetime
import json
import matplotlib.pyplot as Plt
import numpy as np
import os
import sys

from datetime import date

# my code
import gnssrefl.gps as g
import gnssrefl.tide_library as t


import scipy.interpolate as interpolate
from scipy.interpolate import interp1d
import math


def main():
#   make surer environment variables are set 
    g.check_environ_variables()
    xdir = os.environ['REFL_CODE'] 

# must input start and end year
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", default=None, type=str, help="for now one year at a time")
    parser.add_argument("-txtfile", default=None, type=str, help="Filename/will create if not provided") 
    parser.add_argument("-plt", default=None, type=str, help="set to False to suppress plots")
    parser.add_argument("-outlier", default=None, type=str, help="outlier criterion input (meters)")
    parser.add_argument("-extension", default=None, type=str, help="soln subdirectory")
    parser.add_argument("-doy1", default=None, type=str, help="initial day of year")
    parser.add_argument("-doy2", default=None, type=str, help="end day of year")

    args = parser.parse_args()
#   these are required
    station = args.station
    year = int(args.year)

    # default is plots comes to the screen
    plt = True
    if args.plt == 'False':
        plt= False

    txtdir = xdir + '/Files'
    if not os.path.exists(txtdir):
        subprocess.call(['mkdir',txdir])
 
    if args.extension == None:
        ext = ''
    else:
        ext = args.extension

#   these are optional output options
    if args.txtfile == None:
        #create the subdaily file
    # read in the data and make a plot
        if args.doy1 == None:
            doy1 = 1
        else:
            doy1 = int(args.doy1)

        if args.doy2 == None:
            doy2 = 366
        else:
            doy2 = int(args.doy2)

        ntv = t.readin_and_plot(station, year,doy1,doy2,plt,ext)
        N,M = np.shape(ntv)
     # use function instead of writing it here
        writecsv = False;   writetxt = True
        fname = xdir + '/Files/' + station + '_subdaily_rh.txt'
        t.write_subdaily(fname,station,ntv,writecsv,writetxt)
    else:
        fname = args.txtfile
        if not os.path.isfile(fname):
            print('Input subdaily RH file does not exist:', fname)
            sys.exit()

    # I think these are used just for velocity ...
    perday = 24*20 # every 3 minutes

    if args.outlier == None:
        outlier = 0.45
    else:
        outlier = float(args.outlier)

    tv,corr = t.splines_for_dummies2(fname, perday,plt,outlier)

if __name__ == "__main__":
    main()
