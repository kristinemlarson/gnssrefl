# very simple code to pick up all the RH results and make a plot.
# only getting rid of the biggest outliers using a median filter
# Kristine Larson May 2019
import argparse
import numpy as np


# my code
import gnssrefl.gps as g
#

def cdate2nums(col1):
    """
    returns fractional year from ch date, e.g. 2012-02-15
    if time is blank, return 3000
    """
    year = int(col1[0:4])
    if year == 0:
        t=3000 # made up very big time!
    else:
        month = int(col1[5:7])
        day = int(col1[8:10])
        #print(col1, year, month, day)
        doy,cdoy,cyyyy,cyy = g.ymd2doy(year, month, day )
        t = year + doy/365.25

    return t

def main():
#   make surer environment variables are set 
    g.check_environ_variables()

# must input start and end year
    parser = argparse.ArgumentParser()
    parser.add_argument("prn", help="PRN number", type=int)
    parser.add_argument("rdate", help="2012-12-05", type=str)
    print(prn,rdate)
    args = parser.parse_args()
#   these are required
    rprn = args.prn
    cdate = args.rdate
    seekTime =  cdate2nums(cdate)

    fname = 'PRN_GPS'

    x=np.loadtxt(fname, usecols=(0,1,2,3), skiprows=1,dtype='str')
    N,nc = x.shape
    col1 =   x[:,0]
    col2 =   x[:,1]

    for i in range(0,N):
        t1 = cdate2nums(col1[i])
        t2 = cdate2nums(col2[i])
        prn = int(x[i,3])
        gps = int(x[i,2])
        if (prn == rprn):
        if (seekTime >= t1) & (seekTime < t2):
            print(seekTime, t1,t2,prn,gps)

if __name__ == "__main__":
    main()
