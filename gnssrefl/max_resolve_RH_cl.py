import argparse
import numpy as np
import os
import subprocess
import sys

import gnssrefl.gps as g
import gnssrefl.refl_zones as rz
import gnssrefl.nyquist_libs as nl

from gnssrefl.utils import validate_input_datatypes, str2bool


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('station', help='station', type=str)
    parser.add_argument('-lat', help='Latitude (deg), if station not in database', type=float, default=None)
    parser.add_argument('-lon', help='Longitude (deg), if station not in database', type=float, default=None)
    parser.add_argument('-el_height', help='Ellipsoidal height (m) if station not in database', type=float,default=None)
    parser.add_argument('-e1', help='min elevation angle (deg), default 5 ', type=float,default=None)
    parser.add_argument('-e2', help='max elevation angle (deg), default 25', type=float,default=None)
    parser.add_argument('-samplerate', help='receiver sample rate (sec), default 30', type=float,default=None)
    parser.add_argument('-system', help='default=gps, other options : galileo, glonass, beidou', type=str)
    parser.add_argument('-hires_figs', default=None,help='whether you want eps instead of png plots', type=str)

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['hires_figs']
    args = str2bool(args, boolean_args)


    return {key: value for key, value in args.items() if value is not None}

def max_resolve_RH(station: str, lat: float=None, lon: float=None, el_height: float=None, e1: float=5, e2: float=25, 
        samplerate : float = 30, system: str = 'gps', hires_figs : bool = False):
    """
    Calculates the Maximum Resolvable Reflector Height. This is analogous to a Nyquist
    frequency for GNSS-IR.  It creates a plot and makes a plain txt file in case you 
    want to look at the numbers.

    Examples
    --------
    max_resolve_RH sc02 -e1 5 -e2 15
        typical case for sites over water (5-15 degrees) but otherwise using defaults (GPS, 30 seconds)

    max_resolve_RH sc02 -samplerate 15 -system galileo
        Assume receiver sampling rate of 15 seconds and the Galileo constellation

    max_resolve_RH xxxx -lat 40 -lon 100 -el_height 20
        test your own site (xxxx) by inputting coordinates
    

    Parameters
    ----------
    station : str
        4 ch station name
    lat : float, optional
        latitude in deg
    lon : float, optional
        longitude in deg
    el_height : float, optional
        ellipsoidal height in m
    e1 : float
        min elevation angles (deg)
    e2 : float
        max elevation angles (deg)
    samplerate : float
        receiver sampling rate
    system : str, optional
        name of constellation (gps,glonass,galileo, beidou allowed)
        default is gps
    hires_figs : bool
        whether you want eps files instead of png 

    Returns
    -------
    Creates a figure file, stored in $REFL_CODE/Files/station

    """
    foundfiles = rz.save_reflzone_orbits()
    if not foundfiles:
        print('The orbit files needed for this code were either not found')
        print('or not downloaded successfully. They should be in the REFL_CODE/Files directory')
        sys.exit()



    if (lat is None) & (lon is None):
    # check the station coordinates in our database from the station name
        lat, lon, el_height = g.queryUNR_modern(station)
        if (lat == 0) and (lon == 0):
            print('Exiting.')
            sys.exit()
        else:
            print('Using inputs:', lat, lon, el_height)
    else:
        print('Using inputs:', lat, lon, el_height)

    orbfile, it =  rz.set_system(system)

    xx,yy,zz = g.llh2xyz(lat,lon,el_height);
    recv=np.array([xx,yy,zz])
    # main code that does everything
    nl.pickup_files_nyquist(station,recv,orbfile,it,e1,e2,samplerate,hires_figs)


def main():
    args = parse_arguments()
    data = max_resolve_RH(**args)


if __name__ == "__main__":
    main()

