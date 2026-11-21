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
    parser.add_argument("-h1", default=None, type=float, help="Lower limit reflector height (m), default 1")
    parser.add_argument("-h2", default=None, type=float, help="Upper limit reflector height (m), default 8")
    parser.add_argument("-e1", default=None, type=float, help="Lower limit elev. angle (deg), default 5")
    parser.add_argument("-e2", default=None, type=float, help="Upper limit elev. angle (deg), default 15")

    parser.add_argument("-azim1", default=None, type=float, help="Lower limit azimuth angle (deg), default 0")
    parser.add_argument("-azim2", default=None, type=float, help="Upper limit azimuth angle (deg), default 360")
    parser.add_argument("-peak2noise", default=None, type=float, help="Peak2noise QC criterion")

    parser.add_argument("-lat", help="Latitude (degrees)", type=str, default=None)
    parser.add_argument("-lon", help="Longitude (degrees)", type=str, default=None)
    parser.add_argument("-height", help="Ellipsoidal height (meters)", type=str, default=None)
    parser.add_argument("-knot_space", help="Knot spacing in hours ", type=float, default=3.0)
    parser.add_argument("-threedays", help="Doing a 3 day run", type=str, default=None)
    parser.add_argument("-extension", help="special analysis strategy name", type=str, default=None)
# these are the optional inputs 
    args = parser.parse_args().__dict__

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def invsnr_input(station: str, h1: float=1, h2: float=8, e1: float=5, e2: float=15, azim1: float = 0,
                 azim2: float = 360, lat: float = None, lon: float = None, height: float = None, 
                 peak2noise: float=3, knot_space=3.0, threedays=False, extension=None):
    """
    Sets some of the analysis parameters for invnsr. Values are stored in a json in $REFL_CODE/input
    Note: this code was written independently of gnssrefl. The Quality Control parametesr are thus quite 
    different from how gnssrefl is done. The LSP RH retrievals are not - and should not - be the same.

    Examples
    --------
    invsnr_input sc02 -h1 3 -h2 12 -e1 5 -e2 13 -azim1 40 -azim2 220
        general Friday Harbor inputs
    invsnr_input at01 -h1 9 -h2 14 -e1 5 -e2 13 -azim1 20 -azim2 22
        St Michael inputs 



    Parameters
    ----------
    station : str
        four ch ID of the station
    h1 : float, optional
        Lower limit reflector height (m)
    h2 : float, optional
        Upper limit reflector height (m)
    e1 : float, optional
        Lower limit elev. angle (deg)
    e2 : float
        Upper limit elev. angle (deg)
    azim1 : float 
        Lower limit azimuth angle (deg)
    azim2 : float 
        Upper limit azimuth angle (deg)
    lat : float, optional
        Latitude (degrees)
    lon : float, optional
        Longitude (degrees)
    height : float, optional
        Ellipsoidal height (meters)
    peak2noise : float, optional
        peak to noise 
    knot_space : float, optional
        how often are knots estimated (hours) 
    threedays : bool, optional
        whether you plan to use a three-day run
        i.e. the day before and after the one you really want.
    extension : str, optional
        whether you want to make a special analysis strategy file rather than
        default

    """

# rename the user inputs into variables
#
    # use old variable names
    a1=azim1
    a2=azim2
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

    station_config={}
    station_config['station'] = station
    station_config['lat'] = Lat; station_config['lon'] = Long; station_config['ht']=Height
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
    station_config['rhlims'] = [h1, h2]
    station_config['elvlims'] = [e1, e2]
    station_config['azilims'] = [a1, a2]
    station_config['knot_space'] = knot_space 
    station_config['threedays'] = threedays  

    # use david's naming convention for this
    station_config['pktnlim'] = peak2noise

# where the instructions will be written eventually. for now in the current directory
    if 'REFL_CODE' not in os.environ:
        print('The REFL_CODE environment variable has not been set, Please take care of this.')
        print('Exiting')
        sys.exit()
    xdir = os.environ['REFL_CODE']
    outputdir  = xdir + '/input/'  + station + '/inv'
    if not os.path.isdir(outputdir):
        subprocess.call(['mkdir', '-p', outputdir])
        print('made output directory')
    print('All json files created for invsnr are now stored in :', outputdir)
# 
    station_config['precision'] = 0.005 # precision of RH in meters
# 
    station_config['l2c_only'] = True

    #outputfile = outputdir + '/' + station + '.inv.json'
    # default name 
    outputfile = outputdir + '/' + station + '.inv.json'
    if extension is not None:
        print('Using extension option')
        outputfile = outputdir + '/' + station + '.' + extension + '.json'

    print('Writing json file to:', outputfile)
    with open(outputfile, 'w+') as outfile:
        json.dump(station_config, outfile, indent=4)


def main():
    args = parse_arguments()
    invsnr_input(**args)

if __name__ == "__main__":
    main()
