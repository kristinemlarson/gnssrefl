# -*- coding: utf-8 -*-
"""
installs non-python executables
"""
import argparse
import wget
import os
import subprocess
import sys


def main():
    """
    command line interface to install non-python executables, specifically
    CRX2RNX, gpsSNR.e, and gnssSNR.e  
    I will add gfzrnx when I have a chance.
    https://stackoverflow.com/questions/12791997/how-do-you-do-a-simple-chmod-x-from-within-python
    author: kristine larson
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("opsys", help="operating system (linux or macos)", type=str)
# optional arguments

    args = parser.parse_args()

    opsys = args.opsys
    exedir = os.environ['EXE']
    print('executable environment area:', exedir)

    # download executable and mv to EXE area
    if (opsys == 'linux'):
        savename = 'CRX2RNX'
        url = 'https://github.com/kristinemlarson/gnssrefl/blob/master/static/CRX2RNX.linux64.e'
        wget.download(url,savename)
        os.chmod('CRX2RNX',0o111)
        subprocess.call('mv', savename, exedir)
        savename = 'gpsSNR.e'
        url = 'https://github.com/kristinemlarson/gnssrefl/blob/master/static/gpsSNR.linux64.e'
        wget.download(url,savename)
        os.chmod(savename,0o111)
        subprocess.call('mv', savename, exedir)

    elif (opsys == 'macos'):
        savename = 'CRX2RNX'
        url = 'https://github.com/kristinemlarson/gnssrefl/blob/master/static/CRX2RNX.macos.e'
        print(url,savename,exedir)
        wget.download(url,savename)
        os.chmod(savename,0o111)
        subprocess.call('mv', savename, exedir)

        savename = 'gpsSNR.e'
        url = 'https://github.com/kristinemlarson/gnssrefl/blob/master/static/gpsSNR.macos.e'
        print(url,savename,exedir)
        wget.download(url,savename)
        os.chmod(savename,0o111)
        subprocess.call('mv', savename, exedir)

    else:
        print('do not recognize your input. Exiting.')
        sys.exit()


if __name__ == "__main__":
    main()
