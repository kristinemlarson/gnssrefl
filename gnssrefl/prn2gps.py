# -*- coding: utf-8 -*-

import argparse
import numpy as np
import time
import pickle
import urllib
import os
import sys
import subprocess
import urllib

import gnssrefl.gps as g

def download_prn_gps():
    """
    downloads PRN to GPS name conversion file from JPL

    """
    url='https://sideshow.jpl.nasa.gov/pub/gipsy_products/gipsy_params/PRN_GPS.gz'
    file_name='PRN_GPS.gz'
    print('# Downloading the file from JPL')
  
    try:
        urllib.request.urlretrieve(url, file_name)
        subprocess.call(['gunzip',file_name])
    except:
        print('something in the download did not work.')

    return

def read_jpl_file(fname):
    """
    Parameters
    ----------
    fname : str
        filename with prn gps conversion info

    Returns
    -------
    tv : list
        start date (frac year), end date, GPS#, PRN #

    """
    tv = [] # in case there is some problem
    #fname = 'PRN_GPS'
    if os.path.isfile(fname):
        x=np.loadtxt(fname, usecols=(0,1,2,3), skiprows=1,dtype='str')
        N,nc = x.shape
    # date1, date2, gps, prn will go in the 4 columns
        tv = np.empty(shape=[0,4])
        for i in range(0,N):
            t1 = g.cdate2nums(x[i,0]) # fractional date
            t2 = g.cdate2nums(x[i,1])
            prn = int(x[i,3])
            gps = int(x[i,2])
        # only save if PRN < 33
            if (prn < 33) :
                newl = [t1, t2, gps, prn]
                tv = np.append(tv, [newl], axis=0)
    else:
        print('could not find the PRN to GPS conversion file ', fname)
        sys.exit()
    #pname = 'PRN_GPS.pickle'
    #write_jpl_pickle_file(pname,tv)
    return tv


def main():
    """
    Displays the PRN and SVN numbers for the GPS
    constellation on a given date.

    Parameters
    ----------
    date : str
        example 2012-01-01
    overwrite : bool, optional
        whether you want to download new file from JPL

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("date", help="2012-12-05", type=str)
    parser.add_argument("-overwrite", help="set to T or True to download new PRN_GPS file", type=str)
    args = parser.parse_args()
    cdate = args.date
    seekTime =  g.cdate2nums(cdate)
    found = False
    fout = 'PRN_GPS'
    xdir = os.environ['REFL_CODE']
    if (args.overwrite == 'T') or (args.overwrite == 'True'):
        print('# Will remove existing file, if it exists locally, and will download a new one')
        subprocess.call(['rm','-f','PRN_GPS'])
        download_prn_gps()


    print('# Looking for the PRN_GPS file.')
    if os.path.isfile('PRN_GPS'):
         print('# Found locally: ', fout)
         found = True
    if not found:
         print('# Look in the Files directory')
         fout = xdir + '/Files/PRN_GPS'
         if os.path.isfile(fout):
             print('Found: ', fout)
             found = True
    if not found:
        print('# Try to download a file from JPL')
        download_prn_gps()
        if os.path.isfile('PRN_GPS'):
            found = True
            fout = 'PRN_GPS' # though should probably move it
            print('# Downloaded and stored locally: ',fout)

    if not found:
        print('No input file, no output')
        sys.exit()


    x = read_jpl_file(fout)


    #N,nc = x.shape
    # check all 32 PRN numbers

    xx = 0
    for rprn in range(1,33):
        xxx = x[ (rprn == x[:,3] ) & (seekTime >= x[:,0]) & (seekTime <= x[:,1] ), 2 ] 
        gps_name = xxx.astype(int)
        if gps_name > 0:
            xx = xx + 1
            print("%2.0f  %2.0f " % (rprn, gps_name[0]) )
    print('\n There were ', xx, ' valid GPS satellites on ', cdate)


if __name__ == "__main__":
    main()

