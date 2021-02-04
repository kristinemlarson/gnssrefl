# -*- coding: utf-8 -*-
"""
downloads RINEX files
kristine larson
2020sep03 - modified environment variable requirement
"""
import argparse
import gnssrefl.gps as g
import os
import sys


def main():
    """
    command line interface to install non-python executables, specifically
    CRX2RNX, gpsSNR.e, and gnssSNR.e  
    I will add gfzrnx when I have a chance.

    author: kristine larson
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("os", help="operating system (linux or macos)", type=str)
# optional arguments

    args = parser.parse_args()

    os = args.os
    exedir = os.environ['EXE']
    print(exedir)

    if os == 'linux':
        print('linux')

    else:
        print('macos')


if __name__ == "__main__":
    main()
