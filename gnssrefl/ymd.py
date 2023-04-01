# -*- coding: utf-8 -*-
"""
converts ymd to doy
Updated: April 3, 2019
"""
import argparse
import gnssrefl.gps as g

def main():
    """
    converts year month day to day of year and prints it to the screen
    Also does MJD for fun.

    Parameters
    ----------
    year : int

    month : int

    day : int

    Returns
    -------
    doy : str 
        three character day of the year
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("year", help="year ", type=int)
    parser.add_argument("month", help="month", type=int)
    parser.add_argument("day", help="day", type=int)

    args = parser.parse_args()
    year = args.year
    month = args.month
    day = args.day

    doy,cdoy,cyyyy,cyy = g.ymd2doy(year, month, day )
    print(cdoy)
    mjd = g.getMJD(year,month,day,0)
    print('MJD', mjd)

if __name__ == "__main__":
    main()
