# -*- coding: utf-8 -*-
"""
converts ymd to doy
kristine larson
Updated: April 3, 2019
"""
import argparse
import gnssrefl.gps as g

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("year", help="year ", type=int)
    parser.add_argument("month", help="month (or day of year)", type=int)
    parser.add_argument("day", help="day (zero if you want day of year) ", type=int)

    args = parser.parse_args()
    year = args.year
    month = args.month
    day = args.day

    if (day == 0):
        y,m,d=g.ydoy2ymd(year, month) 
        print('month and day', m,d)
    else:
        doy,cdoy,cyyyy,cyy = g.ymd2doy(year, month, day )
        print(cdoy)


if __name__ == "__main__":
    main()
