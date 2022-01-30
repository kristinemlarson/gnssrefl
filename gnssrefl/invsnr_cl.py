# wrapper to call invsnr codes

import argparse
import json
import os
import sys

# all the main functions used by the code are stored here
import gnssrefl.spline_functions as spline_functions

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", default=None,type=str)
    parser.add_argument("year", default=None, type=int, help="year")
    parser.add_argument("doy", default=None, type=int, help="doy")
    parser.add_argument("signal", default=None, type=str, help="signal, L1, L2, or L5")
  
    parser.add_argument("-pktnlim", default=None, type=float, help="peak2noise ratio for QC")
    parser.add_argument("-constel", default=None, type=str, help="single constellation (G,E, or R)")
    parser.add_argument("-screenstats", default=None, type=str, help="screen stats, False is default")
    parser.add_argument("-tempres", default=None, type=int, help="SNR file decimator (seconds)")
    parser.add_argument("-polydeg", default=None, type=int, help="polynomial degree for direct signal removal (default is 2)")
    parser.add_argument("-snrfit", default=None, type=str, help="Do invsnr fit? True is the default ")
    parser.add_argument("-doplot", default=None, type=str, help="Plot to the screen?  default is True")
    parser.add_argument("-doy_end", default=None, type=str, help="day of year to end analysis")
    parser.add_argument("-lspfigs", default=None, type=str, help="make LSP plots, default False. slow.") 
    parser.add_argument("-snrfigs", default=None, type=str, help="make SNR plots, default False. slow.")
    parser.add_argument("-knot_space", default=None, type=int, help="knot spacing in hours")

    args = parser.parse_args()
# the required inputs
    station = args.station
    year = args.year 
    doy = args.doy  
    signal = args.signal
    if signal not in ['L1','L2','L5','L1+L2','L1+L2+L5','L1+L5']:
        print('Illegal signal:', signal)
        sys.exit()

    # build a dictionary with the analysis inputs
    lsp = {} # ??? do i need this?
    # environment variable for the file inputs
    xdir = os.environ['REFL_CODE']
    # location of the analysis inputs, if it exists
    jsondir  = xdir + '/input/'
# file using the current directory location
    instructions =  station + '.inv.json'
# file using the gnssrefl package directory
    instructions2 =  jsondir + station + '.inv.json'

    if os.path.isfile(instructions):
        print('using:', instructions)
        with open(instructions) as f:
            lsp = json.load(f)
    else:
        if os.path.isfile(instructions2):
            print('using:', instructions2)
            with open(instructions2) as f:
                lsp = json.load(f)
        else:
            print('instruction file does not exist. exiting')
            sys.exit()

# save json inputs to variables
    precision = lsp['precision']
    azilims = lsp['azilims']
    elvlims = lsp['elvlims']
    rhlims = lsp['rhlims']
    l2c_only = lsp['l2c_only']

# variable for whether plot comes to the screen
    if (args.doplot == None):
        doplot = True
    else:
        doplot = False

# whether you do the inversion (can just do LSP? )
    snrfit = True
    if (args.snrfit == 'False'):
        snrfit = False

# the decimation value. Default is everything (1 second)
    if (args.tempres != None):
        tempres = args.tempres
    else:
        tempres = 1

# whether stats about the fit and satellite tracks are printed to the screen
    screenstats = False
    if args.screenstats == 'True':
        screenstats = True

# peak to noise ratio limit
    if args.pktnlim == None:
        pktnlim = 4
    else:
        pktnlim = args.pktnlim

# multi doy listing
    if args.doy_end == None:
        doy_end = doy
    else:
        doy_end = int(args.doy_end)

# set constellation.
    if args.constel == None:
        satconsts=['E','G','R'] # the default is gps,glonass, and galileo
    else: 
        satconsts=[args.constel]
        # save people from themselves
        if (args.constel == 'R') and (signal == 'L5'):
            print('illegal constellation/frequency choice',args.constel,'/','signal')
            sys.exit()
        if (args.constel == 'E') and (signal == 'L2'):
            print('illegal constellation/frequency choice', args/constel, '/', signal)
            sys.exit()

# don't turn these on unless you really need plots be acuse it is slow to make one
# per satellite arc
    snrfigs = False
    lspfigs = False
    if args.snrfigs== 'True':
        snrfigs = True; 
    if args.lspfigs== 'True':
        lspfigs = True 

# default knot spacing  in hours
    knot_space = 3 # default
    if (args.knot_space != None):
        knot_space = int(args.knot_space)
    print('Knot spacing (hours):', knot_space)

# default is to only use l2c GPS satellites (rather than all satellites)
    l2conly = True
    kdt = knot_space * 60 * 60  # change knot spacing to seconds 

    spline_functions.snr2spline(station,year,doy, azilims, elvlims, rhlims, precision,kdt, signal=signal,lspfigs=lspfigs,snrfigs=snrfigs,snrfit=snrfit,doplot=doplot, pktnlim=pktnlim,satconsts=satconsts,screenstats=screenstats,tempres=tempres,doy_end=doy_end,l2c_only=l2c_only)


if __name__ == "__main__":
    main()


