# -*- coding: utf-8 -*-
import argparse
import datetime
import numpy as np
import os
import sys
import subprocess
import time

import gnssrefl.gps as g
import gnssrefl.nmea2snr as nmea
import gnssrefl.gnssir_v2 as guts2

from gnssrefl.utils import validate_input_datatypes, str2bool

import multiprocessing
from functools import partial


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("doy", help="start day of year", type=int)

    parser.add_argument("-snr", default=66, help="snr file type, 99: 5-30 deg.; 66: < 30 deg.; 88: all data; 50: < 10 deg", type=int)
    parser.add_argument("-year_end", default=None, help="end year", type=int)
    parser.add_argument("-doy_end", default=None, help="end day of year", type=int)
    parser.add_argument("-overwrite", default=None, help="boolean", type=str)
    parser.add_argument("-dec", default=None, help="decimation, seconds", type=int)
    parser.add_argument("-lat", default=None, help="latitude, degrees", type=float)
    parser.add_argument("-lon", default=None, help="longitude, degrees", type=float)
    parser.add_argument("-height", default=None, help="ellipsoid height, m", type=float)
    parser.add_argument("-risky", default=None, help="boolean for whether low quality orbits are used instead of precise sp3", type=str)
    parser.add_argument("-gzip", default=None, help="gzip SNR file after creation. Default is true.", type=str)
    parser.add_argument("-par", default=None, help="parallel processing, up to 10", type=int)
    parser.add_argument("-orb", default=None, help="request specific orbit source", type=str)
    parser.add_argument("-hour", default=None, help="request hour for ultra orbit", type=int)

    g.print_version_to_screen()

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['risky', 'gzip', 'overwrite']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}

def nmea2snr( station: str, year: int, doy: int, snr: int = 66, year_end: int=None, doy_end: int=None, 
             overwrite : bool=False, dec : int=1, lat : float = None, lon : float=None, 
             height : float = None, risky : bool=False, gzip : bool = True, par:int = None, orb:str = None, hour:int =0):
    """
    This code creates SNR files from NMEA files.  

    The NMEA files should be stored in $REFL_CODE/nmea/ssss/2023 for station ssss and year 2023
    or $REFL_CODE/nmea/SSSS/2023 for station SSSS. The NMEA files should be named 
    SSSS1520.23.A or ssss1520.23.A, where the day of year is 152 and year is 2023 in this example.

    The SNR files created are stored with upper case if given upper case, lower case if given lower case.
    Currently I have left the last character in the file name as it was given to me - capital A.
    If this should be lower case for people that use lowercase station names, please let me know.
    As far as I can tell, the necessary fields in the NMEA files are GPGGA and GPGSV.

    Originally this code used interpolations of the az and el NMEA fields. I have decided this 
    is DANGEROUS. If you really want to use those low-quality measurements, you have to say -risky T

    The default usage is to use multi-GNSS orbits from GFZ.  To compute az-el, you need to 
    provide a priori station coordinates. You can submit those on the 
    command line or it will read them from the $REFL_CODE/input/ssss.json file 
    (for station ssss or SSSS) if it exists.

    As of 2023 September 14, the SNR files are defined in GPS time, which is how the file is defined.
    Prior to version 1.7.0, if you used the sp3 option, the SNR files were written in UTC. This led to 
    the orbits being propagated to the wrong time and thus az-el values are biased. The impact on RH 
    is not necessarily large - but you should be aware. The best thing to do is remake your SNR files.  

    As for March 16, 2024, this code has been changed to use gnssrefl standards for inputs and outputs.
    The code, in principle, now looks for final, rapid, and ultra rapid orbits from GFZ, in that order.

    As of version 3.6.4 you no longer have to enter station coordinates on the command line. 
    You just need to follow the instructions in the file formats documentation to set up a list of the locations of 
    your local stations. 

    Parameters
    ----------
    station : str
        4 ch name of station
    year : int
        full year
    doy : int
        day of year
    snr : int, optional
        snr file type (default is 66); 99: 5-30 deg.; 66: < 30 deg.; 88: all data; 50: < 10 deg
    year_end : int, optional
        final year
    doy_end : int, optional
        final day of year
    overwrite : bool, optional
        whether make a new SNR file even if one already exists
    dec : int, optional
        decimation in seconds
    lat: float, optional
        latitude, deg, 
    lon: float, optional
        longitude, deg
    height: float, optional
        ellipsoidal height, m
    risky : bool, optional
        confirm you want to use low quality orbits (default is False)
    gzip : bool, optional
        compress SNR files after creation.  Default is true
    par : int
        number of parallel processes. default is none (i.e. 1)
    orb : str
        specific orbit source (gnss, rapid, ultra, wum2). default is rapid
    hour : int
        specific hour of ultrarapid orbit. default is zero

    Examples
    --------
    nmea2snr wesl 2023 8 -dec 5
         makes SNR file with decimation of 5 seconds with good orbits

    nmea2snr wesl 2023 8 
         makes SNR file with original sampling rate  and good orbits

    nmea2snr xyz2 2023 8 -lat 40.2342 -lon -120.32424 -height 12
         makes SNR file with user provided station coordinates and good orbits

    """
    # queue which handles any exceptions any of the processes encounter
    manager = multiprocessing.Manager()
    error_queue = manager.Queue()


    g.check_environ_variables()

    NS = len(station)
    if (NS != 4):
        print('Illegal input - Station name must have 4 characters. Exiting.')
        sys.exit()

    # THIS CODE DOES NOT USE OUR ACCEPTED PROTOCOLS for argparse
    if len(str(year)) != 4:
        print('Year must be four characters long. Exiting.', year)
        sys.exit()    

    # 
    gfz_date = 2021 + 137/365.25
    # assume people are sensible until proven otherwise

    recv = [0,0,0]
    llh = [lat,lon,height]    

    if risky:
        print('You insist on using low quality az-el NMEA values and have set the risky option to True.')
        sp3 = False
    else:
        sp3 = True
        # check local coordinte file
        foundcoords, lat, lon, ht = g.query_coordinate_file(station)
        if foundcoords:
            print(lat,lon,ht)
            x,y,z = g.llh2xyz(lat,lon,ht)
            recv = [x,y,z]
        else:
        # try to get a priori coordinates, Cartesian
            recv, foundcoords = nmea.nmea_apriori_coords(station,llh,sp3)
        if not foundcoords:
            print('The default in this code is to use precise orbits to calculate az/el values.')
            print('We need to know apriori coordinates for your site. Please input lat/lon/ellipsoidal height ')
            print('on the command line or use a local coordinate file as explained in the documentation for')
            print('query_coordinate_file. You can also store the values using gnssir_input.')
            sys.exit()


    if doy_end is None:
        doy_end = doy
    if year_end is None:
        year_end = year



    MJD1 = int(g.ydoy2mjd(year,doy))
    MJD2 = int(g.ydoy2mjd(year_end,doy_end))

    #def run_nmea2snr(station, year, doy, isnr, overwrite, dec, llh, sp3, gzip):
    # calling cartesian coordinates llh is so wrong
    args = {'station': station, 'isnr': snr,  'overwrite': overwrite, 'dec':dec, 'llh': llh, 'recv': recv, 'sp3': sp3, 'gzip': gzip, 'orb': orb, 'hour': hour}

    # first get it working without parallel processing
    if not par:
        print('No parallel processing')
        mjd_list = {}; mjd_list[0] = [MJD1, MJD2]
        s1 = time.time()
        process_jobs_multi(index=0,args=args,datelist=mjd_list,error_queue=error_queue)
        s2 = time.time()
        print('That took ', round(s2-s1,2), ' seconds')
    else:
        if par > 10:
            print('Only allow ten parallel processes for now')
            par = 10
        numproc = par

        # get a list of times in MJD associated with the multiple spawned processes
        # this does not work for skipping dates though ...
        datelist, numproc = guts2.make_parallel_proc_lists_mjd(year, doy, year_end, doy_end, numproc)
        print(datelist)

        # make a list of process IDs
        index = list(range(numproc))
        s1 = time.time()

        pool = multiprocessing.Pool(processes=numproc)

        partial_process = partial(process_jobs_multi, args=args,datelist=datelist,error_queue = error_queue)

        pool.map(partial_process,index)

        pool.close()
        pool.join()
        s2 = time.time()
        print('That took ', round(s2-s1,2), ' seconds')


def process_jobs_multi(index,args,datelist,error_queue):
    """
    runs the nmea2snr queue

    Parameters
    ----------
    index : int
        which job to run
    args : dict
        dictionary of parameters for run_nmea2snr
    datelist: dict
        start and stop dates in MJD
    error_queue:?
        not sure how to describe this

    """

    # should try be on each submission?  or each list of submissions?
    try:
        d1 = datelist[index][0]; d2 = datelist[index][1]
        mjd_list = list(range(d1, d2+1))
        for mjd in mjd_list:
            y, d = g.modjul_to_ydoy(mjd)
            args['year'] = y
            args['doy'] = d
            nmea.run_nmea2snr(**args)

    except Exception as e:
        print('Error of some kind processing year/doy ', y, d)
        error_queue.put(e)

    return


def main():
    args = parse_arguments()
    nmea2snr(**args)


if __name__ == "__main__":
    main()

