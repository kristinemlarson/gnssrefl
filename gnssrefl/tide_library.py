# codes for subdaily/tide data. 
# used primarily by prelim_tides.py
# kristine larson february 2021
import argparse
import datetime
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

from datetime import date

# my code
import gnssrefl.gps as g


import scipy
import scipy.interpolate as interpolate
from scipy.interpolate import interp1d
import math

def print_badpoints(t):
    """
    input: station name and lomb scargle result array of "bad points"
    """
#  year, doy, RH,  sat, UTCtime,  Azim,   Amp,  PkNoise, Freq, edotF, Mon,Day, Hr,Min,  MJD
#   (0)  (1)  (2)  (3)   (4)    (5)      (6)    (7)    (8)      (9)  (10)   (11)(12)(13)(14)   (15)
    m,n = t.shape
    f = 'outliers.txt'
    print('outliers written to file: ', f) 
    fout = open(f, 'w+')
    for i in range(0,m):
         fout.write('doy {0:3.0f} sat {1:3.0f} azim {2:6.2f} fr {3:3.0f} \n'.format(t[i,1], t[i,3],t[i,5], t[i,8]) )
    fout.close()

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


def readin_and_plot(station, year,d1,d2,plt2screen,extension):
    """
    station - 4 character name
    year is year ;-)  
    d1 and d2 are days of year if you want to look at a smaller dataset
    plt2screen is a boolean whether you want the plot displayed to the screen
    author: kristine larson
    """
    print('read in the data and plot it between these days: ',d1,d2)
    xdir = os.environ['REFL_CODE']

    # output will go to REFL_CODE/Files
    txtdir = xdir + '/Files'
    if not os.path.exists(txtdir):
        os.makedirs(txtdir)

    # where the LSP results are kept
    direc = xdir + '/' + str(year) + '/results/' + station  + '/' + extension + '/'
    tv = np.empty(shape=[0, 17])
    if os.path.isdir(direc):
        all_files = os.listdir(direc)
        print(direc)
        #print('Number of files in ', year, len(all_files))
        for f in all_files:
            # only evaluate txt files
            if (len(f) ==  7) and (f[4:8] == 'txt'):
                day = int(f[0:3])
                if (day >= d1) & (day <= d2):
                    fname = direc + f
                    try:
                        a = np.loadtxt(fname,comments='%')
                        if len(a) > 0:
                            tv = np.append(tv, a,axis=0)
                    except:
                        print('some issue with ',fname)

    print('Number of rows and columns ', tv.shape)
    print(tv.shape)
    t=tv[:,0] + (tv[:,1] + tv[:,4]/24)/365.25
    rh = tv[:,2]

    # sort the data
    ii = np.argsort(t)
    t = t[ii] ; rh = rh[ii]
    # store it all in a new variable
    tv = tv[ii,:]
    # sill y - why read it if you are not going to use it
    # and restrict by doy - mostly to make testing go faster
    ii = (tv[:,1] >= d1) & (tv[:,1] <= d2)
    tv = tv[ii,:]

    #
    if plt2screen:
        plt.figure()
        plt.plot( tv[:,1] + tv[:,4]/24, tv[:,2], '.')
        plt.ylabel('Reflector Height (m)')
        plt.title('GNSS station: ' + station)
        plt.xlabel('Days in the Year ' + str(year) ) 
        plt.gca().invert_yaxis()
        plt.xticks(rotation =45)
        plt.grid()
        plt.show()
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


def writejsonfile(ntv,station, outfile):
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

def splines_for_dummies2(fname,perday,pltit,outlierV):
    """
    tvd is a filename for subdaily RH results 

    pltit is a boolean for plots to come to the screen
    note: x was in units of years before but now is in days??


    Returns xx and y- these are in units of days (xx)
    and meters (yy), where yy is the spline fit to reflector height
    computed perday times per day
    """
    # read in the tvd values which are the output of gnssir
    tvd = np.loadtxt(fname,comments='%')
    # sort the data by days 
    ii = np.argsort( (tvd[:,1]+tvd[:,4]/24) ).T
    tvd = tvd[ii,:]

    # time variable in days
    th= tvd[:,1] + tvd[:,4]/24; 
    # reflector height
    h = tvd[:,2]
    xfac = tvd[:,9]

    # 
    fillgap = 1/24 # one hour fake values
    gap = 4/24 # up to four hour gap allowed

    tnew =[] ; ynew =[]; 
    # fill in gaps using variables called tnew and ynew
    for i in range(1,len(th)):
        d= th[i]-th[i-1]
        if (d > gap):
            #print(t[i], t[i-1])
            print('found a gap in hours',d*24)
            x0 = th[i-1:i+1]
            h0 = h[i-1:i+1]
            f = scipy.interpolate.interp1d(x0,h0)
            tnew = np.arange(th[i-1]+fillgap, th[i], fillgap)
            ynew = f(tnew)
#            print('new t values', tnew)
#            print('new h values', ynew)

# append the interpolated values so the splines don't get unhappy

    if (len(tnew) > 0):
        tnew = np.append(th,tnew)
        ynew = np.append(h,ynew)
        # try sorting to see if that fixes it
        ii = np.argsort( tnew) 
        tnew = tnew[ii]
        ynew = ynew[ii]
    else:
        tnew = th
        ynew = h

    knots_per_day = 12

    Ndays = tnew.max()-tnew.min()
    numKnots = int(knots_per_day*(Ndays))
    print('First and last time values', '{0:8.3f} {1:8.3f} '.format (tnew.min(), tnew.max()) )
    print('Number of RH obs', len(h))
    print('Average obs per day', '{0:5.1f} '.format (len(h)/Ndays) )
    print('Number of knots', numKnots)
    print('Number of days ', '{0:8.2f}'.format ( Ndays) )
    # need the first and last knot to be inside the time series
    t1 = tnew.min()+0.05
    t2 = tnew.max()-0.05
    # try this 
    # 
    knots =np.linspace(t1,t2,num=numKnots)

    t, c, k = interpolate.splrep(tnew, ynew, s=0, k=3,t=knots,task=-1)
    # user specifies how many values per day you want to send back to the user  

    # should i do extrapolate True? it is the default  - could make it periodic?
    spline = interpolate.BSpline(t, c, k, extrapolate=True)
    # equal spacing in both x and y
    # evenly spaced data - units of days
    N = int(Ndays*perday)
    xx = np.linspace(tnew.min(), tnew.max(), N)
    spl_x = xx; spl_y = spline(xx)

#  clean up the data a bit
    resid_spl = h - spline(th) 
    # good points
    i = (np.absolute(resid_spl) < outlierV)
    # bad points
    j = (np.absolute(resid_spl) > outlierV)
    # put these in a file if you are interested
    print_badpoints(tvd[j,:])
    if pltit:
        plt.figure()
        plt.subplot(211)
        plt.plot(th, h, 'bo', label='Original points',markersize=3)
        # cannot use this because i do not have the year in the tnew variable
        #obstimes = fract_to_obstimes(spl_x)
        plt.plot(spl_x, spl_y, 'r', label='spline')
        plt.title('Reflector Height')
        plt.ylabel('meters')
        plt.plot(th[j], h[j], 'co',label='Outliers') 
        plt.grid()
        #plt.legend(loc="upper left")

# take out the bad points
    th = th[i]; h = h[i]
    xfac = xfac[i]
    resid_spl = resid_spl[i]
# remove bad points from the original variable
    tvd = tvd[i,:]

# put the original series without outliers eventually?
# use first diff to get simple velocity.  
# 24 hours a day, you asked for perday values by day
    obsPerHour= perday/24
        
    # these are unreliable at beginning and end of the series for clear reasons
    tvel = spl_x[1:N]
    yvel = obsPerHour*np.diff(spl_y)

    rhdot_at_th = np.interp(th, tvel, yvel)

    # this is the RHdot correction. This can be done better - 
    # this is just a start
    correction = xfac*rhdot_at_th

    if pltit:
        plt.subplot(212)
        plt.plot(tvel, yvel, '-',label='RHdot')
        plt.plot(th, rhdot_at_th,'.',label='RHdot at obs')
        plt.title('RHdot in meters per hour')
        plt.ylabel('meters per hour'); plt.xlabel('days of the year')
        plt.grid()
        plt.xticks(rotation=45)

        plt.figure()
        plt.subplot(211)
        plt.plot(th, resid_spl,'.',label='uncorr')
        plt.plot(th, resid_spl - correction,'.',label='wcorr')
        plt.legend(loc="upper left")
        plt.xlabel('days of the year')
        plt.grid()
        plt.xticks(rotation=45)
        plt.show()
    print('RMS no corr (m)', '{0:6.3f}'.format ( np.std(resid_spl)) )
    print('RMS w/ corr (m)', '{0:6.3f}'.format ( np.std(resid_spl - correction))  )
    # this is RH with the RHdot correction
    a = resid_spl - correction
    print('Freq   Bias(m)   Sigma (m)')
    for f in [1, 20, 5, 101, 102, 201, 205,207,208]:
        ff = (tvd[:,8] == f)
        if len(a[ff]) > 0:
            print('{0:3.0f} {1:6.2f} {2:6.2f} '.format (f, np.mean(a[ff]), np.std(a[ff]) ) )


    return tvd, correction 

