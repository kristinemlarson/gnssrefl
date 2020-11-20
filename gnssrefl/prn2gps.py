# -*- coding: utf-8 -*-
"""
author: kristine larson
prn 2 gps conversion script
"""
import argparse
import numpy as np

import gnssrefl.gps as g

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("prn", help="PRN number", type=int)
    parser.add_argument("rdate", help="2012-12-05", type=str)
    args = parser.parse_args()
    rprn = args.prn
    cdate = args.rdate
    seekTime =  g.cdate2nums(cdate)
    print(rprn, cdate,seekTime)

    fname = 'PRN_GPS'
    x=np.loadtxt(fname, usecols=(0,1,2,3), skiprows=1,dtype='str')
    N,nc = x.shape
    col1 =   x[:,0]
    col2 =   x[:,1]

    for i in range(0,N):
        t1 = g.cdate2nums(col1[i])
        t2 = g.cdate2nums(col2[i])
        prn = int(x[i,3])
        gps = int(x[i,2])
        if (prn == rprn):
        if (seekTime >= t1) & (seekTime < t2):
            print(seekTime, t1,t2,prn,gps)

if __name__ == "__main__":
    main()
