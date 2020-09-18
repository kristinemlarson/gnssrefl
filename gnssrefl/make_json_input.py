#
# Author: Kristine M. Larson
# Date: august 25, 2020
# Purpose: help set up json input file needed for gnssIR_lomb.py

import argparse
import json
import os
import subprocess

import gnssrefl.gps as g

def main():

# user inputs the observation file information
    parser = argparse.ArgumentParser()
# required arguments
    parser.add_argument("station", help="station (lowercase)", type=str)
    parser.add_argument("lat", help="latitude (degrees)", type=float)
    parser.add_argument("long", help="longitude (degrees)", type=float)
    parser.add_argument("height", help="ellipsoidal height (meters)", type=float)
# these are the optional inputs 
    parser.add_argument("-e1", "--e1", default=None, type=int, help="lower limit elevation angle")
    parser.add_argument("-e2", "--e2", default=None, type=int, help="upper limit elevation angle")
    parser.add_argument("-h1", "--h1", default=None, type=float, help="lower limit reflector height (m)")
    parser.add_argument("-h2", "--h2", default=None, type=float, help="upper limit reflector height (m)")
    parser.add_argument("-nr1", "--nr1", default=None, type=float, help="lower limit noise region for QC(m)")
    parser.add_argument("-nr2", "--nr2", default=None, type=float, help="upper limit noise region for QC(m)")
    parser.add_argument("-peak2noise", "--peak2noise", default=None, type=float, help="peak 2 noise ratio used for QC")
    args = parser.parse_args()
#

# make sure environment variables exist
    g.check_environ_variables()

# rename the user inputs into variables
#
    station = args.station
# location of the site - does not have to be very good.  within 100 meters is fine
    Lat = args.lat
    Long = args.long
    Height = args.height

# start the lsp dictionary
    lsp={}
    lsp['station'] = station
    lsp['lat'] = Lat; lsp['lon'] = Long; lsp['ht']=Height

# reflector height (meters)
    if (args.h1 != None):
        h1 = args.h1
    else:
        h1=0.5

    if (args.h2 != None):
        h2 = args.h2
    else:
        h2=6.0
#
    lsp['minH'] = h1; lsp['maxH'] = h2

# elevation angles (degrees)
    if (args.e1 != None):
        e1 = args.e1
    else:
        e1 = 5

    if (args.e2 != None):
        e2 = args.e2
    else:
        e2 = 25
    lsp['e1'] = e1; lsp['e2'] = e2

# the default noise region will the same as the RH exclusion area for now
    nr1=h1 
    nr2=h2
    if (args.nr1 != None):
        nr1 = args.nr1
    if (args.nr2 != None):
        nr2 = args.nr2
#
    lsp['NReg'] = [nr1, nr2]

    if (args.peak2noise == None):
        lsp['PkNoise'] = 2.7  # just a starting point for water - should be 3 or 3.5 for snow ... 
    else:
        lsp['PkNoise'] = args.peak2noise  

# where the instructions will be written
    xdir = os.environ['REFL_CODE']
    outputdir  = xdir + '/input' 
    if not os.path.isdir(outputdir):
        subprocess.call(['mkdir',outputdir])

    outputfile = outputdir + '/' + station + '.json'


    lsp['polyV'] = 4 ; # polynomial order for DC removal
    lsp['pele'] = [5, 30] # elevation angles used for DC removal
    lsp['ediff']= 2 ; # degrees
    lsp['desiredP']= 0.005 ; # precision of RH in meters
# azimuth regions in degrees (in pairs)
# you can of course have more subdivisions here
    lsp['azval'] = [0, 90 , 90 ,180 , 180 , 270 , 270 , 360] 
# 
# frequencies to use - and their required amplitudes. The amplitudes are not set in stone
#
    lsp['freqs'] = [1, 20]; lsp['reqAmp'] = [6, 6]
# use refraction correction
    lsp['refraction'] = True

# write new RH results  each time you run the code
    lsp['overwriteResults'] = True; 

# if snr file does not exist, try to make one
    lsp['seekRinex'] = False; 

# compress snr files after analysis - saves disk space
    lsp['wantCompression'] = False; 

# periodogram plots come to the screen
    lsp['plt_screen'] = False; 

# command line req to only do a single satellite - default is do all satellites
    lsp['onesat'] = None; 

# send some information on periodogram RH retrievals to the screen
    lsp['screenstats'] = True 

# save the output plots
    lsp['pltname'] = station + '_lsp.png'

# how long can the arc be, in minutes 
    lsp['delTmax'] = 75 # - this is appropriate for 5-30 degrees
 
    print('writing out to:', outputfile)
    with open(outputfile, 'w+') as outfile:
        json.dump(lsp, outfile,indent=4)

if __name__ == "__main__":
    main()
