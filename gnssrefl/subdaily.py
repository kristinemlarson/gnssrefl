# codes for subdaily module. primarily for tidal applications
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

def print_badpoints(t,outliersize):
    """
    input: station name and lomb scargle result array of "bad points"
    second input is the size of the outlier, in meters
    author: kristine larson

    """
# (1)  (2)   (3) (4)  (5)     (6)   (7)    (8)    (9)   (10)  (11) (12) (13)    (14)     (15)    (16) (17) (18,19,20,21,22)
# year, doy, RH, sat,UTCtime, Azim, Amp,  eminO, emaxO,NumbOf,freq,rise,EdotF, PkNoise  DelT     MJD  refr  MM DD HH MM SS
# (0)  (1)   (2) (3)  (4)     (5)   6 )    (7)    (8)   (9)  (10) (11) (12)    (13)     (14)    (

    m,n = t.shape
    f = 'outliers.txt'
    print('outliers written to file: ', f) 
    fout = open(f, 'w+')
    for i in range(0,m):
        fout.write('doy {0:3.0f} sat {1:3.0f} azim {2:6.2f} fr {3:3.0f} pk2noise {4:5.1f} residual {5:5.2f} \n'.format(
            t[i,1], t[i,3],t[i,5], t[i,10], t[i,13], outliersize[i] ))
    fout.close()

def output_names(txtdir, txtfile,csvfile,jsonfile):
    """
    input: txtdir is the directory where the results should be written out
    txtfile, csvfile, and jsonfile are the command line input values 
    if they are not set (i.e. they are None), that means you do not want it.
    if writejson is true, then it is written to txtdir + jsonfile 
    if writecsv is true, then it is written to txtdir + csvfile and so on
    author: kristine larson
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

def write_subdaily(outfile,station,ntv,writecsv,writetxt,extraline):
    """
    input: output filename
    station - 4 character station name
    nvt is the variable with the LSP results
    writecsv and writetxt are booleans to tell you whether you 
    want csv output format or plain txt format (with spaces between colunmns)
    21may04 - extra line may be added to the header
    changed this to use hte original format.  changing the number of columns was a HUGE
    mistake.  put m,d,h,m,s at the end

    author: kristine larson
    """
    # this is lazy - should use shape
    N= len(ntv)
    nr,nc = ntv.shape
    print('write_subdaily', nr,nc)
    N= nr
    # this is true so I don't have to move the indents
    print('Results are being written to : ', outfile)
    fout = open(outfile, 'w+')
    write_out_header(fout,station,extraline)
    dtime = False
    for i in np.arange(0,N,1):
        year = int(ntv[i,0]); doy = int(ntv[i,1])
        year, month, day, cyyyy,cdoy, YMD = g.ydoy2useful(year,doy)
        rh = ntv[i,2]; UTCtime = ntv[i,4]; 
        dob, year, month, day, hour, minute, second = g.ymd_hhmmss(year,doy,UTCtime,dtime)
        #ctime = g.nicerTime(UTCtime); 
        #hr = ctime[0:2]
        #minute = ctime[3:5]
        # you can either write a csv or text, but not both
        if writecsv:
            fout.write(" {0:4.0f},{1:3.0f},{2:6.3f},{3:3.0f},{4:6.3f},{5:6.2f},{6:6.2f},{7:6.2f},{8:6.2f},{9:4.0f},{10:3.0f},{11:2.0f},{12:8.5f},{13:6.2f},{14:7.2f},{15:12.6f},{16:1.0f},{17:2.0f},{18:2.0f},{19:2.0f},{20:2.0f},{21:2.0f} \n".format(year, doy, rh,ntv[i,3],UTCtime,ntv[i,5],ntv[i,6],ntv[i,7],ntv[i,8], ntv[i,9], \
                            ntv[i,10],ntv[i,11], ntv[i,12],ntv[i,13], ntv[i,14], ntv[i,15], ntv[i,16],month,day,hour,minute, int(second)))
        else:
            fout.write(" {0:4.0f} {1:3.0f} {2:6.3f} {3:3.0f} {4:6.3f} {5:6.2f} {6:6.2f} {7:6.2f} {8:6.2f} {9:4.0f} {10:3.0f} {11:2.0f} {12:8.5f} {13:6.2f} {14:7.2f} {15:12.6f} {16:1.0f} {17:2.0f} {18:2.0f} {19:2.0f} {20:2.0f} {21:2.0f} \n".format(year, doy, rh,ntv[i,3],UTCtime,ntv[i,5],ntv[i,6],ntv[i,7],ntv[i,8], ntv[i,9], \
                            ntv[i,10],ntv[i,11], ntv[i,12],ntv[i,13], ntv[i,14], ntv[i,15], ntv[i,16],month,day,hour,minute, int(second)))
    fout.close()


def readin_and_plot(station, year,d1,d2,plt2screen,extension):
    """
    Inputs:
    station - 4 character name
    year is year ;-)  
    d1 and d2 are days of year if you want to look at a smaller dataset
    plt2screen is a boolean whether you want the plot displayed to the screen

    author: kristine larson
    2021april27 return datetime object
    """
    print('Read in the RH retrievals and plot it between these days: ',d1,d2)
    if (d2 < d1):
        print('First day of year must be less than last day of year. Exiting')
        sys.exit()

    xdir = os.environ['REFL_CODE']

    # output will go to REFL_CODE/Files
    txtdir = xdir + '/Files'
    if not os.path.exists(txtdir):
        os.makedirs(txtdir)

    # where the LSP results are kept
    direc = xdir + '/' + str(year) + '/results/' + station  + '/' + extension + '/'
    # datetime object for time
    obstimes = []
    tv = np.empty(shape=[0, 17])
    if os.path.isdir(direc):
        all_files = os.listdir(direc)
        #print(direc)
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

    nr,nc=tv.shape
    print('Number of RH retrievals', nr)

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

    # now that you have everything the way you want it .... 
    nr,nc = tv.shape
    otimes = []
    for ijk in range(0,nr):
        dtime, iyear,imon,iday,ihour,imin,isec = g.ymd_hhmmss(tv[ijk,0],tv[ijk,1],tv[ijk,4],True)
        otimes.append(dtime)

    # make arrays to save number of RH retrievals on each day
    nval = []; tval = []; y = tv[0,0]
    for d in range(d1,(d2+1)):
        ii = (tv[:,1] == d)
        dtime, iyear,imon,iday,ihour,imin,isec = g.ymd_hhmmss(year,d,12,True)
        tval.append(dtime)
        n = len(tv[ii,1])
        nval.append(n)
    #
    fs = 12
    if plt2screen:
        fig,ax=plt.subplots()
        #plt.figure()
        ax.plot(tval,nval,'.')
        plt.title(station + ': number of RH retrievals each day',fontsize=fs)
        plt.xticks(rotation =45,fontsize=fs)
        plt.yticks(fontsize=fs)
        plt.grid()
        fig.autofmt_xdate()

        fig,ax=plt.subplots()
        ax.plot( otimes, tv[:,2], '.')
        plt.ylabel('meters',fontsize=fs)
        plt.title('GNSS station: ' + station + ' Reflector Heights', fontsize=fs)
        plt.gca().invert_yaxis()
        plt.xticks(rotation =45,fontsize=fs)
        plt.yticks(fontsize=fs)
        plt.grid()
        fig.autofmt_xdate()

        plotname = txtdir + '/' + station + '_subdaily_RH.png'
        plt.savefig(plotname,dpi=300)
        print('png file saved as: ', plotname)
        plt.show()
    # probably nice to also have a plot with number of retrievals vs time

    
    return tv,otimes


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

    note: i have to assume this does not work well with data outages
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
    
def write_out_header(fout,station,extraline):
    """
    21may04 extra line for user
    changed this so that it is EXACTLY THE SAME as gnssir, with extra columns for m/d/h/m
    """
    xxx = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    fout.write('% Results for {0:4s} calculated on {1:20s} \n'.format(  station, xxx ))
    fout.write('% gnssrefl, https://github.com/kristinemlarson \n')
    if len(extraline) > 0:
        fout.write('% IMPORTANT {0:s} \n'.format(  extraline ))
    fout.write('% Phase Center corrections have NOT been applied \n')
    fout.write("% (1)  (2)   (3) (4)  (5)     (6)   (7)    (8)    (9)   (10)  (11) (12) (13)    (14)     (15)    (16) (17) (18,19,20,21,22)\n")
    fout.write("% year, doy, RH, sat,UTCtime, Azim, Amp,  eminO, emaxO,NumbOf,freq,rise,EdotF, PkNoise  DelT     MJD  refr  MM DD HH MM SS \n")


def writejsonfile(ntv,station, outfile):
    """
    subdaily RH values written out in json format
    inputs: ntv is the variable with concatenated results
    outfile is output file name
    2021may05 fixed a ton of column definition errors
    """
    print('You picked the json output')
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
    freq  = ntv[:,8].tolist()
    freq =[int(freq[i]) for i in range(N)];

    # amplitude of main periodogram (LSP)
    ampl  = ntv[:,6].tolist()
    ampl =[str(ampl[i]) for i in range(N)];

    # azimuth in degrees
    azim  = ntv[:,5].tolist()
    azim =[str(azim[i]) for i in range(N)];

    # edotF in units ??
    edotf  = ntv[:,9].tolist()
    edotf =[str(edotf[i]) for i in range(N)];

    # modified julian day
    #mjd = ntv[:,15].tolist()
    mjd = ntv[:,14].tolist()
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

def splines_for_dummies2(station,fname,fname_new,perday,pltit,outlierV,**kwargs):
    """
    tvd is a filename for subdaily RH results 

    pltit is a boolean for plots to come to the screen
    note: x was in units of years before but now is in days??


    Returns xx and y- these are in units of days (xx)
    and meters (yy), where yy is the spline fit to reflector height
    computed perday times per day

    2021april27 sending obstimes as kwarg input
    2021may5 change file format back to original file format
    author: kristine larson

    where did splines_for_dummies go? LOL

    21may18 try to remove massive outliers

    """
    fs = 12 # fontsize
    # read in the tvd values which are the output of gnssir
    tvd = np.loadtxt(fname,comments='%')
    # sort the data by days 
    ii = np.argsort( (tvd[:,1]+tvd[:,4]/24) ).T
    tvd = tvd[ii,:]

    print('try to remove massive outliers')
    NV = len(tvd)
    medval = np.median(tvd[:,2])
    xx= tvd[:,2]-medval
    plt.figure()
    n, bins, patches = plt.hist(xx, 50, density=True, facecolor='g', alpha=0.75)
    plt.xlabel('standard deviations')
    plt.title('RH (median removed) ')

    # use 3 sigma ... 
    Sig = np.std(xx)
    ij =  np.absolute(xx) < 3*Sig
    xnew = xx[ij]
    plt.figure()
    plt.subplot(212)
    n, bins, patches = plt.hist(xnew, 50, density=True, facecolor='g', alpha=0.75)
    plt.xlabel('standard deviations')
    plt.title('RH (median removed) without massive outliers')
    if pltit:
        plt.show()

    tvd = tvd[ij,:]


    # time variable in days
    th= tvd[:,1] + tvd[:,4]/24; 
    # reflector height (meters)
    h = tvd[:,2]
    # this is the edot factor
    xfac = tvd[:,12]

    # now get obstimes if they were not passed
    obstimes = kwargs.get('obstimes',[])
    if len(obstimes) == 0:
        print('you need to get those obstimes ...')
        obstimes = g.get_obstimes(tvd)

    # 
    fillgap = 1/24 # one hour fake values
    gap = 4/24 # up to four hour gap allowed

    tnew =[] ; ynew =[]; 
    # fill in gaps using variables called tnew and ynew
    for i in range(1,len(th)):
        d= th[i]-th[i-1] # delta in time
        if (d > gap):
            #print(t[i], t[i-1])
            x0 = th[i-1:i+1]
            h0 = h[i-1:i+1]
            print('found a gap in hours',d*24, 'day ', x0[0])
            f = scipy.interpolate.interp1d(x0,h0)
            # so this is fake data
            ttnew = np.arange(th[i-1]+fillgap, th[i], fillgap)
            yynew = f(ttnew)
            #print(ttnew)
            # now append it to your real data
            tnew = np.append(tnew,ttnew)
            ynew = np.append(ynew,yynew)
        else:
            tnew = np.append(tnew,th[i])
            ynew = np.append(ynew,h[i])

    # sort it just to make sure ...
    ii = np.argsort( tnew) 
    tnew = tnew[ii]
    ynew = ynew[ii]

    knots_per_day = 12
    Ndays = tnew.max()-tnew.min()
    numKnots = int(knots_per_day*(Ndays))
    print('First and last time values', '{0:8.3f} {1:8.3f} '.format (tnew.min(), tnew.max()) )
    print('Number of RH obs', len(h))
    print('Average obs per day', '{0:5.1f} '.format (len(h)/Ndays) )
    print('Number of knots: ', numKnots)
    print('Number of days of data: ', '{0:8.2f}'.format ( Ndays) )
    # need the first and last knot to be inside the time series
    t1 = tnew.min()+0.05
    t2 = tnew.max()-0.05
    # try this 
    # 
    knots =np.linspace(t1,t2,num=numKnots)

    #ftest = open('testing.txt', 'w+')
    #for i in range(0,len(tnew)):
    #    ftest.write('{0:9.4f} {1:7.3f}  \n'.format( tnew[i], ynew[i]))
    #ftest.close()

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
# make a residual to the spline fit.  Spline is NOT truth
    resid_spl = h - spline(th) 
    # good points
    i = (np.absolute(resid_spl) < outlierV)
    # bad points
    j = (np.absolute(resid_spl) > outlierV)
    # put these in a file if you are interested
    print_badpoints(tvd[j,:], resid_spl[j])
    if pltit:
        plt.figure()
        #plt.plot(obstimes, h, 'bo', label='Original points',markersize=3)
        plt.plot(th, h, 'bo', label='Original points',markersize=3)
        # cannot use this because i do not have the year in the tnew variable
        #obstimes = fract_to_obstimes(spl_x)
        plt.plot(spl_x, spl_y, 'r', label='spline')
        plt.title('Station: ' + station + ' Reflector Height')
        plt.plot(th[j], h[j], 'co',label='Outliers') 
        plt.ylabel('meters',fontsize=fs)
        plt.xlabel('days',fontsize=fs)
        plt.grid()
        plt.gca().invert_yaxis()
        plt.legend(loc="upper left")

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
    #  this is where i should do a new spline fit with the corrected RH values
    # h = h - correction


    if pltit:
        fig,ax=plt.subplots()
        ax.plot(tvel, yvel, '-',label='RHdot')
        ax.plot(th, rhdot_at_th,'.',label='RHdot at obs')
        plt.title('RHdot in meters per hour',fontsize=fs)
        plt.ylabel('meters per hour',fontsize=fs); 
        plt.xlabel('days of the year',fontsize=fs)
        plt.grid()
        plt.yticks(fontsize=fs)
        plt.xticks(fontsize=fs)
        #fig.autofmt_xdate()

        #plt.figure()
        fig,ax=plt.subplots()
        ax.plot(th, resid_spl,'.',label='without RHdot corr')
        ax.plot(th, resid_spl - correction,'.',label='with RHdot corr')
        plt.legend(loc="upper left")
        plt.xlabel('days of the year',fontsize=fs)
        plt.ylabel('meters',fontsize=fs)
        plt.yticks(fontsize=fs)
        plt.xticks(fontsize=fs)
        plt.title('Reflector Height Residuals to the Spline Fit',fontsize=fs)
        plt.grid()
        plt.show()
    print('RMS no RHdot correction (m)', '{0:6.3f}'.format ( np.std(resid_spl)) )
    print('RMS w/ RHdot correction (m)', '{0:6.3f}'.format ( np.std(resid_spl - correction))  )
    # this is RH with the RHdot correction
    correctedRH = resid_spl - correction
    print('Freq  Bias  Sigma   NumObs ')
    print('       (m)   (m)       ')
    for f in [1, 20, 5, 101, 102, 201, 205,207,208]:
        ff = (tvd[:,10] == f)
        ret = correctedRH[ff]
        if len(ret) > 0:
            print('{0:3.0f} {1:6.2f} {2:6.2f} {3:6.0f}'.format (f, np.mean(ret), np.std(ret), len(ret) ) )

    # put the correction in column 2
    tvd[:,2] = tvd[:,2] - correction
    writecsv = False
    writetxt = True
    extraline = 'Large outliers removed and RHDot correction has been applied'
    write_subdaily(fname_new,station,tvd,writecsv,writetxt,extraline)

    return tvd, correction 


def testing_hourly(tvd):
    """
    this does not work
    """
    d1 = 15
    d2 = 40
    # start with hourly
    t = tvd[:,1] + tvd[:,4]/24
    rh = tvd[:,2]
    rh_hourly = []; t_hourly = []
    for d in range(d1,d2):
        for h in range(0,24):
            t1= d + h/24; t2= d + (h+1)/24;
            ii = (t >= t1) & (t < t2)  
            if len(rh[ii]) > 0:
                avgRH = np.average(rh[ii])
                #print(d,h,avgRH)
                rh_hourly.append(avgRH)
                # put each time at the half hour
                t_hourly.append(d+(h+0.5)/24)
            
    plt.figure()
    plt.plot(t_hourly, rh_hourly,'.')
    plt.show()

