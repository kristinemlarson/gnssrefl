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


def parse_arguments():
# user inputs the observation file information
    parser = argparse.ArgumentParser()
# required arguments
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("h1", default=None, type=float, help="Lower limit reflector height (m)")
    parser.add_argument("h2", default=None, type=float, help="Upper limit reflector height (m)")
    parser.add_argument("e1", default=None, type=float, help="Lower limit elev. angle (deg)")
    parser.add_argument("e2", default=None, type=float, help="Upper limit elev. angle (deg)")

    parser.add_argument("-a1", default=None, type=float, help="Lower limit azimuth angle (deg)")
    parser.add_argument("-a2", default=None, type=float, help="Upper limit azimuth angle (deg)")

    parser.add_argument("-lat", help="Latitude (degrees)", type=str, default=None)
    parser.add_argument("-lon", help="Longitude (degrees)", type=str, default=None)
    parser.add_argument("-height", help="Ellipsoidal height (meters)", type=str, default=None)
# these are the optional inputs 
    args = parser.parse_args().__dict__

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def invsnr_input(station: str, h1: float, h2: float, e1: float, e2: float, a1: float = 0,
                 a2: float = 360, lat: float = None, lon: float = None, height: float = None):
    """
    Parameters
    ----------
    station : string
        Character ID of the station

    h1 : float
        Lower limit reflector height (m)

    h2 : float
        Upper limit reflector height (m)

    e1 : float
        Lower limit elev. angle (deg)

    e2 : float
        Upper limit elev. angle (deg)

    a1 : float, optional
        Lower limit azimuth angle (deg)

    a2 : float, optional
        Upper limit azimuth angle (deg)

    lat : float, optional
        Latitude (degrees)

    lon : float, optional
        Longitude (degrees)

    height : float, optional
        Ellipsoidal height (meters)

    """

# rename the user inputs into variables
#
    NS = len(station)
    if (NS != 4):
        print('station name must be four characters long. Exiting.')
        sys.exit()
    Lat, Long, Height = g.queryUNR_modern(station)
    if Lat == 0:
        if lat is None:
            print('I did not find your station at UNR.')
            print('You need to set them using -lat, -lon, -height')
            sys.exit()
        else:
            Lat = float(lat)
            Long = float(lon)
            Height = float(height)

# start the lsp dictionary (left over name from another piece of code)
    lsp={}
    lsp['station'] = station
    lsp['lat'] = Lat; lsp['lon'] = Long; lsp['ht']=Height
#
    if h1 > h2:
        print('h1 cannot be greater than h2. ', h1, h2, ' Exiting.')
        sys.exit()

    if e1 > e2:
        print('e1 must be less than e2.', e1, e2, ' Exiting.')
        sys.exit()

    if a1 > a2:
        print('a1 must be less than a2.', a1, a2, ' Exiting.')
        sys.exit()

    # make groupings of RH, ele, and azim limits
    lsp['rhlims'] = [h1, h2]
    lsp['elvlims'] = [e1, e2]
    lsp['azilims'] = [a1, a2]

# where the instructions will be written eventually. for now in the current directory
    if 'REFL_CODE' not in os.environ:
        print('The REFL_CODE environment variable has not been set, Please take care of this.')
        print('Exiting')
        sys.exit()
    xdir = os.environ['REFL_CODE']
    outputdir  = xdir + '/input' 
    if not os.path.isdir(outputdir):
        subprocess.call(['mkdir', outputdir])
# 
    lsp['precision'] = 0.005 # precision of RH in meters
# 
    lsp['l2c_only'] = True

    outputfile = outputdir + '/' + station + '.inv.json'
    print('writing json file to:', outputfile)
    print(lsp)
    with open(outputfile, 'w+') as outfile:
        json.dump(lsp, outfile, indent=4)


def main():
    args = parse_arguments()
    invsnr_input(**args)

if __name__ == "__main__":
    main()
