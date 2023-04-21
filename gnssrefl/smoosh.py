# -*- coding: utf-8 -*-
import argparse
import os
import subprocess
import sys

import gnssrefl.gps as g

def main():
    """
    Decimates and strips out SNR data

    Parameters
    ----------
    rinex : str
        filename
    dec : int
        decimation value in seconds
    snr : bool, optional
        whether you want only SNR observables

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("rinexfile", help="filename, rinex 2 only", type=str)
    parser.add_argument("dec", help="decimation value, seconds", type=int)
    parser.add_argument("-snr", help="whether you want SNR data stripped out", type=str,default=None)

    args = parser.parse_args()
    rinexfile = args.rinexfile
    dec = args.dec 
    gexe = g.gfz_version()
    snr = True
    rinexfile2 = rinexfile + '.tmp'

    if not os.path.exists(gexe):
        print('Required gfzrnx executable does not exist. Exiting.')
        sys.exit()


    if not os.path.isfile(rinexfile):
        print('Your RINEX input file does exist:', rinexfile)
        sys.exit()

    crate = str(dec)
    iall = 'GRE'
    sig = 'S1,S2C,S2,S5,S6,S7'
    subprocess.call([gexe,'-finp', rinexfile, '-fout', rinexfile2, '-vo','2','-ot', sig, '-smp', crate, '-satsys',iall,'-f'])
    # move new file to original name
    subprocess.call(['rm','-f', rinexfile])
    subprocess.call(['mv','-f', rinexfile2, rinexfile])

    #if os.path.isfile(rinex2):
    #    print('SUCCESS: new file created', rinex2)

if __name__ == "__main__":
    main()
