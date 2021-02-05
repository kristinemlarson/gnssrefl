# -*- coding: utf-8 -*-
"""
installs non-python executables
"""
import argparse
import wget
import os
import subprocess
import sys

def download_chmod_move(url,savename,exedir):
    """
    inputs are url, filename and executable directory
    it should chmod g+rwx and  move to exe area
    """
    wget.download(url,savename)
    os.chmod(savename,0o777)
    subprocess.call(['mv', '-f',savename, exedir])
    print('\n Executable stored:', savename)

def main():
    """
    command line interface to install non-python executables, specifically
    CRX2RNX, gpsSNR.e, and gnssSNR.e  
    I will add gfzrnx when I have a chance.
    https://stackoverflow.com/questions/12791997/how-do-you-do-a-simple-chmod-x-from-within-python
    author: kristine larson
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("opsys", help="operating system (linux64 or macos)", type=str)
# optional arguments

    args = parser.parse_args()

    opsys = args.opsys
    exedir = os.environ['EXE']
    print('Executable environment area:', exedir)


    # where the files are stored publicly
    sto = 'https://morefunwithgps.com/public_html/'

    if (opsys == 'linux64'):
        savename = 'CRX2RNX'
        url = sto + savename + '.' + opsys + '.e'
        download_chmod_move(url,savename,exedir)

        savename = 'gpsSNR.e'
        url = sto + 'gpsSNR.' + opsys + '.e'
        download_chmod_move(url,savename,exedir)

        savename = 'gnssSNR.e'
        url = sto + 'gnssSNR.' + opsys + '.e'
        download_chmod_move(url,savename,exedir)

        savename = 'gfzrnx'
        url = sto + 'gfzrnx.' + opsys + '.e'
        download_chmod_move(url,savename,exedir)

    elif (opsys == 'macos'):
        savename = 'CRX2RNX'
        url = sto + savename + '.' + opsys + '.e'
        download_chmod_move(url,savename,exedir)

        #savename = 'gpsSNR.e'
        #url = sto + 'gpsSNR.' + opsys + '.e'
        #download_chmod_move(url,savename,exedir)

        #savename = 'gnssSNR.e'
        #url = sto + 'gnssSNR.' + opsys + '.e'
        #download_chmod_move(url,savename,exedir)

        savename = 'gfzrnx'
        url = sto + 'gfzrnx.' + opsys + '.e'
        download_chmod_move(url,savename,exedir)
        print('Unfortunately there are no static executables for gpsSNR.e and gnssSNR.e')

    else:
        print('do not recognize your operating system input. Exiting.')
        sys.exit()


if __name__ == "__main__":
    main()
