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
    parser.add_argument("month", help="month", type=int)
    parser.add_argument("day", help="day", type=int)

    args = parser.parse_args()
    year = args.year
    month = args.month
    day = args.day

    doy,cdoy,cyyyy,cyy = g.ymd2doy(year, month, day )
    print(cdoy)


if __name__ == "__main__":
    main()
