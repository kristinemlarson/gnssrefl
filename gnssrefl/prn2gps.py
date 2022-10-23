# -*- coding: utf-8 -*-
"""
author: kristine larson
prn to gps conversion script
gps number also known as SVN

some of these functions are no longer called.


"""
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
    try to download a file from JPL ... 
    """
    url='https://sideshow.jpl.nasa.gov/pub/gipsy_products/gipsy_params/PRN_GPS.gz'
    file_name='PRN_GPS.gz'
    print('Downloading the file from JPL')
  
    try:
        urllib.request.urlretrieve(url, file_name)
        subprocess.call(['gunzip',file_name])
    except:
        print('something in the download did not work.')

    return


def write_jpl_pickle_file(pname,tv):
    """
    write out PRN_GPS info
    """
    f = open(pname, 'wb')
    pickle.dump(tv, f)
    f.close()


def read_jpl_pickle_file(pname):
    """
    read in PRN_GPS info
    """
    tv=[]
    if os.path.isfile(pname):
        print('read existing pickle file')
        f = open(pname, 'rb')
        tv = pickle.load(f)
        f.close()
        print(tv)

    return tv


def read_jpl_file(fname):
    """
    send filename with prn gps conversion info
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


    parser = argparse.ArgumentParser()
    parser.add_argument("date", help="2012-12-05", type=str)
    parser.add_argument("-overwrite", help="set to T to download the existing PRN_GPS file", type=str)
    args = parser.parse_args()
    cdate = args.date
    seekTime =  g.cdate2nums(cdate)
    found = False
    fout = 'PRN_GPS'
    xdir = os.environ['REFL_CODE']
    if args.overwrite == 'T':
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

    #time1 = time.time()
    #picklename = 'PRN_GPS.pickle'
    #x = read_jpl_pickle_file(picklename)
    #time2 = time.time()
    #print(time2-time1, 'reading pickle')

    #time1 = time.time()
    x = read_jpl_file(fout)

    #x returns date1, date2, GPS, and PRN
    #time2 = time.time()
    #print(time2-time1, 'reading txt')

    #N,nc = x.shape
    # check all 32 PRN numbers
    for rprn in range(1,33):
        xxx = x[ (rprn == x[:,3] ) & (seekTime >= x[:,0]) & (seekTime <= x[:,1] ), 2 ] 
        gps_name = xxx.astype(int)
        if gps_name > 0:
            print("%2.0f  %2.0f " % (rprn, gps_name[0]) )
            #print(rprn,gps_name[0])



if __name__ == "__main__":
    main()

    #for rprn in range(1,33):
    #    for i in range(0,N):
    #        t1 = x[i,0]
    #        t2 = x[i,1]
    #        prn = x[i,3]
    #        gps = x[i,2]
    #        if (prn == rprn) and ((seekTime >= t1) and (seekTime < t2)):
    #            #print(prn,gps)
    #            break
