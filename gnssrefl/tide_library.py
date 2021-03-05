# preliminary tide data. 
# used primarily by prelim_tides.py
# kristine larson february 2021
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

def output_names(txtdir, txtfile,csvfile,jsonfile):
    """
    input: txtdir is the directory where the results should be written out
    txtfile, csvfile, and jsonfile 
    are the command line input values 
    if they are not set (i.e. they are None), that means you do not want it.
    """
    writetxt = True
    if txtfile == None:
        writetxt = False
    writecsv = True
    if csvfile == None:
        writecsv = False

    writejson = True
    if writejson == None:
        writejson = False

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

    print('outputfile ', outfile)
    return writetxt,writecsv,writejson,outfile

def write_subdaily(outfile,station,ntv,writecsv,writetxt):
    """
    input: output filename
    station - 4 character station name
    nvt is the variable with the LSP results
    writecsv and writetxt are booleans to tell you whether you 
    want csv output format or plain txt format (with spaces between colunmns)
    """
    N= len(ntv)
    # this is true so I don't have to move the indents
    if True:
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


def readin_and_plot(station, year,d1,d2,plt2screen):
    """
    station - 4 character name
    year -  
    d1 and d2 are days of year if you want to look at a smaller dataset
    plt2screen is a boolean whether you want the plot displayed to the screen
    """
    print('read in the data and plot it',d1,d2)
    xdir = os.environ['REFL_CODE']

    # output will go to REFL_CODE/Files
    txtdir = xdir + '/Files'
    if not os.path.exists(txtdir):
        os.makedirs(txtdir)

    # where the LSP results are kept
    direc = xdir + '/' + str(year) + '/results/' + station  + '/'
    tv = np.empty(shape=[0, 17])
    if os.path.isdir(direc):
        all_files = os.listdir(direc)
        print('Number of files in ', year, len(all_files))
        for f in all_files:
            fname = direc + f
            a = np.loadtxt(fname,comments='%')
            tv = np.append(tv, a,axis=0)

    print('Number of rows and columns ', tv.shape)
    t=tv[:,0] + (tv[:,1] + tv[:,4]/24)/365.25
    rh = tv[:,2]

    # sort the data
    ii = np.argsort(t)
    t = t[ii] ; rh = rh[ii]
    # store it all in a new variable
    tv = tv[ii,:]
    # and restrict by doy - mostly to make testing go faster
    ii = (tv[:,1] >= d1) & (tv[:,1] <= d2)
    tv = tv[ii,:]

    #
    if plt2screen:
        Plt.figure()
        Plt.plot( tv[:,0] + (tv[:,1] + tv[:,4]/24)/365.25, tv[:,2], '.')
        Plt.ylabel('Reflector Height (m)')
        Plt.title('GNSS station: ' + station)
        Plt.gca().invert_yaxis()
        Plt.grid()
        Plt.show()
    # always make a png file
#    plotname = txtdir + '/' + station + '_subdaily_RH.png'
#    Plt.savefig(plotname)
#    print('png file saved as: ', plotname)
    
    return tv


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
def splines_for_dummies(x,y,perday,plt):
    """
    inputs for now are fractional years (x) and RH (y)
    and number of values per day
    plt is a boolean for plots to come to the screen
        
    this is not an attempt to model water varaiations
    Our goal here is to remove a first model for RH dot impacts.  
    There are other ways to do this - and we will be adding more
    of them as time allows
    For a full tidal analysis you should estimate tidal coefficients

    Returns xx and spline(xx) in the same units as x and y
    """
    # sort the data by time
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
#    Plt.figure()
    t, c, k = interpolate.splrep(x, y, s=0, k=3,t=knots,task=-1)
    # user specifies how many values per day you want to provide
    N = int(Ndays*perday)
    xx = np.linspace(x.min(), x.max(), N)
    spline = interpolate.BSpline(t, c, k, extrapolate=False)
    # equal spacing in both x and y
    spl_x = xx; spl_y = spline(xx)

    resid = y-spline(x)
    ii = np.absolute(resid) > 0.5; 
    jj = np.absolute(resid) < 0.5; 

    if plt:

        Plt.figure()
        Plt.plot(x, y, 'bo', label='Original points',markersize=3)
        obstimes = fract_to_obstimes(spl_x)
        Plt.plot(spl_x, spl_y, 'r', label='Kristine spline')

        Plt.figure()
        Plt.plot(x, resid, 'bo', x[ii], resid[ii],'ro', markersize=3)

        # with large outliers removed?
        #Plt.figure()
        #xx=x[jj]
        #yy= y[jj]
        #splx,sply = in_out(xx,yy)
        #Plt.plot(xx,yy, 'o', markersize=3)
        #Plt.plot(splx,sply,'r-')

        #Plt.figure()
        #Plt.plot(xx, yy-sply, 'ro', markersize=3)

        Plt.show()

    return spl_x, spl_y

def in_out(x,y):
    """
    inputs are numpy arrays of time (in years) and reflector heights (m)
    outputs are the spline fit
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


def writejson(ntv,station, outfile):
    """
    subdaily RH values written out in json format
    inputs: ntv is the variable with concatenated results
    outfile is output file name
    """
    print('you picked the json output')
    # dictionary
    #o = {}
    N= len(ntv)

    # year is in first column
    year  =  ntv[:,0].tolist()
    year =[str(int(year[i])) for i in range(N)];

    # day of year
    doy =  ntv[:,1].tolist()
    doy=[str(int(doy[i])) for i in range(N)];

    # UTC hour
    UTChour = ntv[:,4].tolist()
    UTChour = [str(UTChour[i]) for i in range(N)];

    # converted to ???
    timestamp = [quickTr(ntv[i,0], ntv[i,1], ntv[i,4]) for i in range(N)]

    # reflector height (meters)
    rh = ntv[:,2].tolist()
    rh=[str(rh[i]) for i in range(N)];

    # satellite number
    sat  = ntv[:,3].tolist()
    sat =[int(sat[i]) for i in range(N)];

    # frequency
    freq  = ntv[:,10].tolist()
    freq =[int(freq[i]) for i in range(N)];

    # amplitude of main periodogram (LSP)
    ampl  = ntv[:,6].tolist()
    ampl =[str(ampl[i]) for i in range(N)];

    # azimuth in degrees
    azim  = ntv[:,5].tolist()
    azim =[str(azim[i]) for i in range(N)];

    # edotF in units ??
    edotf  = ntv[:,12].tolist()
    edotf =[str(edotf[i]) for i in range(N)];

    # modified julian day
    mjd = ntv[:,15].tolist()
    mjd=[str(mjd[i]) for i in range(N)];

    #column_names = ['timestamp','rh','sat','freq','ampl','azim','edotf','mjd']
    # now attempt to zip them
    l = zip(timestamp,rh,sat,freq,ampl,azim,edotf,mjd)
    dzip = [dict(zip(column_names, next(l))) for i in range(N)]
    # make a dictionary with metadata and data
    o={}
    # not setting lat and lon for now
    lat = "0"; lon = "0";
    firstline = {'name': station, 'latitude': lat, 'longitude': lon}
    o['metadata'] = firstline
    o['data'] = dzip
    outf = outfile
    with open(outf,'w+') as outf:
        json.dump(o,outf,indent=4)

    return True

def splines_for_dummies2(tvd,azim,perday,plt):
    """
    
    inputs for now are fractional days (origx) and RH (origy)
    and number of values per day you want in the smoothed outputs

    plt is a boolean for plots to come to the screen
    note: x was in units of years before

    Returns xx and spline(xx) in the same units as origx and origy
    """
    # sort the data by time
    t = tvd[:,1] + tvd[:,4]/24
    ii = np.argsort(t).T
    tvd = tvd[ii,:]

    t= tvd[:,1] + tvd[:,4]/24; 
    h = tvd[:,2]

    fillgap = 2/24
    gap = 4/24 # up to four hour gap allowed

    xnew =[] ; ynew =[]
    for i in range(1,len(t)):
    d= t[i]-t[i-1]
    if (d > gap):
        print(t[i], t[i-1])
        #print(h[i], h[i-1])
        print('found a gap in hours',d*24)
        x0 = t[i-1:i+1]
        h0 = h[i-1:i+1]
        f = scipy.interpolate.interp1d(x0,h0)
        xnew = np.arange(t[i-1]+fillgap, t[i], fillgap)
        ynew = f(xnew)
        print('new t values', xnew)
        print('new h values', ynew)

# append the interpolated values so the splines don't get unhappy
if (len(xnew) > 0):
    xnew = np.append(t,xnew)
    ynew = np.append(h,ynew)
else:
    xnew = t
    ynew = h

    # now make a x and y array that fills gaps - just makes things easier
    # to calculate RH dot.  it IS NOT because we think interpolation is 
    # acceptable

    knots_per_day = 12
    Ndays = x.max()-x.min()
    numKnots = int(knots_per_day*(Ndays))
    print('xmin, xmax',x.min(), x.max(), 'knots', numKnots,'number of days ', Ndays )
    # need the first and last knot to be inside the time series
    x1 = x.min()+0.1
    x2 = x.max()-0.1
    knots =np.linspace(x1,x2,num=numKnots)
#    Plt.figure()
    t, c, k = interpolate.splrep(x, y, s=0, k=3,t=knots,task=-1)
    # user specifies how many values per day you want to provide
    N = int(Ndays*perday)
    # evenly spaced data - units of days
    xx = np.linspace(x.min(), x.max(), N)
    spline = interpolate.BSpline(t, c, k, extrapolate=False)
    # equal spacing in both x and y
    spl_x = xx; spl_y = spline(xx)
    # this is the residual for each measurement defined in x,y
    # they are not time sorted however
    resid = origy-spline(origx)
    ii = np.absolute(resid) > 0.5;
    print(azim[ii])
    print(resid[ii])
    # "good points"
    jj = np.absolute(resid) < 0.5;
    if plt:
        Plt.figure()
        Plt.subplot(211)
        Plt.plot(x, y, 'bo', label='Original points',markersize=3)
        obstimes = fract_to_obstimes(spl_x)
        Plt.plot(spl_x, spl_y, 'r', label='Kristine spline')

        Plt.subplot(212)
        Plt.plot(origx[jj],origy[jj],'b.',origx[ii],origy[ii],'ro')


        Plt.show()

    return spl_x, spl_y
        # this worked - but didn't have names, so not useful
        #o['station'] = station
        #o['data'] =  ntv[:,[0,1,2,4,15,3]].tolist()
        # give my numpy variables names
        # to make a string
        # x=datetime.datetime(2018,9,15)
        # print(x.strftime("%b %d %Y %H:%M:%S"))
