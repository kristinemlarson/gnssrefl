# -*- coding: utf-8 -*-
import argparse
import os
import subprocess
import sys

import gnssrefl.gps as g

def main():
    """
    Decimates and strips out SNR data from a RINEX 2.11 file. 
    Only RINEX, no Hatanaka RINEX or gzipped files allowed. If you would like to add
    these features, please submit a PR.

    Examples
    --------

    smoosh p0410010.22o 5
        decimates a highrate rinex 2.11 file to 5 seconds

    smoosh p0410010.22o 5 -snr T
        also eliminates all observation types except for SNR

    Parameters
    ----------
    rinex : str
        rinex 2.11 filename
    dec : int
        decimation value in seconds
    snr : bool, optional
        whether you want only SNR observables
        helpful when you have too many observables in your file.

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


if __name__ == "__main__":
    main()
