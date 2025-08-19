#!/usr/bin/env python3

"""
VWC Hourly Rolling Command Line Interface

Generates hourly rolling VWC measurements by processing all possible bin offsets
and combining them into a chronologically ordered dataset.
"""

from gnssrefl.vwc_cl import main_hourly

def main():
    main_hourly()

if __name__ == "__main__":
    main()