# -*- coding: utf-8 -*-

import argparse
import gnssrefl.gps as g

def main():
    """
    Calculates GPS week information

    Parameters
    ----------
    year : integer
        full year

    month : integer
        calendar month

    day : integer
        day of the month

    Returns
    -------
    wk : int
        GPS week

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("month", help="month", type=int)
    parser.add_argument("day", help="day", type=int)

    args = parser.parse_args()
    year = args.year
    month = args.month
    day = args.day

    wk,swk = g.kgpsweek(year, month, day, 0,0,0)
    print('WEEK:', wk, ' DAY:', int(swk/86400))


if __name__ == "__main__":
    main()
