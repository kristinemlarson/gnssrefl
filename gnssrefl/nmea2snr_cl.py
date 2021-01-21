# -*- coding: utf-8 -*-
"""
translates NMEA files
kristine larson
"""
import argparse
import gnssrefl.gps as g
import os
import sys
import gnssrefl.nmea2snr as n

def main():
    """
    command line interface for download_rinex
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="inputfile name", type=str)
    parser.add_argument("outputfile", help="outputfile name", type=str)

# optional arguments
    args = parser.parse_args()

#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

    inputfile = args.inputfile
    outputfile = args.outputfile
    n.nmea_snr(inputfile,outputfile)

if __name__ == "__main__":
    main()
