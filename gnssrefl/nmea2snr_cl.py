# -*- coding: utf-8 -*-
import argparse
import datetime
import numpy as np
import os
import sys
import subprocess
import gnssrefl.gps as g
import gnssrefl.nmea2snr as nmea

def main():
    """
    main script for the nmea2snr conversion code

    Looks for NMEA files in $REFL_CODE/nmea/ssss/2023 for station ssss and year 2023
    or $REFL_CODE/nmea/SSSS/2023 for station SSSS. Personally I prefer lowercase station 
    names, but I believe the code allows you to do either.

    Files are named:  SSSS1520.23.A or ssss1520.23.A

    day of year is 152 and year is 2023 in this example

    The SNR files are stored with upper case if given upper case, lower case if given lower case.
    Currently I have left the last character in the file name as it was given to me - capital A.
    If this should be lower case for people that use lowercase station names, please let me know.

    As far as I can tell, the necessary fields in the NMEA files are GPGGA and GPGSV.

    Originally this code used interpolations of the az and el NMEA fields. I have decided this 
    is DANGEROUS. If you really want to use those low-quality measurements, you 
    can use them by saying -sp3 F. Otherwise, if your data were collected after 
    day of year 137 and year 2021, it will use the multi-GNSS sp3 file from GFZ. 
    This means you have to provide a priori station coordinates. You can submit those on the 
    command line or it will read them from the $REFL_CODE/input/ssss.json file (for station ssss or SSSS) if it exists.


    Parameters
    ----------
    station : str
        4 ch name of station
    year : int
        full year
    doy : int
        day of year
    snr : str, optional
        snr file type, default is 66
    overwrite : bool, optional
        whether make a new SNR file even if one already exists
    dec : int, optional
        decimation in seconds
    lat: float, optional
        latitude, deg, required for sp3file if json file not available
    lon: float, optional
        longitude, deg, required for sp3file if json file not available
    height: float, optional
        height, m, required for sp3file if json file not available
    sp3 : str, optional
        set to False or F to use low quality NMEA values for az and el angles.
        this is changed to a boolean in the nmea2snr command line tool.

    Examples
    --------
    nmea2snr wesl 2023 8 -dec 5
         makes SNR file with decimation of 5 seconds with good orbits

    nmea2snr wesl 2023 8 
         makes SNR file with original sampling rate  and good orbits

    nmea2snr xyz2 2023 8 -lat 40.2342 -lon -120.32424 -height 12
         makes SNR file with user provided station coordinates and good orbits

    """
    
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("doy", help="start day of year", type=int)

    parser.add_argument("-snr", default='66', help="snr file ending, 99: 5-30 deg.; 66: < 30 deg.; 88: all data; 50: < 10 deg", type=str)
    parser.add_argument("-doy_end", default=None, help="end day of year", type=int)
    parser.add_argument("-year_end", default=None, help="end year", type=int)
    parser.add_argument("-overwrite", default=None, help="boolean", type=str)
    parser.add_argument("-dec", default=None, help="decimation, seconds", type=int)
    parser.add_argument("-lat", default=None, help="latitude, degrees", type=float)
    parser.add_argument("-lon", default=None, help="longitude, degrees", type=float)
    parser.add_argument("-height", default=None, help="ellipsoid height,m", type=float)
    parser.add_argument("-sp3", default=None, help="boolean for whether sp3 orbits are used", type=str)
    parser.add_argument("-risky", default=None, help="boolean for whether sp3 orbits are used", type=str)

    args = parser.parse_args()

    g.check_environ_variables()

    station = args.station; 
    NS = len(station)
    if (NS != 4):
        print('Illegal input - Station name must have 4 characters. Exiting.')
        sys.exit()

    year = args.year
    if len(str(year)) != 4:
        print('Year must be four characters long. Exiting.', year)
        sys.exit()    

    isnr = args.snr
    isnr = int(isnr)

    if args.risky == None:
        risky = False
    else:
        if (args.risky == 'T') or (args.risky == 'True'):
            risky = True
        else:
            risky = False
        

    doy= args.doy
    if args.doy_end == None:
        doy2 = doy
    else:
        doy2 = args.doy_end
        
    year1=year
    if args.year_end == None:
        year2 = year 
    else:
        year2 = args.year_end
    doy_list = list(range(doy, doy2+1))
    year_list = list(range(year1, year2+1))
    
    overwrite = False
    if (args.overwrite == 'True') or (args.overwrite == 'T'):
        overwrite = True

    dec = 1
    if (args.dec is not None):
        dec = args.dec

    # 
    gfz_date = 2021 + 137/365.25
    # assume people are sensible until proven otherwise
    sp3 = True

    if (args.sp3 is not None):
        if (args.sp3 == 'False') or (args.sp3 == 'F'):
            sp3 = False

    if (year+doy/365.25 >= gfz_date):
        if not sp3:
            if risky:
                print('You insist on using low quality az-el NMEA values but have set the risky option to True')
                sp3 = False
            else:
                print('You insist on using low quality az-el NMEA values.  You must set risky to T or True to proceed.')
                sys.exit()
            
    else:
        print('Your data were collected before my code knows how to pick up GFZ rapid orbits')
        print('If you would like to use reliable orbits, please submit a PR pointing to other sp3 files.')
        if risky:
            print('You set risky to True. Proceeding.')
        else:
            print('You must set risky to T or True to proceed using the unreliable orbits.')
            sys.exit()
        sp3 = False

    if sp3 :
        print('Using GFZ multi-GNSS sp3 file for orbits')

    # for now set to zero as Makan's code does not need LLH
    lat = 0; lon = 0; height = 0;
    if args.lat is not None:
        lat = args.lat
    if args.lon is not None:
        lon = args.lon
    if args.height is not None:
        height = args.height
    llh = [lat,lon,height]    
    nmea.run_nmea2snr(station, year_list, doy_list, isnr, overwrite,dec,llh,sp3)

if __name__ == "__main__":
    main()
