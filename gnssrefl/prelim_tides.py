# preliminary tide data. 
import argparse
import datetime
import json
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

def quickTr(year, doy,frachours):
    """
    inputs from the lomb scargle code (year, doy) and UTC hour (fractional)
    returns character string for json 
    """
    year = int(year); doy = int(doy); frachours = float(frachours)
    # convert doy to get month and day
    d = datetime.datetime(year, 1, 1) + datetime.timedelta(days=(doy-1))
    month = int(d.month)
    day = int(d.day)

    hours = int(np.floor(frachours))
    leftover = 60*(frachours - hours)
    minutes = int(np.floor(leftover))
    leftover_hours  = frachours - (hours + minutes/60)
    seconds = int(leftover_hours*3600)
    #print(frachours, hours,minutes,leftover_seconds)

    jd = datetime.datetime(year,month, day,hours,minutes,seconds)
    datestring = jd.strftime("%Y-%m-%d %H:%M:%S")


    return datestring


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
def splines_for_dummies(x,y,plt):
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
    if plt:

        Plt.figure()
        Plt.plot(x, y, 'bo', label='Original points',markersize=3)
# equal spacing
        spl_x = xx; spl_y = spline(xx)
        obstimes = fract_to_obstimes(spl_x)
        Plt.plot(spl_x, spl_y, 'r', label='Kristine spline')

        Plt.figure()
        resid = y-spline(x)
        ii = np.absolute(resid) > 0.5; 
        jj = np.absolute(resid) < 0.5; 
        Plt.plot(x, resid, 'bo', x[ii], resid[ii],'ro', markersize=3)

        # with residuals removed?
        Plt.figure()
        xx=x[jj]
        yy= y[jj]
        splx,sply = in_out(xx,yy)
        Plt.plot(xx,yy, 'o', markersize=3)
        Plt.plot(splx,sply,'r-')

        Plt.figure()
        Plt.plot(xx, yy-sply, 'ro', markersize=3)

        Plt.show()

    return True

def in_out(x,y):
    """
    """
    knots_per_day = 12
    Ndays = 365.25*(x.max()-x.min())
    numKnots = int(knots_per_day*(Ndays))
    #print('xmin, xmax',x.min(), x.max(), 'knots', numKnots,Ndays )
    x1 = x.min()+0.1/365.25
    x2 = x.max()-0.1/365.25
    knots =np.linspace(x1,x2,num=numKnots)
    t, c, k = interpolate.splrep(x, y, s=0, k=3,t=knots,task=-1)
#   calculate water level hourly for now
    N = int(Ndays*24 )
    xx = np.linspace(x.min(), x.max(), N)
    spline = interpolate.BSpline(t, c, k, extrapolate=False)

    return x,spline(x) 
    
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
    parser.add_argument("-jsonfile", default='None', type=str, help="output (json)")
    parser.add_argument("-plt", default='None', type=str, help="set to False to suppress plots")

    args = parser.parse_args()
#   these are required
    station = args.station

#   these are optional
    txtfile = args.txtfile
    csvfile = args.csvfile
    jsonfile = args.jsonfile


    writetxt = True  
    if txtfile == 'None':
        writetxt = False
    writecsv = True  
    if csvfile == 'None':
        writecsv = False
    writejson = True
    if jsonfile == 'None':
        writejson = False

    if args.year == 'None':
        year = 2020
    else:
        year=int(args.year)

    if args.plt == 'False':
        plt= False
    else:
        plt = True

# where the summary files will be written to
    txtdir = xdir + '/Files' 

    if not os.path.exists(txtdir):
        os.makedirs(txtdir)

    direc = xdir + '/' + str(year) + '/results/' + station  + '/'
    tv = np.empty(shape=[0, 17])
    if os.path.isdir(direc):
        all_files = os.listdir(direc)
        print('Number of files in ', year, len(all_files))
        for f in all_files:
            fname = direc + f
            a = np.loadtxt(fname,comments='%')
            tv = np.append(tv, a,axis=0)
            print(len(tv))

    print(tv.shape)
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

    splines_for_dummies(t,rh,plt)

    # apply time tags to a new variable
    N,M = np.shape(ntv)
    if writejson:
        outfile = txtdir + '/' + jsonfile
    if writecsv:
        outfile = txtdir + '/' + csvfile
    if writetxt:
        outfile = txtdir + '/' + txtfile
    if (writecsv) and (writetxt) :
        print('You cannot simultaneously write out a csvfile and a txtfile')
        print('Default to writing only a txtfile')
        writecsv = False

    if (writejson):
        print('you picked the json output')
        o = {}
        N= len(ntv)
        column_names = ['timestamp','rh','sat','freq','ampl','azim','edotf','mjd']

        # this worked - but didn't have names, so not useful
        #o['station'] = station
        #o['data'] =  ntv[:,[0,1,2,4,15,3]].tolist()
        # give my numpy variables names
        # to make a string
        # x=datetime.datetime(2018,9,15)
        # print(x.strftime("%b %d %Y %H:%M:%S"))
        year  =  ntv[:,0].tolist()
        year =[str(int(year[i])) for i in range(N)]; 

        doy =  ntv[:,1].tolist()
        doy=[str(int(doy[i])) for i in range(N)]; 

        UTChour = ntv[:,4].tolist()
        UTChour = [str(UTChour[i]) for i in range(N)]; 

        timestamp = [quickTr(ntv[i,0], ntv[i,1], ntv[i,4]) for i in range(N)]

        rh = ntv[:,2].tolist()
        rh=[str(rh[i]) for i in range(N)]; 

        sat  = ntv[:,3].tolist()
        sat =[int(sat[i]) for i in range(N)]; 

        freq  = ntv[:,10].tolist()
        freq =[int(freq[i]) for i in range(N)]; 

        ampl  = ntv[:,6].tolist()
        ampl =[str(ampl[i]) for i in range(N)]; 

        azim  = ntv[:,5].tolist()
        azim =[str(azim[i]) for i in range(N)]; 

        edotf  = ntv[:,12].tolist()
        edotf =[str(edotf[i]) for i in range(N)]; 

        mjd = ntv[:,15].tolist()
        mjd=[str(mjd[i]) for i in range(N)]; 

        # now attempt to zip them
        l = zip(timestamp,rh,sat,freq,ampl,azim,edotf,mjd)
        dzip = [dict(zip(column_names, next(l))) for i in range(N)]
        # make a dictionary with metadata and data
        o={}
        lat = "0"; lon = "0"; 
        firstline = {'name': station, 'latitude': lat, 'longitude': lon}
        o['metadata'] = firstline
        o['data'] = dzip

        outf = outfile
        print(outfile)
        with open(outf,'w+') as outf:
            json.dump(o,outf,indent=4)
        #close(outf)

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
