# -*- coding: utf-8 -*-
# kristine M. larson


import argparse
import datetime
import json
import numpy as np
import matplotlib.pyplot as plt
import os
import scipy.interpolate
import scipy.signal
import subprocess
import sys
import warnings

import gnssrefl.gnssir as guts
import gnssrefl.gps as g



def main():
# pick up the environment variable for where you are keeping your LSP data
    print('=================================================================================')
    print('===========================RUNNING GNSS IR ======================================')
    print('=================================================================================')
 
#
# user inputs the observation file information
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("doy", help="doy", type=int)

# optional inputs
    parser.add_argument("-snr", default=66,help="snr file ending, default is 66", type=int)
    parser.add_argument("-plt",  default=None, help="plt to screen (True or False)", type=str)
    parser.add_argument("-fr", default=None, type=int, help="try -fr 1 for GPS L1 only, or -fr 101 for Glonass L1")
    parser.add_argument("-ampl",  default=None, type=float, help="try -ampl 5-6 for minimum spectral amplitude")
    parser.add_argument("-sat", default=None, type=int, help="allow individual satellite")
    parser.add_argument("-doy_end",  default=None, type=int, help="doy end")
    parser.add_argument("-year_end", default=None, type=int, help="year end")
    parser.add_argument("-azim1", default=None, type=int, help="lower limit azimuth")
    parser.add_argument("-azim2", default=None, type=int, help="upper limit azimuth")
    parser.add_argument("-nooverwrite",  default=None, type=int, help="use any integer to not overwrite")
    parser.add_argument("-extension", default=None, type=str, help="extension for result file, useful for testing strategies")
    parser.add_argument("-compress",  default=None, type=str, help="xz compress SNR files after use")
    parser.add_argument("-screenstats",  default=None, type=str, help="some stats printed to screen(default is True)")
    parser.add_argument("-delTmax", default=None, type=int, help="Req satellite arc length (minutes)")
    parser.add_argument("-e1", default=None, type=str, help="override min elev angle")
    parser.add_argument("-e2", default=None, type=str, help="override max elev angle")

    args = parser.parse_args()

#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

#
# rename the user inputs as variables
#
    station = args.station
    year = int(args.year)
    doy= int(args.doy)
    # this is now optional
    snr_type = args.snr
    #snr_type = args.snrEnd


    if len(str(year)) != 4:
        print('Year must have four characters: ', year)
        sys.exit()

    if (doy > 366):
        print('doy cannot be larger than 366: ', year)
        sys.exit()

# allow people to have an extension to the output file name so they can run different analysis strategies
# this is undocumented and only for Kristine at the moment
    if args.extension == None:
        extension = ''
    else:
        extension = args.extension

    lsp = guts.read_json_file(station, extension)
    #print(lsp)
    # now check the overrides to the json instructions
    #print('plt argument', args.plt)
    if args.plt == 'True':
        lsp['plt_screen'] = True
    elif args.plt == 'False':
        lsp['plt_screen'] = False

    if (args.delTmax != None):
        lsp['delTmax'] = args.delTmax
        print('Using user defined maximum satellite arc time (minutes) ', lsp['delTmax'])

# though I would think not many people would do this ... 
    if (args.compress != None):
        if args.compress == 'True':
            lsp['wantCompression'] = True
        else:
            lsp['wantCompression'] = False


    #print(lsp['screenstats'], 'screenstats from json')
    # do you override them?
    if args.screenstats == 'False':
        print('No statistics will come to the screen')
        lsp['screenstats'] = False
    if args.screenstats == 'True':
        print('Statistics will come to the screen')
        lsp['screenstats'] = True

# in case you want to analyze multiple days of data
    if args.doy_end == None:
        doy_end = doy
    else:
        doy_end = int(args.doy_end)

# in case you want to analyze multiple years of data
    if args.year_end == None:
        year_end = year
    else:
        year_end = int(args.year_end)

# default will be to overwrite
    if args.nooverwrite == None:
        lsp['overwriteResults'] = True
        print('LSP results will be overwritten')
    else:
        lsp['overwriteResults'] = False
        print('LSP results will not be overwritten')

    if (args.e1 != None):
        print('Overriding minimum elevation angle: ',args.e1)
        lsp['e1'] = float(args.e1)
    if (args.e2 != None):
        print('Overriding maximum elevation angle: ',args.e2)
        lsp['e2'] = float(args.e2)

# number of azimuth regions 
    naz = int(len(lsp['azval'])/2)
# in case you want to look at a restricted azimuth range from the command line 
    setA = 0
    if args.azim1 == None:
        azim1 = 0
    else:
        setA = 1; azim1 = args.azim1

    if args.azim2 == None:
        azim2 = 360
    else:
        azim2 = args.azim2; setA = setA + 1

    if (setA == 2):
        naz = 1; 
        lsp['azval']  = [azim1,  azim2]

# this is for when you want to run the code with just a single frequency, i.e. input at the console
# rather than using the input restrictions
    if args.fr != None:
        lsp['freqs'] = [args.fr]
        print('Overriding frequency choices')
    if args.ampl != None:
        print('Overriding amplitude choices')
        lsp['reqAmp'] = [args.ampl]

    if args.sat != None:
        print('Overriding - only looking at a single satellite')
        lsp['onesat'] = [args.sat]


    year_list = list(range(year, year_end+1))
    doy_list = list(range(doy, doy_end+1))
    for year in year_list:
        for doy in doy_list:
            print('--------------------------------------------------')
            print('RESULTS gnssir for: ', station, year, doy)
            print('--------------------------------------------------')
            guts.gnssir_guts(station,year,doy, snr_type, extension,lsp)

if __name__ == "__main__":
    main()

# get instructions first - this should be a standalone function some day
# instructions_ext = str(os.environ['REFL_CODE']) + '/input/' + station + '.' + extension + '.json'
# instructions = str(os.environ['REFL_CODE']) + '/input/' + station + '.json'
# if os.path.isfile(instructions_ext):
#     print('using specific instructions for this extension')
#     with open(instructions_ext) as f:
#             lsp = json.load(f)
# else:
#    print('will use the default instructions')
#    if os.path.isfile(instructions):
#        with open(instructions) as f:
#            lsp = json.load(f)
#    else:
#        print('Instruction file does not exist: ', instructions)
#        print('Please make with make_json_input and run this code again.')
#        sys.exit()

