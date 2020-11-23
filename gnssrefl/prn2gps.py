# -*- coding: utf-8 -*-
"""
author: kristine larson
prn 2 gps conversion script
"""
import argparse
import numpy as np
import time
import pickle
import os
import sys

import gnssrefl.gps as g

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


def read_jpl_file():
    """
    """
    tv = [] # in case there is some problem
    fname = 'PRN_GPS'
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

#    fname = 'PRN_GPS'
#    x=np.loadtxt(fname, usecols=(0,1,2,3), skiprows=1,dtype='str')

    parser = argparse.ArgumentParser()
    parser.add_argument("date", help="2012-12-05", type=str)
    args = parser.parse_args()
    cdate = args.date
    seekTime =  g.cdate2nums(cdate)


    #time1 = time.time()
    #picklename = 'PRN_GPS.pickle'
    #x = read_jpl_pickle_file(picklename)
    #time2 = time.time()
    #print(time2-time1, 'reading pickle')

    #time1 = time.time()
    x = read_jpl_file()
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


    #for rprn in range(1,33):
    #    for i in range(0,N):
    #        t1 = x[i,0]
    #        t2 = x[i,1]
    #        prn = x[i,3]
    #        gps = x[i,2]
    #        if (prn == rprn) and ((seekTime >= t1) and (seekTime < t2)):
    #            #print(prn,gps)
    #            break

if __name__ == "__main__":
    main()
