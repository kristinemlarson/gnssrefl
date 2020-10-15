# -*- coding: utf-8 -*-
"""
author: kristine m. larson
quickLook command line function 
# 
"""
import argparse
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import scipy.interpolate
import scipy.signal


# my codes
import gnssrefl.gps as g
import gnssrefl.read_snr_files as snr
import gnssrefl.quickLook_function as quick


def main():
# user inputs the observation file information
    parser = argparse.ArgumentParser()
# required arguments
    parser.add_argument("station", help="station", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("doy", help="day of year", type=int)
# these are the optional inputs
    parser.add_argument("-snr", default=66,help="snr ending - default is 66", type=int)
    parser.add_argument("-fr", default=None, type=int, help="try -fr 1 for GPS L1 only, or -fr 101 for Glonass L1")
    parser.add_argument("-ampl", default=None, type=float, help="minimum spectral amplitude allowed")
    parser.add_argument("-e1",  default=None, type=int, help="lower limit elevation angle (deg)")
    parser.add_argument("-e2",  default=None, type=int, help="upper limit elevation angle (deg)")
    parser.add_argument("-h1",  default=None, type=float, help="lower limit reflector height (m)")
    parser.add_argument("-h2",  default=None, type=float, help="upper limit reflector height (m)")
    parser.add_argument("-sat", default=None, type=int, help="satellite")
    parser.add_argument("-peak2noise",  default=None, type=float, help="Quality Control ratio")
    parser.add_argument("-fortran", default='True', type=str, help="Default is True: use Fortran translators")
    args = parser.parse_args()


#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

#
# rename the user inputs as variables
#
    station = args.station
    year = args.year
    doy= args.doy
    #snr_type = args.snrEnd - now optional

    if len(str(year)) != 4:
        print('Year must have four characters: ', year)
        sys.exit()

# default value is 66 for now
    snr_type = args.snr 

    exitS = g.check_inputs(station,year,doy,snr_type)

    if exitS:
        sys.exit()

    if args.fortran == 'True':
        fortran = True
    else:
        fortran = False


# set some reasonable default values for LSP (Reflector Height calculation). 
# most of these can be overriden at the command line
    freqs = [1] # default is to do L1 
    pele = [5, 30] # polynomial fit limits 
    minH = 0.5; maxH = 6 # RH limits in meters - this is typical for a snow setup
    e1 = 5; e2 = 25 # elevation angle limits for estimating LSP
# look at the four geographic quadrants to get started - these are azimuth angles
    azval = [0, 90, 90,180, 180, 270, 270, 360]
    reqAmp = [7] # this is arbitrary  - but often true for L1 obs 
    twoDays = False
# peak to noise value is one way of defining that significance (not the only way).
# For snow and ice, 3.5 or greater, tides can be tricky if the water is rough (and thus
# you might go below 3 a bit, say 2.5-2.7
    PkNoise = 3.0

# if user inputs these, then it overrides the default
    if (args.e1 != None):
        e1 = args.e1
    if (args.e2 != None):
         e2 = args.e2
    if e1 < 5:
        print('have to change the polynomial limits because you went below 5 degrees')
        print('this restriction is for quickLook only ')
        pele[0] = e1

    if (args.peak2noise != None):
        PkNoise = args.peak2noise

    if (args.h1 != None):
        minH  = args.h1
    if (args.h2 != None):
        maxH = args.h2
    if (args.sat != None):
        sat = args.sat
    else:
        sat = None


# this is for when you want to run the code with just a single frequency, i.e. input at the console
# rather than using the input restrictions
    if args.fr != None:
        freqs = [args.fr] 
    if args.ampl != None:
        reqAmp[0] = args.ampl


    f=freqs[0]
    NReg = [minH, maxH] # noise region - again, this is for typical snow setup


    quick.quickLook_function(station, year, doy, snr_type,f,e1,e2,minH,maxH,reqAmp,pele,sat,PkNoise,fortran)


if __name__ == "__main__":
    main()
