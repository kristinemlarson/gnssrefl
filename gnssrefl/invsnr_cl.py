# wrapper to call invsnr codes

import argparse
import json
import os
import sys

# 22feb09 adding beidou
# 22mar08 adding refraction

# all the main functions used by the code are stored here
import gnssrefl.spline_functions as spline_functions
import gnssrefl.refraction as refr

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", default=None,type=str)
    parser.add_argument("year", default=None, type=int, help="year")
    parser.add_argument("doy", default=None, type=int, help="doy")
    parser.add_argument("signal", default=None, type=str, help="L1, L2, L5, L1+L2, L1+L2+L5, etc")
  
    parser.add_argument("-pktnlim", default=None, type=float, help="Peak2noise ratio for Quality Control")
    parser.add_argument("-constel", default=None, type=str, help="Only a single constellation (G,E, or R)")
    parser.add_argument("-screenstats", default=None, type=str, help="screen stats, False is default")
    parser.add_argument("-tempres", default=None, type=int, help="SNR file decimator (seconds)")
    parser.add_argument("-polydeg", default=None, type=int, help="polynomial degree for direct signal removal (default is 2)")
    parser.add_argument("-snrfit", default=None, type=str, help="Do invsnr fit? True is the default ")
    parser.add_argument("-doplot", default=None, type=str, help="Plot to the screen?  default is True")
    parser.add_argument("-doy_end", default=None, type=str, help="day of year to end analysis")
    parser.add_argument("-lspfigs", default=None, type=str, help="Make LSP plots, default False.") 
    parser.add_argument("-snrfigs", default=None, type=str, help="Make SNR plots, default False.")
    parser.add_argument("-knot_space", default=None, type=str, help="knot spacing in hours (default is 3)")
    parser.add_argument("-rough_in", default=None, type=str, help="Roughness (default is 0.1)")
    parser.add_argument("-risky", default=None, type=str, help="Risky taker related to gaps/knot spacing, False is default)")
    parser.add_argument("-snr_ending", default=None, type=str, help="SNR file ending. Default is 66)")
    parser.add_argument("-outfile_type", default=None, type=str, help="Output file type (txt or csv)")
    parser.add_argument("-delta_out", default=None, type=str, help="Output increment, in seconds (default is 300)")
    parser.add_argument("-refraction", default=None, type=str, help="Set to True to turn on")

    args = parser.parse_args()
# the required inputs
    station = args.station
    year = args.year 
    doy = args.doy  
    signal = args.signal
    if signal not in ['L1','L2','L5','L6','L7','L1+L2','L1+L2+L5','L1+L5','ALL']:
        print('Currently only allow L1,L2,L5,L6,L7 and various combinations')
        print('Illegal signal:', signal)
        sys.exit()
    if signal == 'ALL':
        print('Using all signals')
        signal = 'L1+L2+L5+L6+L7'
    print(signal)
    # build a dictionary with the analysis inputs
    lsp = {} # ??? do i need this?
    # environment variable for the file inputs
    xdir = os.environ['REFL_CODE']
    # location of the analysis inputs, if it exists
    jsondir  = xdir + '/input/'
    instructions2 =  jsondir + station + '.inv.json'

    if os.path.isfile(instructions2):
        print('using:', instructions2)
        with open(instructions2) as f:
            lsp = json.load(f)
    else:
        print('Instruction file does not exist.', instructions2, ' Exiting.')
        sys.exit()

# look into the refraction issue

# save json inputs to variables
# this is ridiculous - I should just send the dictionary!
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
        # added beidou 22feb09
        satconsts=['E','G','R','C'] # the default is gps,glonass, and galileo
    else: 
        satconsts=[args.constel]
        # save people from themselves
        if (args.constel == 'R') and (signal == 'L5'):
            print('illegal constellation/frequency choice',args.constel,'/','signal')
            sys.exit()
        if (args.constel == 'E') and (signal == 'L2'):
            print('illegal constellation/frequency choice', args/constel, '/', signal)
            sys.exit()
        if (args.constel == 'C') and (signal == 'L1' or signal == 'L5'):
            print('illegal constellation/frequency choice', args/constel, '/', signal)
            sys.exit()
        #if (args.constel == 'C') and (signal == 'L6' or signal == 'L7'):
        #    print('Sorry - I have not added L6 and L7 to the code yet. Exiting.')
        #    sys.exit()

# don't turn these on unless you really need plots be acuse it is slow to make one
# per satellite arc
    snrfigs = False
    lspfigs = False
    if args.snrfigs== 'True':
        snrfigs = True; 
    if args.lspfigs== 'True':
        lspfigs = True 

# default roughness 
    rough_in = 0.1 # default
    if (args.rough_in != None):
        rough_in  = float(args.rough_in)
    print('Roughness:', rough_in)

    risky = False
    if (args.risky != None):
        if args.risky == 'True':
            risky = True

    snr_ending = 66 
    if (args.snr_ending!= None):
        snr_ending = int(args.snr_ending)

# default knot spacing  in hours
    knot_space = 3.0 # default
    if (args.knot_space != None):
        knot_space = float(args.knot_space)
    print('Knot spacing (hours):', knot_space)

# default is to only use l2c GPS satellites (rather than all satellites)
    l2conly = True
    kdt = knot_space * 60 * 60  # change knot spacing to seconds 

# default is 300 seconds and plain txt
    if (args.delta_out == None):
        delta_out = 300
    else:
        delta_out = int(args.delta_out)

    if (args.outfile_type == None):
        outfile_type = 'txt'
    else:
        outfile_type = args.outfile_type

    # trying to add refraction to an existing dictionary. this is how it is done in the main lsp code
    lsp['refraction'] = False
    if (args.refraction == None):
        lsp['refraction'] = True 
    else:
        if args.refraction == 'True':
            lsp['refraction'] = True 

    spline_functions.snr2spline(station,year,doy, azilims, elvlims, rhlims, precision,kdt, signal=signal,lspfigs=lspfigs,snrfigs=snrfigs,snrfit=snrfit,doplot=doplot, pktnlim=pktnlim,satconsts=satconsts,screenstats=screenstats,tempres=tempres,doy_end=doy_end,l2c_only=l2c_only,rough_in=rough_in,risky=risky,snr_ending=snr_ending,outfile_type=outfile_type,delta_out=delta_out,lsp=lsp)


if __name__ == "__main__":
    main()


