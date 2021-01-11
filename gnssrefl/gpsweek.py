# -*- coding: utf-8 -*-
"""
computers GPS week (and day of week) from y,m,d
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

    wk,swk = g.kgpsweek(year, month, day, 0,0,0)
    #doy,cdoy,cyyyy,cyy = g.ymd2doy(year, month, day )
    print('WEEK:', wk, ' DAY:', int(swk/86400))


if __name__ == "__main__":
    main()
