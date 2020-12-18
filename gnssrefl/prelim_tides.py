# preliminary tide data. 
import argparse
import datetime
import matplotlib.pyplot as Plt
import numpy as np
import os
import sys

from datetime import date

# my code
import gnssrefl.gps as g


import scipy.interpolate as interpolate
from scipy.interpolate import interp1d
import math

def fract_to_obstimes(spl_x):
    N=len(spl_x)
    obstimes = np.empty(shape=[0, 1])
    year = np.floor(spl_x)
    fdoy = 365.25*(spl_x - year)
    doy = np.floor(fdoy)
    fhours = 24*(fdoy - doy)
    hours = np.floor(fhours)
    leftover = 60*(fhours - hours)
    minutes = np.floor(leftover)
    for i in range(0,N):
        y = int(year[i]); d = int(doy[i])
        y, month, day, cyyyy,cdoy, YMD = g.ydoy2useful(y,d)
        h= int(hours[i])
        m = int(minutes[i])
        #print(y,month,day,h,m)
        obstimes = np.append(obstimes, datetime.datetime(year=y, month=month, day=day, hour=h, minute=m, second=0 ))

    return obstimes

#
def splines_for_dummies(x,y):
    """
    inputs for now are fractional years (x) and RH (y)
    """
    ii = np.argsort(x).T
    x = x[ii]
    y = y[ii]
    knots_per_day = 12
    Ndays = 365.25*(x.max()-x.min())
    numKnots = int(knots_per_day*(Ndays))
    print('xmin, xmax',x.min(), x.max(), 'knots', numKnots,Ndays )
    x1 = x.min()+0.1/365.25
    x2 = x.max()-0.1/365.25
    knots =np.linspace(x1,x2,num=numKnots)
    t, c, k = interpolate.splrep(x, y, s=0, k=3,t=knots,task=-1)
#   calculate water level hourly for now
    N = int(Ndays*24 )
    xx = np.linspace(x.min(), x.max(), N)
    spline = interpolate.BSpline(t, c, k, extrapolate=False)
    Plt.figure()
    Plt.plot(x, y, 'bo', label='Original points',markersize=3)

    Plt.figure()
    Plt.plot(x, y, 'bo', label='Original points',markersize=3)
# equal spacing
    spl_x = xx
    spl_y = spline(xx)
    obstimes = fract_to_obstimes(spl_x)
    Plt.plot(spl_x, spl_y, 'r', label='Kristine spline')

    Plt.figure()
    resid = y-spline(x)
    ii = np.absolute(resid) > 0.5; 
    Plt.plot(x, resid, 'bo', x[ii], resid[ii],'ro', markersize=3)
    Plt.show()

    return True


    
def write_out_header(fout,station):
    xxx = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    fout.write('% Results for {0:4s} calculated on {1:20s} \n'.format(  station, xxx ))
    fout.write('% gnssrefl, https://github.com/kristinemlarson \n')
    fout.write('% Phase Center corrections have NOT been applied \n')
    fout.write('% (1)  (2)  (3)   (4)    (5)      (6)    (7)    (8)      (9)  (10)   (11)(12)(13)(14)   (15)\n')
    fout.write('% year, doy, RH,  sat, UTCtime,  Azim,   Amp,  PkNoise, Freq, edotF, Mon,Day, Hr,Min,  MJD \n')


def main():
#   make surer environment variables are set 
    g.check_environ_variables()
    xdir = os.environ['REFL_CODE'] 

# must input start and end year
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
# optional inputs: filename to output daily RH results 
    parser.add_argument("-year", default='None', type=str, help="restrict to years beginning with")
    parser.add_argument("-txtfile", default='None', type=str, help="output (plain text)") 
    parser.add_argument("-csvfile", default='None', type=str, help="output (csv)")
    parser.add_argument("-plt", default='None', type=str, help="set to False to suppress plots")

    args = parser.parse_args()
#   these are required
    station = args.station

#   these are optional
    txtfile = args.txtfile
    csvfile = args.csvfile
    if args.plt == 'False':
        plt= False
    else:
        plt = True

    writetxt = True; writecsv = True
    if txtfile == 'None':
        writetxt = False
    if csvfile == 'None':
        writecsv = False

    if args.year == 'None':
        year = 2020
    else:
        year=int(args.year)


# where the summary files will be written to
    txtdir = xdir + '/Files' 

    if not os.path.exists(txtdir):
        os.makedirs(txtdir)

    direc = xdir + '/' + str(year) + '/results/' + station  + '/'
    tv = np.empty(shape=[0, 17])
    if os.path.isdir(direc):
        all_files = os.listdir(direc)
        #print('Number of files in ', year1, len(all_files))
        for f in all_files:
            fname = direc + f
            a = np.loadtxt(fname,comments='%')
            tv = np.append(tv, a,axis=0)

    #print(tv.shape)
    t=tv[:,0] + (tv[:,1] + tv[:,4]/24)/365.25
    rh = tv[:,2]

    # sort the data
    ii = np.argsort(t)
    t = t[ii] ; rh = rh[ii]
    # store it all in a new variable
    ntv = tv[ii,:]
    #
    Plt.figure()
    Plt.plot(t, rh,'.')
    Plt.ylabel('Reflector Height (m)')
    Plt.title('GNSS station: ' + station)
    Plt.gca().invert_yaxis()
    Plt.grid()
    # default is to show the plot
    #if plt:
        #Plt.show()
    # always make a png file
    plotname = txtdir + '/' + station + '_subdaily_RH.png'
    Plt.savefig(plotname)
    print('png file saved as: ', plotname)


    splines_for_dummies(t,rh)

    # apply time tags to a new variable
    N,M = np.shape(ntv)
    #txtfile = station + '_subdaily_rh.txt'
    #csvfile = station + '_subdaily_rh.csv'
    if writecsv:
        outfile = txtdir + '/' + csvfile
    if writetxt:
        outfile = txtdir + '/' + txtfile
    if (writecsv) and (writetxt):
        print('You cannot simultaneously write out a csvfile and a txtfile')
        print('Default to writing only a txtfile')
        writecsv = False

    if (writecsv) or (writetxt):
        print('Results are being written to : ', outfile)
        fout = open(outfile, 'w+')
        write_out_header(fout,station)
        for i in np.arange(0,N,1):
            year = int(ntv[i,0]); doy = int(ntv[i,1])
            year, month, day, cyyyy,cdoy, YMD = g.ydoy2useful(year,doy)
            rh = ntv[i,2]; UTCtime = ntv[i,4]; mjd = ntv[i,15]
            ctime = g.nicerTime(UTCtime); ctime2 = ctime[0:2] + ' ' + ctime[3:5]
            if writecsv:
                fout.write(" {0:4.0f},{1:3.0f},{2:7.3f},{3:3.0f},{4:7.3f},{5:8.2f},{6:7.2f},{7:5.2f},   {8:3.0f},{9:8.5f}, {10:2.0f}, {11:2.0f},{12:2s},{13:2s},{14:15.6f} \n".format(year, doy, rh,ntv[i,3],UTCtime,ntv[i,5],ntv[i,6],ntv[i,13],ntv[i,10],ntv[i,12],month,day,ctime[0:2],ctime[3:5] ,mjd ))
            else:
                fout.write(" {0:4.0f} {1:3.0f} {2:7.3f} {3:3.0f} {4:7.3f} {5:8.2f} {6:7.2f} {7:5.2f}    {8:3.0f} {9:8.5f}  {10:2.0f}  {11:2.0f} {12:5s} {13:15.6f} \n".format(year, doy, rh,ntv[i,3],UTCtime,ntv[i,5],ntv[i,6],ntv[i,13],ntv[i,10],ntv[i,12],month,day,ctime2,mjd ))
        fout.close()

if __name__ == "__main__":
    main()
