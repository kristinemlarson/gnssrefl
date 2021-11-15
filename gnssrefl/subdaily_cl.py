# preliminary water analysis to apply RHdot correction
# originally called prelim-tides - now subdaily_cl.py
# kristine larson, modified may 2021
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
import gnssrefl.subdaily as t


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
    parser.add_argument("-txtfile", default=None, type=str, help="Filename for editing") 
    parser.add_argument("-splinefile", default=None, type=str, help="Input filename for spline fitting (optional)") 
    parser.add_argument("-csvfile", default=None, type=str, help="set to True if you prefer csv to plain txt") 
    parser.add_argument("-plt", default=None, type=str, help="set to False to suppress plots")
    parser.add_argument("-outlier", default=None, type=str, help="outlier criterion used in splinefit (meters)")
    parser.add_argument("-sigma", default=None, type=str, help="simple sigma outlier criterion (e.g. 1 for 1sigma, 3 for 3sigma)")
    parser.add_argument("-extension", default=None, type=str, help="soln subdirectory")
    parser.add_argument("-spline", default=None, type=str, help="set to True to turn on spline fitting for RHdot correction")
    parser.add_argument("-doy1", default=None, type=str, help="initial day of year")
    parser.add_argument("-doy2", default=None, type=str, help="end day of year")
    parser.add_argument("-testing", default=None, type=str, help="set to True for testing mode")
    parser.add_argument("-ampl", default=None, type=str, help="new amplitude constraint")
    parser.add_argument("-azim1", default=None, type=str, help="new min azimuth")
    parser.add_argument("-azim2", default=None, type=str, help="new max azimuth")
    parser.add_argument("-peak2noise", default=None, type=str, help="new peak2noise constraint")

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
        subprocess.call(['mkdir',txtdir])
 
    if args.extension == None:
        ext = ''
    else:
        ext = args.extension

    # if not specified, use 2.5 sigma
    if args.sigma == None:
        sigma = 2.5 
    else:
        sigma = float(args.sigma)

    # if not specified, use outlier criterion of 0.5 m
    # i believe this is only used for spline
    if args.outlier == None:
        outlier = 0.5 
    else:
        outlier = float(args.outlier)

# these constraints are added at the command line
    azim1 = 0
    if not (args.azim1 == None):
        azim1 = int(args.azim1)

    azim2 = 360 
    if not (args.azim2 == None):
        azim2 = int(args.azim2)

    ampl = 0 
    if not (args.ampl == None):
        ampl = float(args.ampl)

    peak2noise = 0
    if not (args.peak2noise == None):
        peak2noise = float(args.peak2noise)

    usespline = False # though it is dangerous
    if args.spline == 'True':
        usespline = True

#   these are optional output options
    #create the subdaily file
    if args.doy1 == None:
        doy1 = 1
    else:
        doy1 = int(args.doy1)
    if args.doy2 == None:
        doy2 = 366
    else:
        doy2 = int(args.doy2)
        # writejson not allowed as of yet.
    writecsv = False
    if (args.csvfile == 'True'):
        writecsv = True
    if (args.splinefile == None):
        txtfile = ''
        if (args.txtfile == None):
            print('Will pick up and concatenate daily result files')
        else:
            txtfile = args.txtfile 
            print('Using ',txtfile)
        # if txtfile provided, you can use that as your starting dataset 
        ntv,obstimes,fname,fname_new = t.readin_and_plot(station, year,doy1,doy2,plt,ext,sigma,writecsv,azim1,azim2,ampl,peak2noise,txtfile)
        haveObstimes = True
        N,M = np.shape(ntv)
    else:
        haveObstimes = False
        fname_new = args.splinefile
        if not os.path.isfile(fname_new):
            print('Input subdaily RH file you provided does not exist:', fname_new)
            sys.exit()

    # I think these are used just for velocity ...
    perday = 24*20 # yikes - every 3 minutes

    # testing added so that if it crashes, only effects me.  and I get more useful error messages
    # added spline input 2021 oct 27. It was not coded well enough for gaps etc.
    input2spline = fname_new; output4spline = fname_new + '.rev'
    if usespline:
        if (args.testing == None): 
            try:
                if haveObstimes:
                    tv,corr = t.splines_for_dummies2(station,input2spline, output4spline, perday,plt,outlier,obstimes=obstimes)
                else:
                    tv,corr = t.splines_for_dummies2(station,input2spline, output4spline, perday,plt,outlier)
            except: 
                okok = 1
        else:
            print('for me only')
            if haveObstimes:
                tv,corr = t.splines_for_dummies2(station,input2spline, output4spline, perday,plt,outlier,obstimes=obstimes)
            else:
                tv,corr = t.splines_for_dummies2(station,input2spline, output4spline, perday,plt,outlier)


if __name__ == "__main__":
    main()
