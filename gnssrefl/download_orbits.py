# -*- coding: utf-8 -*-
"""
downloads Orbit files
author: kristine larson
2020sep03 - modified environment variable requirement
"""
import argparse
import gnssrefl.gps as g
import sys


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("orbit", help="orbit name (gps,gnss,gps+glo, or specific e.g. jax) ", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("month", help="month (or day of year)", type=int)
    parser.add_argument("day", help="day (zero if you use day of year earlier)", type=int)
    parser.add_argument("-doy_end", help="doy end for multi-day download ", type=int)

    args = parser.parse_args().__dict__

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def download_orbits(orbit: str, year: int, month: int, day: int):
    """
        command line interface for download_orbits
        Parameters:
        ___________
        orbit : string
        
            value options:

                gps (default) : uses GPS broadcast orbit

                gps+glo : will use JAXA orbits which have GPS and Glonass (usually available in 48 hours)

                gnss : will use GFZ orbits, which is multi-GNSS (available in 3-4 days)

                nav : GPS broadcast, adequate for reflectometry.

                igs : IGS precise, GPS only

                igr : IGS rapid, GPS only

                jax : JAXA, GPS + Glonass, within a few days, missing block III GPS satellites

                gbm : GFZ Potsdam, multi-GNSS, not rapid

                grg : French group, GPS, Galileo and Glonass, not rapid

                esa : ESA, multi-GNSS

                gfr : GFZ rapid, GPS, Galileo and Glonass, since May 17 2021

                wum : (disabled) Wuhan, multi-GNSS, not rapid

                gnss2 : multi-GNSS, but uses IGN instead of CDDIS

                brdc : rinex 3 broadcast file from CDDIS

                ultra : ultra orbits from GFZ

                rapid : rapid orbits from GFZ

         year : integer
            year

         month : integer
            month

         day : integer
            day

         doy_end : integer
            day

    """

#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

    orbit_list = ['igs', 'igr', 'jax', 'grg', 'wum', 'gbm', 'nav', 'gps', 'gps+glo', 'gnss', 'gfr', 'esa', 'gnss2', 'brdc', 'ultra', 'rapid']


#   assign to normal variables
    pCtr = orbit

    if len(str(year)) != 4:
        print('Year must have four characters: ', year)
        sys.exit()

    if day == 0:
        # then you are using day of year as input
        doy = month
        year, month, day = g.ydoy2ymd(year, doy)
        doy, cdoy, cyyyy, cyy = g.ymd2doy(year, month, day)
    else:
        doy, cdoy, cyyyy, cyy = g.ymd2doy(year, month, day)

    if pCtr not in orbit_list:
        print('You picked an orbit type - ', pCtr, ' - that I do not recognize')
        print(orbit_list)
        sys.exit()

    # if generic names used, we direct people to these orbit types
    if pCtr == 'gps':
        pCtr = 'nav'

    # this is picked up from CDDIS
    if pCtr == 'gnss':
        pCtr = 'gbm'

    if pCtr == 'gps+glo':
        pCtr = 'jax'

    # using gfz multi-gnss for rapid
    if pCtr == 'rapid':
        pCtr = 'gfr'

    if pCtr == 'nav':
        navname, navdir, foundit = g.getnavfile(year, month, day)
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
            # also at GFZ
            elif pCtr == 'ultra':
                hour = 0 # for now
                filename, fdir, foundit = g.ultra_gfz_orbits(year, month, day, hour)
            elif pCtr == 'gnss2':
                # use IGN instead of CDDIS
                filename, fdir, foundit = g.avoid_cddis(year, month, day)
            elif pCtr == 'brdc':
                # https://cddis.nasa.gov/archive/gnss/data/daily/2021/brdc/
                # test code to get rinex 3 broadcast file
                # will not store it in ORBITS because it is not used explicitly
                # this is not operational as yet
                filename, fdir, foundit = g.rinex3_nav(year, month, day)
            else:
                filename, fdir, foundit = g.getsp3file_mgex(year, month, day, pCtr)
        if foundit:
            print('SUCCESS:', fdir+'/'+filename)
        else:
            print(filename, ' not found')


def main():
    args = parse_arguments()
    download_orbits(**args)


if __name__ == "__main__":
    main()
