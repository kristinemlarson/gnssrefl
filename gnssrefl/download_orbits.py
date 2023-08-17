# -*- coding: utf-8 -*-
import argparse
import numpy as np
import sys
import time

import gnssrefl.gps as g


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("orbit", help="orbit name (gps,gnss,gps+glo, or specific e.g. jax) ", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("month", help="month (or day of year)", type=int)
    parser.add_argument("day", help="day (zero if you use day of year earlier)", type=int)
    parser.add_argument("-doy_end", default=None, help="doy end for multi-day download ", type=str)

    args = parser.parse_args().__dict__

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def download_orbits(orbit: str, year: int, month: int, day: int, doy_end: int = None ):
    """
    command line interface for download_orbits. If day is zero, then it is assumed that 
    the month record is day or year

    Examples
    --------
    download_orbits nav 2020 50 0
        downloads broadcast orbits for day of year 50 in the year 2020
    download_orbits nav 2020 1 1 
        downloads broadcast orbits for January 1, 2020
    download_orbits gnss 2023 1 1 
        multi-GNSS orbits from GFZ
    download_orbits rapid 2023 1 1 
        rapid multi-GNSS orbits from GFZ
    download_orbits rapid 2023 1 0 -doy_end 10
        rapid multi-GNSS orbits from GFZ for days of year 1 thru 10 in 2023

    Parameters
    ----------

    orbit : string
        value options:

            gps (default) : uses GPS broadcast orbit

            gps+glo : will use JAXA orbits which have GPS and Glonass (usually available in 48 hours)

            gnss : will use GFZ orbits, which is multi-GNSS (available in 3-4 days). but taken from CDDIS archive

            nav : GPS broadcast, adequate for reflectometry. Searches various places

            nav-sopac : GPS broadcast file from SOPAC, adequate for reflectometry. 

            nav-esa : GPS broadcast file from ESA, adequate for reflectometry. 

            nav-cddis : GPS broadcast file from CDDIS, very slow to download

            igs : IGS precise, GPS only

            igr : IGS rapid, GPS only

            jax : JAXA, GPS + Glonass, within a few days, missing block III GPS satellites

            gbm : GFZ Potsdam, multi-GNSS, not rapid

            grg : French group, GPS, Galileo and Glonass, not rapid

            esa : ESA, multi-GNSS

            gfr : GFZ rapid, GPS, Galileo and Glonass, since May 17 2021

            wum : (disabled) Wuhan, multi-GNSS, not rapid

            gnss2 : multi-GNSS, but uses IGN instead of CDDIS. does not work

            gnss3 : multi-GNSS, but uses GFZ archive instead of CDDIS. same as gnss-gfz

            ultra : ultra orbits directly from GFZ

            rapid : rapid orbits directly from GFZ

    year : integer
        full year
    month : integer
        calendar month
    day : integer
        day of the month
    doy_end : integer 
        optional, allows multiple day download

    """

#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

    orbit_list = ['igs', 'igr', 'jax', 'grg', 'wum', 'gbm', 'nav', 'gps', 'gps+glo', 
            'gnss', 'gfr', 'esa', 'gnss2', 'gnss3','gnss-gfz','ultra', 'rapid','nav-esa', 'nav-sopac','nav-cddis']

#   assign to normal variables
    pCtr = orbit

    if len(str(year)) != 4:
        print('Year must have four characters: ', year)
        sys.exit()
    month, day, doy, cyyyy, cyy, cdoy = g.ymd2ch(year,month,day)

    if doy_end == None:
        doy_end = doy 

    if pCtr not in orbit_list:
        print('You picked an orbit type - ', pCtr, ' - that I do not recognize')
        print(orbit_list)
        sys.exit()

    # if generic names used, we direct people to these orbit types
    if pCtr == 'gps':
        pCtr = 'nav'

    # send to CDDIS to get final GFZ orbits
    if pCtr == 'gnss':
        pCtr = 'gbm'

    if pCtr == 'gps+glo':
        pCtr = 'jax'

    # using gfz multi-gnss for rapid
    if pCtr == 'rapid':
        pCtr = 'gfr'

    d1= int(doy); d2 = int(doy_end) + 1
    for d in range(d1, d2):
        s1 = time.time()

        year,month,day= g.ydoy2ymd(year,d)
        print('Looking for ', year, '/', d, ' mm/dd', month, day)
        if (pCtr == 'nav'):
            navname, navdir, foundit = g.getnavfile(year, month, day)
            if foundit:
                print('\n SUCCESS:', navdir+'/'+navname)
        elif (pCtr == 'nav-esa'):
            navname, navdir, foundit = g.getnavfile_archive(year, month, day,'esa')
            if foundit:
                print('\n SUCCESS:', navdir+'/'+navname)
        elif (pCtr == 'nav-cddis'):
            navname, navdir, foundit = g.getnavfile_archive(year, month, day,'cddis')
            if foundit:
                print('\n SUCCESS:', navdir+'/'+navname)
        elif (pCtr == 'nav-sopac'):
            navname, navdir, foundit = g.getnavfile_archive(year, month, day,'sopac')
            if foundit:
                print('\n SUCCESS:', navdir+'/'+navname)
        else:
            if (pCtr == 'igs') or (pCtr == 'igr'):
                filename, fdir, foundit = g.getsp3file_flex(year, month, day, pCtr)
            else:
                if pCtr == 'esa':
                # this is ugly - but hopefully will work for now.
                    filename, fdir, foundit = g.getsp3file_flex(year, month, day, pCtr)
                elif pCtr == 'gfr':
                # rapid GFZ is available again ...
                    filename, fdir, foundit = g.rapid_gfz_orbits(year, month, day)
                elif pCtr == 'ultra':
                    hour = 0 # for now only download hour 0 for ultra products
                    filename, fdir, foundit = g.ultra_gfz_orbits(year, month, day, hour)
                elif (pCtr == 'gnss3') or (pCtr == 'gnss-gfz'):
                # use GFZ archive instead of CDDIS
                    filename, fdir, foundit = g.gbm_orbits_direct(year, month, day)
                elif pCtr == 'gnss2':
                # use IGN instead of CDDIS
                    print('To my knowledge, this option no longer works')
                    filename, fdir, foundit = g.avoid_cddis(year, month, day)
                else:
                    filename, fdir, foundit = g.getsp3file_mgex(year, month, day, pCtr)
            if foundit:
                print('SUCCESS:', fdir+'/'+filename)
            else:
                print(filename, ' not found')
        s2 = time.time()
        print('That download took ', np.round(s2-s1,2), ' seconds')


def main():
    args = parse_arguments()
    download_orbits(**args)


if __name__ == "__main__":
    main()
