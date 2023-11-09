# -*- coding: utf-8 -*-
import argparse
import gnssrefl.gps as g

# this requires python 3.8
#from importlib.metadata import version

def main():
    """
    converts year month day to day of year and prints it to the screen

    MJD is an optional output

    Parameters
    ----------
    year : int
        4 ch year

    month : int
        calendar month

    day : int
        calendar day

    mjd : str
        use T or True to get MJD printed to the screen

    Returns
    -------
    doy : str 
        three character day of the year
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("year", help="year ", type=int)
    parser.add_argument("month", help="month", type=int)
    parser.add_argument("day", help="day", type=int)
    # this is not our normal way to input booleans but I am busy ...!
    parser.add_argument("-mjd", help="Print MJD to the screen. Default is F", type=str,default=None)

    args = parser.parse_args()
    year = args.year
    month = args.month
    day = args.day

    doy,cdoy,cyyyy,cyy = g.ymd2doy(year, month, day )
    print(cdoy)
    if args.mjd is not None:
        if (args.mjd == 'T') or (args.mjd == 'True'):
            mjd = g.getMJD(year,month,day,0)
            print('MJD', mjd)

if __name__ == "__main__":
    main()
