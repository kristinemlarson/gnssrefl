#
# Author: Kristine M. Larson
# Date: december 25, 2021
# Purpose: help set up json input file needed for snr inversion code

import argparse
import json
import os
import subprocess
import sys

# internal library of GPS functions
import gnssrefl.gps as g

# function to read UNR database
# import unr 

def main():

# user inputs the observation file information
    parser = argparse.ArgumentParser()
# required arguments
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("h1", default=None, type=float, help="lower limit reflector height (m)")
    parser.add_argument("h2", default=None, type=float, help="upper limit reflector height (m)")
    parser.add_argument("e1", default=None, type=float, help="lower limit elev. angle (deg)")
    parser.add_argument("e2", default=None, type=float, help="upper limit elev. angle (deg)")

    parser.add_argument("-azim1", default=None, type=float, help="lower limit azimuth angle (deg)")
    parser.add_argument("-azim2", default=None, type=float, help="upper limit azimuth angle (deg)")

    parser.add_argument("-lat", help="latitude (degrees)", type=str,default=None)
    parser.add_argument("-long", help="longitude (degrees)", type=str, default=None)
    parser.add_argument("-height", help="ellipsoidal height (meters)", type=str, default=None)
# these are the optional inputs 
    args = parser.parse_args()
#

# make sure environment variables exist

# rename the user inputs into variables
#
    station = args.station
    NS = len(station)
    if (NS != 4):
        print('station name must be four characters long. Exiting.')
        sys.exit()
    Lat, Long, Height = g.queryUNR_modern(station)
    if (Lat == 0):
        if args.lat == None:
            print('I did not find your station at UNR.')
            print('You need to set them using -lat, -long, -height')
            sys.exit()
        else:
            Lat = float(args.lat)
            Long = float(args.long)
            Height = float(args.height)

# start the lsp dictionary (left over name from another piece of code)
    lsp={}
    lsp['station'] = station
    lsp['lat'] = Lat; lsp['lon'] = Long; lsp['ht']=Height

# reflector height limits (meters)
    h1 = args.rh1
    h2 = args.rh2
#
    if (h1 > h2):
        print('h1 cannot be greater than h2. ', h1, h2, ' Exiting.')
        sys.exit()

    e1 = float(args.elev1)
    e2 = float(args.elev2)
    if (e1 > e2):
        print('e1 must be less than e2.', e1, e2, ' Exiting.')
        sys.exit()

    if args.azim1 == None:
        azim1 = 0
    else: 
        a1 = float(args.azim1)

    if args.azim2 == None:
        azim2 = 360
    else: 
        a2 = float(args.azim2)

    if (a1 > a2):
        print('a1 must be less than a2.', a1, a2, ' Exiting.')
        sys.exit()

    # make groupings of RH, ele, and azim limits
    lsp['rhlims'] = [h1,h2]
    lsp['elvlims'] = [e1,e2]
    lsp['azilims'] = [a1,a2] 

# where the instructions will be written eventually. for now in the current directory
    if 'REFL_CODE' not in os.environ:
        print('The REFL_CODE environment variable has not been set, Please take care of this.')
        print('Exiting')
        sys.exit()
    xdir = os.environ['REFL_CODE']
    outputdir  = xdir + '/input' 
    if not os.path.isdir(outputdir):
        subprocess.call(['mkdir',outputdir])
# 
    lsp['precision']= 0.005 ; # precision of RH in meters
# 
    lsp['l2c_only'] = True;
 

    outputfile = outputdir + '/' + station + '.inv.json'
    print('writing json file to:', outputfile)
    print(lsp)
    with open(outputfile, 'w+') as outfile:
        json.dump(lsp, outfile,indent=4)

if __name__ == "__main__":
    main()
