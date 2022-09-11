# codes for subdaily module. primarily for tidal applications
import argparse
import datetime
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

from datetime import date

# support code
import gnssrefl.gps as g


import scipy
import scipy.interpolate as interpolate
from scipy.interpolate import interp1d
import math

def print_badpoints(t,outliersize):
    """
    parameters
    -------------
    t : numpy array
        lomb scargle result array of "bad points". Format given below

    outliersize: float
        outlier criterion, in meters

    returns
    ----------
    writes to a file called outliers.txt

    """
# format of t 

# (1)  (2)   (3) (4)  (5)     (6)   (7)    (8)    (9)   (10)  (11) (12) (13)    (14)     (15)    (16) (17) (18,19,20,21,22)
# year, doy, RH, sat,UTCtime, Azim, Amp,  eminO, emaxO,NumbOf,freq,rise,EdotF, PkNoise  DelT     MJD  refr  MM DD HH MM SS
# (0)  (1)   (2) (3)  (4)     (5)   6 )    (7)    (8)   (9)  (10) (11) (12)    (13)     (14)    (15)  (16) ... 

    m,n = t.shape
    f = 'outliers.txt'
    print('outliers written to file: ', f) 
    fout = open(f, 'w+')
    if (m > 0):
        for i in range(0,m):
            fout.write('doy {0:3.0f} sat {1:3.0f} azim {2:6.2f} fr {3:3.0f} pk2noise {4:5.1f} residual {5:5.2f} \n'.format( 
                t[i,1], t[i,3],t[i,5], t[i,10], t[i,13], outliersize[i] ))
        fout.close()
    else:
        print('no outlier points to write to a file')

def output_names(txtdir, txtfile,csvfile,jsonfile):
    """
    parameters
    ----------------
    txtdir : str
        the directory where the results should be written out
    txtfile : str
        name of the output file
    csvfile : boolean
        cl input whether the output file should be csv format
    jsonfile : boolean
        cl input for whether the output file should be in the json format

    default is plain txt file

    returns
    -----------
    writetxt : boolean

    writecsv : boolean

    writejson : boolean

    outfile : str
        filename

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

def write_subdaily(outfile,station,ntv,writecsv,extraline,**kwargs):
    """
    writes out the results

    parameters
    -----------
    input: str
        output filename
    station : str
        4 character station name, lowercase

    nvt : numpy multi-dimensional
        the variable with the LSP results read via np.loadtxt

    writecsv : boolean

    writetxt : boolean

    this does not accommodate json as yet
    """
    # this is lazy - should use shape
    RHdot_corr= kwargs.get('RHdot_corr',[])
    newRH = kwargs.get('newRH',[])
    if len(RHdot_corr) + len(newRH) == 0:
        extra  = False
    else:
        print('extra columns are being written')
        extra = True
    N= len(ntv)
    nr,nc = ntv.shape
    if nr == 0:
        print('No results in this file, so nothing to write out.')
        return
    print(nr, ' observations will be written to ',outfile)
    N= nr
    fout = open(outfile, 'w+')
    if extra:
        write_out_header(fout,station,extraline,extra_columns=True)
    else:
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
            fout.write(" {0:4.0f},{1:3.0f},{2:7.3f},{3:3.0f},{4:6.3f},{5:6.2f},{6:6.2f},{7:6.2f},{8:6.2f},{9:4.0f},{10:3.0f},{11:2.0f},{12:8.5f},{13:6.2f},{14:7.2f},{15:12.6f},{16:1.0f},{17:2.0f},{18:2.0f},{19:2.0f},{20:2.0f},{21:2.0f} \n".format(year, doy, rh,ntv[i,3],UTCtime,ntv[i,5],ntv[i,6],ntv[i,7],ntv[i,8], ntv[i,9], \
                            ntv[i,10],ntv[i,11], ntv[i,12],ntv[i,13], ntv[i,14], ntv[i,15], ntv[i,16],month,day,hour,minute, int(second)))
        else:
            if extra:
                fout.write(" {0:4.0f} {1:3.0f} {2:7.3f} {3:3.0f} {4:6.3f} {5:6.2f} {6:6.2f} {7:6.2f} {8:6.2f} {9:4.0f} {10:3.0f} {11:2.0f} {12:8.5f} {13:6.2f} {14:7.2f} {15:12.6f} {16:1.0f} {17:2.0f} {18:2.0f} {19:2.0f} {20:2.0f} {21:2.0f} {22:6.3f} {23:6.3f} \n".format(year, doy, rh,ntv[i,3],UTCtime,ntv[i,5],ntv[i,6],ntv[i,7],ntv[i,8], ntv[i,9], \
                            ntv[i,10],ntv[i,11], ntv[i,12],ntv[i,13], ntv[i,14], ntv[i,15], ntv[i,16],month,day,hour,minute, int(second), newRH[i], RHdot_corr[i]))
            else:
                fout.write(" {0:4.0f} {1:3.0f} {2:7.3f} {3:3.0f} {4:6.3f} {5:6.2f} {6:6.2f} {7:6.2f} {8:6.2f} {9:4.0f} {10:3.0f} {11:2.0f} {12:8.5f} {13:6.2f} {14:7.2f} {15:12.6f} {16:1.0f} {17:2.0f} {18:2.0f} {19:2.0f} {20:2.0f} {21:2.0f} \n".format(year, doy, rh,ntv[i,3],UTCtime,ntv[i,5],ntv[i,6],ntv[i,7],ntv[i,8], ntv[i,9], \
                            ntv[i,10],ntv[i,11], ntv[i,12],ntv[i,13], ntv[i,14], ntv[i,15], ntv[i,16],month,day,hour,minute, int(second)))
    fout.close()


def readin_and_plot(station, year,d1,d2,plt2screen,extension,sigma,writecsv,azim1,azim2,ampl,peak2noise,txtfile,h1,h2):
    """
    reads in RH results and makes various plots to help users assess the quality of the solution

    parameters
    -------------
    station : string
        4 character station name

    year : integer

    d1 : integer
        first day of year

    d2 : integer 
        last day of year

    plt2screen : boolean
        if True plots are displayed to the screen

    extension : str
        allow user to specify an extension for results (i.e. gnssir was run using extension string)

    sigma : float
         how many standard deviations away from mean you allow.  

    writecsv : boolean

    azim1 : float
        minimum azimuth value (degrees)

    azim2 : float
        maximum azimuth value (degrees)

    ampl : float
        minimum LSP amplitude allowed

    peak2noise : float
        minim peak2noise value to set solution good

    txtfile : str
        name of output file

    h1 : float
        minimum reflector height (m)

    h2 : float
        maximum reflector height (m)

    returns
    --------------

    tv : numpy array
        LSP results (augmented)

    otimes : datetime object 
        times of observations 

    fname : str
        result file

    fname_new : str
        result file with outliers removed

    """
    # fontsize for plot labels and such
    fs = 10
    xdir = os.environ['REFL_CODE']
    # output will go to REFL_CODE/Files
    txtdir = xdir + '/Files'
    print('Will remove daily outliers greater than ', sigma, ' sigma')
    if not os.path.exists(txtdir):
        os.makedirs(txtdir)
    print('Plot to the screen has been set to ', plt2screen)

    print('>>>>>>>>>>>>>>>>>>>>>>>> readin RH data <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    if txtfile == '':
        print('Read in the RH retrievals for ', year, ' and these days: ',d1,d2)
        if (d2 < d1):
            print('First day of year must be less than last day of year. Exiting')
            sys.exit()
    # where the LSP results are kept
        direc = xdir + '/' + str(year) + '/results/' + station  + '/' + extension + '/'
    # datetime object for time
        obstimes = []
        tv = np.empty(shape=[0, 17])
        if os.path.isdir(direc):
            all_files = os.listdir(direc)
            for f in all_files:
            # only evaluate txt files
                if (len(f) ==  7) and (f[4:7] == 'txt'):
                    day = int(f[0:3])
                #print('looking at file: ', day)
                    if (day >= d1) & (day <= d2):
                        fname = direc + f
                        try:
                            a = np.loadtxt(fname,comments='%')
                            if len(a) > 0:
                                tv = np.append(tv, a,axis=0)
                        except:
                            print('some issue with ',fname)

    else:
        # using external file of concatenated results
        tv = np.loadtxt(txtfile,comments='%')

     
    tv,t,rh,fdoy,ldoy= apply_new_constraints(tv,azim1,azim2,ampl,peak2noise,d1,d2,h1,h2)

    tvoriginal = tv
    nr,nc = tvoriginal.shape
    print('RH retrievals after all commandline constraints', nr)

    # now that you have everything the way you want it .... 
    # make the datatime objects
    nr,nc = tv.shape
    otimes = []
    for ijk in range(0,nr):
        dtime, iyear,imon,iday,ihour,imin,isec = g.ymd_hhmmss(tv[ijk,0],tv[ijk,1],tv[ijk,4],True)
        otimes.append(dtime)

    # make arrays to save number of RH retrievals on each day
    residuals = np.empty(shape=[0,1])
    nval = []; tval = []; y = tv[0,0];  
    # constellation spec number of values
    Cval=[]; Gval =[]; Rval=[]; Eval=[]
    stats = np.empty(shape=[0,3])
    # only look at the doy range where i have data
    for d in range(fdoy,(ldoy+1)):
        ii = (tv[:,1] == d) ; tmp = tv[ii,:]
        dtime, iyear,imon,iday,ihour,imin,isec = g.ymd_hhmmss(year,d,12,True)
        tval.append(dtime)
        n = len(tv[ii,1])
        # total
        nval.append(n)
#       https://stackoverflow.com/questions/26786946/how-to-return-indices-of-values-between-two-numbers-in-numpy-array
        gi =  (tmp[:,10] < 100);
        ri =  (tmp[:,10] > 100) * (tmp[:,10] < 200);
        ei =  (tmp[:,10] > 200) * (tmp[:,10] < 300);
        ci =  (tmp[:,10] > 300); # beidou

        #print( len(tmp[ri,1])) print( len(tmp[ei,1]))

        if (n > 0):
            rhavg = np.mean(tv[ii,2]); 
            rhstd = np.std(tv[ii,2]); 
            newl = [dtime, rhavg, rhstd]
            stats = np.append(stats, [newl], axis=0)
            b = ( tv[ii,2] - rhavg*np.ones( len(tv[ii,2]) ))/ rhstd
            residuals = np.append(residuals, b)
            Gval = np.append(Gval, len(tmp[gi,1]))
            Eval = np.append(Eval, len(tmp[ei,1]))
            Rval = np.append(Rval, len(tmp[ri,1]))
            Cval = np.append(Cval, len(tmp[ci,1]))
        else:
            Gval = np.append(Gval, 0)
            Eval = np.append(Eval, 0)
            Rval = np.append(Rval, 0)
            Cval = np.append(Cval, 0)

    ii = (np.absolute(residuals) > sigma) # data you like
    jj = (np.absolute(residuals) < sigma) # data you do not like ;-)
    if plt2screen:
        fig,ax=plt.subplots()
        ax.plot(tval,nval,'ko',label='Total',markersize=3)
        if (np.sum(Gval) > 0):
            ax.plot(tval,Gval,'bo',label='GPS',markersize=3)
        if (np.sum(Rval) > 0):
            ax.plot(tval,Rval,'ro',label='GLO',markersize=3)
        if (np.sum(Eval) > 0):
            ax.plot(tval,Eval,'o',color='orange',label='GAL',markersize=3)
        if (np.sum(Cval) > 0):
            ax.plot(tval,Cval,'co',label='BEI',markersize=3)
        plt.legend(loc="upper left")
        plt.title(station + ': number of RH retrievals each day',fontsize=fs)
        plt.xticks(rotation =45,fontsize=fs); plt.yticks(fontsize=fs)
        plt.grid()
        fig.autofmt_xdate()
        plotname = txtdir + '/' + station + '_Subnvals.png'
        plt.savefig(plotname,dpi=300)
        print('png file saved as: ', plotname)


        minAz = float(np.min(tv[:,5])) ; maxAz = float(np.max(tv[:,5]))

        #print(d1,d2)
        two_stacked_plots(otimes,tv,station,txtdir,year,d1,d2)
        stack_two_more(otimes,tv,ii,jj,stats, station, txtdir,sigma)
        plt.show()

    # this might work... and then again, it might not
    print_badpoints(tv[ii,:],residuals[ii])

    # now write things out
    fname = xdir + '/Files/' + station + '_all.txt'
    fname_new = xdir + '/Files/' + station + '_subdaily_edits.txt'
    extraline = ''

    editedtv = tv[jj,:]
    nr,nc = editedtv.shape

    write_subdaily(fname,station,tvoriginal,writecsv,extraline)
    print('Edited observations',nr)
    extraline = 'outliers removed/restrictions'
    write_subdaily(fname_new,station,editedtv,writecsv,extraline)
    NV = len(tvoriginal)
    print('Percent of observations removed: ', round(100*(NV-nr)/NV,2))
    
    # now return the names of the output files ... 
    return tv,otimes, fname, fname_new


def quickTr(year, doy,frachours):
    """
    parameters
    -----------
    year : integer

    doy : integer

    frachours : float
        real-valued UTC hour 

    inputs from the lomb scargle code (year, doy) and UTC hour (fractional)
    returns
    --------
    datestr : string
         date ala YYYY-MM-DD HH-MM-SS
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
    """
    this does not seem to be used
    spl_x : numpy array
        fractional time 

    obstimes : numpy array
        datetime format
    """
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

def spline_in_out(x,y,knots_per_day):
    """
    inputs are numpy arrays of time (in doy) and reflector heights (m)
    outputs are the spline fit

    note: i have to assume this does not work well with data outages
    """
    Ndays = round(x.max()-x.min())
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

    return xx,spline(xx) 
    
def write_out_header(fout,station,extraline,**kwargs):
    """
    writes out header for results file ... 
    21may04 extra line for user
    changed this so that it is EXACTLY THE SAME as gnssir, with extra columns for m/d/h/m
    author: kristine larson
    """
    extra_columns = kwargs.get('extra_columns',False)
    xxx = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    fout.write('% Results for {0:4s} calculated on {1:20s} \n'.format(  station, xxx ))
    fout.write('% gnssrefl, https://github.com/kristinemlarson \n')
    if len(extraline) > 0:
        fout.write('% IMPORTANT {0:s} \n'.format(  extraline ))
    fout.write('% Phase Center corrections have NOT been applied \n')
    if extra_columns:
        fout.write("% (1)  (2)   (3) (4)  (5)     (6)   (7)    (8)    (9)   (10)  (11) (12) (13)    (14)     (15)    (16) (17) (18,19,20,21,22) (23)    (24)\n")
        fout.write("% year, doy, RH, sat,UTCtime, Azim, Amp,  eminO, emaxO,NumbOf,freq,rise,EdotF, PkNoise  DelT     MJD  refr  MM DD HH MM SS  newRH  RHcorr\n")
    else:
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

def rhdot_correction(station,fname,fname_new,pltit,outlierV,**kwargs):
    """
    inputs:
    station - 4 char
    fname - input filename 
    fname_new - output filename
    pltit - boolean for plots to the screen
    outlierV is meter outlier cutoff

    pltit is a boolean for plots to come to the screen
    note: x was in units of years before but now is in days??

    2021april27 sending obstimes as kwarg input
    2021may5 change file format back to original file format
    21may18 try to remove massive outliers
    21oct27 add usespline option because this code is not robust
    can also input knots per day 

    author: kristine larson

    """
    outlierV = float(outlierV) #just to make sure - i think it was sending a string
    # output will go to REFL_CODE/Files
    xdir = os.environ['REFL_CODE']
    txtdir = xdir + '/Files'

#   how often do you want velocity computed (per day)
    perday = 24*20 # so every 3 minutes
    fs = 10 # fontsize
    # making a knot every three hours ...
    # knots_per_day = 8
    knots_default = 8
    knots_per_day= kwargs.get('knots',8)
    print('>>>>>>>>>>>>>>>>>>>> Entering spline fit <<<<<<<<<<<<<<<<<<<<<<<<')
    print('Input filename:', fname)
    print('Output filename: ', fname_new)
    # read in the tvd values which are the output of gnssir
    # i.e. the reflector heights
    tvd = np.loadtxt(fname,comments='%')
    if len(tvd) == 0:
        print('empty input file')
        return
    # sort the data in time
    ii = np.argsort( (tvd[:,1]+tvd[:,4]/24) ).T
    tvd = tvd[ii,:]

    NV = len(tvd)
    # remove a median value from RH
    medval = np.median(tvd[:,2])
    xx= tvd[:,2]-medval

    # use 3 sigma for the histogram plot ????
    Sig = np.std(xx)
    ij =  np.absolute(xx) < 3*Sig
    xnew = xx[ij]

    # sure looks like 3 sigma is being removed here! But this would get rid of a real storm surge
    # perhaps not needed since 3 sigma should have been taken out from the daily values
    tvd = tvd[ij,:]

    # time variable in days
    th= tvd[:,1] + tvd[:,4]/24; 
    # reflector height (meters)
    h = tvd[:,2]
    # this is the edot factor - 
    # this was computed by gnssir as the mean of the tangent(eangles) over an arc,
    # divided by edot (the tiem rate of change of elevation angle, initially rad/sec,
    # but then converted to rad/hour).  Thus this parameter has units  rad/(rad/hour) >>>> hours
    # it is multiplied by RHDot in meters/hour, which gives you a correction value in meters
    xfac = tvd[:,12]
    
    # now get obstimes if they were not passed
    obstimes = kwargs.get('obstimes',[])
    if len(obstimes) == 0:
        print('Calculating obstimes ...')
        obstimes = g.get_obstimes(tvd)

    # 
    fillgap = 1/24 # one hour fake values
    # ???
    gap = 5/24 # up to five hour gap allowed before warning

    tnew =[] ; ynew =[]; faket = []; 
    # fill in gaps using variables called tnew and ynew
    Ngaps = 0
    for i in range(1,len(th)):
        d= th[i]-th[i-1] # delta in time in units of days ?
        if (d > gap):
            #print(t[i], t[i-1])
            x0 = th[i-1:i+1]
            h0 = h[i-1:i+1]
            print('Gap on doy:', int(np.floor(x0[0])), ' lasting ', round(d*24,2), ' hours ')
            Ngaps = Ngaps + 1
            f = scipy.interpolate.interp1d(x0,h0)
            #f = scipy.interpolate.interp1d(x0,h0,'quadratic')
            # so this is fake data
            ttnew = np.arange(th[i-1]+fillgap, th[i], fillgap)
            yynew = f(ttnew)
            faket = np.append(faket, ttnew)
            # now append it to your real data
            tnew = np.append(tnew,ttnew)
            ynew = np.append(ynew,yynew)
        else:
            tnew = np.append(tnew,th[i])
            ynew = np.append(ynew,h[i])

    if (Ngaps > 3):
        print('This is a beta version of the rhdot/spline fit code - and does not work well with gaps. You have been warned!')
    # sort it just to make sure ...
    ii = np.argsort( tnew) 
    tnew = tnew[ii]
    ynew = ynew[ii]

    Ndays = tnew.max()-tnew.min()
    numKnots = int(knots_per_day*(Ndays))
    print('First and last time values', '{0:8.3f} {1:8.3f} '.format (tnew.min(), tnew.max()) )
    print('Number of RH obs', len(h))
    print('Average obs per day', '{0:5.1f} '.format (len(h)/Ndays) )
    print('Knots per day: ', knots_per_day, ' Number of knots: ', numKnots)
    print('Outlier criterion with respect to spline fit (m): ', outlierV)
    print('Number of days of data: ', '{0:8.2f}'.format ( Ndays) )
    # need the first and last knot to be inside the time series ???
    # 
    # try this instead - first and last day
    tt1 = tvd[0,1]
    tt2 = tvd[-1,1] + 1
    kdt = knots_per_day/24
    knots = np.linspace(tt1 + kdt/2, tt2 - kdt/2, numKnots)
    firstKnot_in_minutes = 15
    t1 = tnew.min()+firstKnot_in_minutes/60/24
    t2 = tnew.max()-firstKnot_in_minutes/60/24
    knots =np.linspace(t1,t2,num=numKnots)


    t, c, k = interpolate.splrep(tnew, ynew, s=0, k=3,t=knots,task=-1)


    # should i do extrapolate True? it is the default  
    #spline = interpolate.BSpline(t, c, k, extrapolate=True)
    spline = interpolate.BSpline(t, c, k, extrapolate=False)
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
        #plt.figure()
        fig=plt.figure(figsize=(10,4))

        #plt.plot(obstimes, h, 'bo', label='Original points',markersize=3)
        plt.plot(th, h, 'b.', label='Original points',markersize=3)
        # cannot use this because i do not have the year in the tnew variable
        #obstimes = fract_to_obstimes(spl_x)
        plt.plot(spl_x, spl_y, 'r', label='spline')
        plt.title( station.upper() + ' Reflector Heights')
        outlierstring = str(outlierV) + '(m) outliers'
        plt.plot(th[j], h[j], 'c.',label=outlierstring) 
        plt.ylabel('meters',fontsize=fs)
        plt.xlabel('days',fontsize=fs)
        plt.grid()
        plt.gca().invert_yaxis()
        plt.legend(loc="upper left")
        plotname = txtdir + '/' + station + '_rhdot1.png'
        plt.savefig(plotname,dpi=300)
        print('png file saved as: ', plotname)

# take out these points
    th = th[i]; h = h[i]
    xfac = xfac[i]
    resid_spl = resid_spl[i]
    tvd = tvd[i,:]

# taking out first and last six hours as well
    t1 = float(th[0] + 6/24)
    t2 = float(th[-1] - 6/24)
# and again
    i = (th >= t1) & (th <= t2)
    th = th[i]; h = h[i]
    xfac = xfac[i]
    resid_spl = resid_spl[i]
    tvd = tvd[i,:]

    #i = (th <= t2)
    #th = th[i]; h = h[i]
    #xfac = xfac[i]
    #resid_spl = resid_spl[i]
    #tvd = tvd[i,:]

# put the original series without outliers eventually?
# use first diff to get simple velocity.  
# 24 hours a day, you asked for perday values by day
    obsPerHour= perday/24
        
    # these are unreliable at beginning and end of the series for clear reasons
    # these velocities are in meters/hour
    tvel = spl_x[1:N]
    yvel = obsPerHour*np.diff(spl_y)

    rhdot_at_th = np.interp(th, tvel, yvel)
    # this is the RHdot correction. This can be done better - 
    # this is just a start
    correction = xfac*rhdot_at_th
    #  this is where i should do a new spline fit with the corrected RH values
    # h = h - correction

    if pltit:
        fig=plt.figure(figsize=(12,6))
        ax1=fig.add_subplot(311)
        ijk = np.abs(correction) >  1
        plt.plot(th, correction,'b.',label='RHcorr')
        plt.plot(th[ijk], correction[ijk],'rx',label='suspect')
        plt.title('RHdot Correction',fontsize=fs)
        plt.ylabel('m',fontsize=fs);
        plt.grid()
        plt.setp(ax1.get_xticklabels(), visible=False)
        plt.xlim((th[0], th[-1]))

        ax2=fig.add_subplot(312)
        plt.plot(th, rhdot_at_th,'b.',label='at obs')
        plt.plot(tvel[2:-2], yvel[2:-2], '-',color='orange',label='modeled')
        plt.title('RHdot in meters per hour',fontsize=fs)
        plt.ylabel('m/hr',fontsize=fs);
        plt.legend(loc="best")
        plt.grid()
        plt.setp(ax2.get_xticklabels(), visible=False)
        plt.yticks(fontsize=fs); plt.xticks(fontsize=fs)
        plt.xlim((th[0], th[-1]))

        ax3=fig.add_subplot(313)
        label1 = 'w/o RHdot ' + str( round(np.std(resid_spl),2)) + 'm'
        label2 = 'w/ RHdot ' + str(round(np.std(resid_spl-correction),2)) + 'm'
        plt.plot(th, resid_spl,'.',color='orange',label= label1)
        plt.plot(th, resid_spl - correction,'b.',label=label2)
        plt.plot(th[ijk], resid_spl[ijk] - correction[ijk],'rx',label='suspect')
        plt.legend(loc="best")
        plt.xlabel('days of the year',fontsize=fs)
        plt.ylabel('m',fontsize=fs)
        plt.yticks(fontsize=fs); plt.xticks(fontsize=fs)
        plt.title('Reflector Height Residuals to the Spline Fit',fontsize=fs)
        plt.xlim((th[0], th[-1]))
        plt.grid()

        plotname = txtdir + '/' + station + '_rhdot2.png'
        plt.savefig(plotname,dpi=300)
        print('png file saved as: ', plotname)
        plt.show()

    print('RMS no RHdot correction (m)', '{0:6.3f}'.format ( np.std(resid_spl)) )
    print('RMS w/ RHdot correction (m)', '{0:6.3f}'.format ( np.std(resid_spl - correction))  )
    # this is RH with the RHdot correction
    correctedRH = resid_spl - correction
    print('Freq  Bias  Sigma   NumObs ')
    print('       (m)   (m)       ')
    biasCorrected_RH = tvd[:,2] - correction
    for f in [1, 2, 20, 5, 101, 102, 201, 205,207,208]:
        ff = (tvd[:,10] == f)
        ret = correctedRH[ff]
        if len(ret) > 0:
            print('{0:3.0f} {1:6.2f} {2:6.2f} {3:6.0f}'.format (f, np.mean(ret), np.std(ret), len(ret) ) )
            biasCorrected_RH[ff] = biasCorrected_RH[ff] - np.mean(ret)

    writecsv = False; writetxt = True
    extraline = 'outliers removed/two new columns: corrected RH and the RHdot correction applied '
    newRH = tvd[:,2] - correction
    write_subdaily(fname_new,station,tvd,writecsv,extraline,newRH=newRH, RHdot_corr=correction)
    nr,nc = tvd.shape
    print('Percent of observations removed:', round(100*(NV-nr)/NV,2))

    # doy
    newt = tvd[:,1] + tvd[:,4]/24 ; 
    residual = redo_spline(newt, newRH, biasCorrected_RH,pltit,txtdir,station)

    # this is just for kristine
    ntv = tvd
    dtime = False
    kristine = False
    if kristine:
        fout = open('ktest.txt','+w')
        for i in range(0,nr):
            year = int(ntv[i,0]); doy = int(ntv[i,1])
            year, month, day, cyyyy,cdoy, YMD = g.ydoy2useful(year,doy)
            rh = ntv[i,2]; UTCtime = ntv[i,4];
            dob, year, month, day, hour, minute, second = g.ymd_hhmmss(year,doy,UTCtime,dtime)
            fout.write(" {0:4.0f} {1:3.0f} {2:7.3f} {3:3.0f} {4:6.3f} {5:6.2f} {6:6.2f} {7:6.2f} {8:6.2f} {9:4.0f} {10:3.0f} {11:2.0f} {12:8.5f} {13:6.2f} {14:7.2f} {15:12.6f} {16:1.0f} {17:2.0f} {18:2.0f} {19:2.0f} {20:2.0f} {21:2.0f} {22:6.3f} {23:6.3f} {24:6.3f} \n".format(year, doy, rh,ntv[i,3],UTCtime,ntv[i,5],ntv[i,6],ntv[i,7],ntv[i,8], ntv[i,9], ntv[i,10],ntv[i,11], ntv[i,12],ntv[i,13], ntv[i,14], ntv[i,15], ntv[i,16],month,day,hour,minute, int(second), newRH[i], correction[i], residual[i]))
               #ntv[i,10],ntv[i,11], ntv[i,12],ntv[i,13], ntv[i,14], ntv[i,15], ntv[i,16],month,day,hour,minute, int(second), newRH[i], RHdot_corr[i]))
        fout.close()

    return tvd, correction 



def two_stacked_plots(otimes,tv,station,txtdir,year,d1,d2):
    """
    otimes - datetime
    tv = gnssrefl results variable
    station - name just for the title
    txtdir is where the plots will be written to

    author: kristine larson
    """
    if d1 == 1 and d2 == 366:
        # these are the defaults
        setlimits = False
    else:
        setlimits = True
        yyy,mm,dd = g.ydoy2ymd(year, d1)
        th1 = datetime.datetime(year=year, month=mm, day=dd)
        yyy,mm,dd = g.ydoy2ymd(year, d2)
        th2 = datetime.datetime(year=year, month=mm, day=dd)
    # this is not working, so just setting it to false, cause who cares!
    setlimits = False
    fs = 10
    fig,(ax1,ax2,ax3)=plt.subplots(3,1,sharex=True)
    i = (tv[:,10] < 100)
    colors = tv[:,10]
    scatter = ax1.scatter(otimes,tv[:,2],marker='o', s=10, c=colors)
    colorbar = fig.colorbar(scatter, ax=ax1)
    colorbar.set_label('Sat Numbers', fontsize=fs)
    ax1.set_title('Constellation',fontsize=fs)
    plt.xticks(rotation =45,fontsize=fs); 
    ax1.set_ylabel('meters',fontsize=fs)
    plt.yticks(fontsize=fs)
    ax1.invert_yaxis()
    ax1.grid(True)
    fig.suptitle( station.upper() + ' Reflector Heights', fontsize=fs)
    if setlimits:
        ax1.set_xlim((th1, th2))
    fig.autofmt_xdate()



    #fig,(ax1,ax2)=plt.subplots(2,1,sharex=True)
        # put some azimuth information on it
    colors = tv[:,5]
        # ax.plot( otimes, tv[:,2], '.')
        # https://matplotlib.org/stable/gallery/lines_bars_and_markers/scatter_with_legend.html
    scatter = ax2.scatter(otimes,tv[:,2],marker='o', s=10, c=colors)
    colorbar = fig.colorbar(scatter, ax=ax2)
    colorbar.set_label('deg', fontsize=fs)
    ax2.set_ylabel('meters',fontsize=fs)
    ax2.set_title('Azimuth',fontsize=fs)
    #ax1.title.set_text('Azimuth')
    plt.xticks(rotation =45,fontsize=fs); plt.yticks(fontsize=fs)
    ax2.invert_yaxis()
    ax2.grid(True)
    if setlimits:
        ax2.set_xlim((th1, th2))
    fig.autofmt_xdate()

# put some amplitude information on it
    colors = tv[:,6]
    # ax.plot( otimes, tv[:,2], '.')
    # https://matplotlib.org/stable/gallery/lines_bars_and_markers/scatter_with_legend.html
    scatter = ax3.scatter(otimes,tv[:,2],marker='o', s=10, c=colors)
    colorbar = fig.colorbar(scatter, ax=ax3)
    ax3.set_ylabel('meters',fontsize=fs)
    colorbar.set_label('v/v', fontsize=fs)
    plt.xticks(rotation =45,fontsize=fs); plt.yticks(fontsize=fs)
    ax3.set_title('Amplitude',fontsize=fs)
    ax3.invert_yaxis()
    ax3.grid(True)
    if setlimits:
        ax3.set_xlim((th1, th2))
    fig.autofmt_xdate()

    plotname = txtdir + '/' + station + '_combined.png'
    plt.savefig(plotname,dpi=300)
    print('png file saved as: ', plotname)

def stack_two_more(otimes,tv,ii,jj,stats, station, txtdir, sigma):
    """
    otimes - datetime object
    tv - variable with the gnssrefl results
    ii - good data?
    jj - bad data?
    station - for title
    txtdir - where plots will be written
    sigma is constraint used for the outlier detection
 poor man's outlier detector
    """
    fs = 10
    fig = plt.figure()
    colors = tv[:,5]
# put some amplitude information on it
# ax.plot( otimes, tv[:,2], '.')
# https://matplotlib.org/stable/gallery/lines_bars_and_markers/scatter_with_legend.html
    otimesarray = np.asarray(otimes)

    ax1 = fig.add_subplot(211)
    plt.plot(otimes,tv[:,2], '.',color='gray',label='arcs')
    plt.plot(stats[:,0], stats[:,1], '.',markersize=4,color='blue',label='daily avg')
    slabel = str(sigma) + ' sigma'
    plt.plot(stats[:,0], stats[:,1]-sigma*stats[:,2], '--',color='black',label=slabel)
    plt.plot(stats[:,0], stats[:,1]+sigma*stats[:,2], '--',color='black')
    plt.plot(otimesarray[ii],tv[ii,2], 'r.',markersize=4,label='outliers')
    #plt.plot(otimesarray[ii],tv[ii,2], '.',color='red',label='outliers',markersize=12)
    plt.legend(loc="best",bbox_to_anchor=(0.95, 0.9),prop={"size":8})
    plt.ylabel('meters',fontsize=8)
    plt.title(station.upper() + ' Reflector Heights', fontsize=8)
    plt.gca().invert_yaxis()
    plt.xticks(rotation =45,fontsize=8); plt.yticks(fontsize=8)
    plt.grid() ; fig.autofmt_xdate()
    # get the limits so you can use thme on the next plot
    #aaa, bbb = plt.ylim()
    savey1,savey2 = plt.ylim()  

    ax2 = fig.add_subplot(212)
    plt.plot(otimesarray[jj],tv[jj,2], '.',color='green',label='arcs')
    plt.gca().invert_yaxis()
    plt.ylabel('meters',fontsize=8)
    plt.xticks(rotation =45,fontsize=8); plt.yticks(fontsize=8)
    plt.title('Edited Reflector Heights', fontsize=8)
    plt.grid() ; fig.autofmt_xdate()
    plotname = txtdir + '/' + station + '_outliers_hunting.png'
    plt.savefig(plotname,dpi=300)
    plt.ylim((savey1, savey2))
    print('png file saved as: ', plotname)


def apply_new_constraints(tv,azim1,azim2,ampl,peak2noise,d1,d2,h1,h2):
    """
    cleaning up the main code. this sorts data and applies various "commandline" constraints
    tv is the full set of results from gnssrefl
    t and rh are just time (in fractional doy) and reflector height
    other inputs:
    azim1-aimz2 - azimuth constraints in degrees
    ampl is amplitude of the periodogram (volts/volts)
    d1 and d2 are days of year
    peak2noise 
    """
    nr,nc=tv.shape
    tvoriginal = tv
    print('Number of initial RH retrievals', nr)
    nroriginal = nr
    if (nr == 0):
        print('Exiting')
        sys.exit()

    ii = (tv[:,2] <= h2) & (tv[:,2] >= h1)
    tv = tv[ii,:]

    if ((nr-len(tv)) > 0):
        print(nr-len(tv) , ' points removed for reflector height constraints ',h1,h2, ' (m)')

    # not sure these need to be here - are they used elsewhere?
    # could be moved to apply_new_constraints
    
    t=tv[:,0] + (tv[:,1] + tv[:,4]/24)/365.25
    rh = tv[:,2]

# sort the data
    ii = np.argsort(t)
    t = t[ii] ; rh = rh[ii]
    # store the sorted data
    tv = tv[ii,:]

    # apply azimuth constraints
    nr,nc = tv.shape
    ii = (tv[:,5]  >= azim1) & (tv[:,5] <= azim2)
    tv = tv[ii,:]
    print(nr-len(tv) , ' points removed for azimuth constraints ',azim1,azim2)

    # now apply amplitude constraint
    nr,nc = tv.shape
    ii = (tv[:,6]  >= ampl) ; tv = tv[ii,:]
    print(nr-len(tv) , ' points removed for amplitude constraint ')

    # now apply peak2noise constraint
    nr,nc = tv.shape
    ii = (tv[:,13]  >= peak2noise) ; tv = tv[ii,:]
    print(nr-len(tv) , ' points removed for peak2noise constraints ')


    # silly - why read it if you are not going to use it
    # and restrict by doy - mostly to make testing go faster
    ii = (tv[:,1] >= d1) & (tv[:,1] <= d2)
    tv = tv[ii,:]
    firstdoy = int(min(tv[:,1]))
    lastdoy =  int(max(tv[:,1]))

    return tv,t,rh,firstdoy,lastdoy

def redo_spline(tnew,ynew,biasCorr_ynew,pltit,txtdir,station):
    """
    having calculated and applied RHdot correction
    AND applied the frequency biases, create new plots

    parameters
    -------------
    tnew : numpy array
        day of year 
    ynew : numpy array
        float of reflector heights rhdot corrected (meters)
    ynew : numpy array
        float of reflector heights rhdot and freq bias corrected (meters)
    pltit : boolean
        plots to the screen
    txtdir : string
         directory for output (e.g. $REFL_CODE/Files)
    station : string
        station name used for the plot titles and filenames

    returns
    ---------
    res : numpy array
        residuals to spline fit, in meters

    """
    fs = 10 # font size
    ynew = biasCorr_ynew
    # now sort them again ....
    ii = np.argsort(tnew)
    tnew = tnew[ii]
    ynew = ynew[ii]
    outlierV = 0.5 # for now

    # making a knot every three hours ...
    knots_per_day = 8
    Ndays = tnew.max()-tnew.min()
    numKnots = int(knots_per_day*(Ndays))
    NV = len(ynew)
    print('First and last time values', '{0:8.3f} {1:8.3f} '.format (tnew.min(), tnew.max()) )
    print('Number of RH obs', NV)
    print('Number of days of data: ', '{0:8.2f}'.format ( Ndays) )
    print('Average obs per day', '{0:5.1f} '.format (NV/Ndays) )
    print('Number of knots: ', numKnots)
    # need the first and last knot to be inside the time series
    firstKnot_in_minutes = 15
    t1 = tnew.min()+firstKnot_in_minutes/60/24
    t2 = tnew.max()-firstKnot_in_minutes/60/24
    # try this
    #
    knots =np.linspace(t1,t2,num=numKnots)
    try:
        t, c, k = interpolate.splrep(tnew, ynew, s=0, k=3,t=knots,task=-1)
        spline = interpolate.BSpline(t, c, k, extrapolate=False)
    except:
        print('crashed on the interpolation stage')
        sys.exit()

    # user specifies how many values per day you want to send back to the user

    # should i do extrapolate True? it is the default  - could make it periodic?
    #spline = interpolate.BSpline(t, c, k, extrapolate=True)

    # evenly spaced data - units of days
    perday = 48 # so every 30 minutes in this case
    N = int(Ndays*perday)
    xx = np.linspace(tnew.min(), tnew.max(), N)
    spl_x = xx; spl_y = spline(xx)
    spline_at_tnew = spline(tnew)
    N = len(spl_x)
    kristine = False
    if kristine:
        ftest = open('Ktesting.txt', 'w+')
        myyear = 2022
        for i in range(0,N):
            mjdish = g.fdoy2mjd(myyear,spl_x[i])
            ftest.write('{0:9.4f} {1:7.3f} {2:12.6f} \n'.format( spl_x[i], spl_y[i], mjdish))

        ftest.close()
        

    plt.subplot(211)
    plt.plot(tnew,ynew,'k.')
    plt.plot(tnew,biasCorr_ynew,'b.',label='with freq/rhdot corr')
    plt.plot(spl_x, spl_y,'-',color='orange',label='spline fit')
    plt.title(station + ' RH Obs and new spline fit after freq bias removed')

    plt.legend(loc="upper right")
    plt.xlabel('day of year'); 
    plt.ylabel('meters')
    plt.grid()
    plt.gca().invert_yaxis()

    rms = np.std(ynew-spline_at_tnew)
    newrms = str(round(rms,3))
    print('std (m)', newrms)
    ii = np.abs(ynew-spline_at_tnew) > 3*rms
    jj = np.abs(ynew-spline_at_tnew) < 3*rms
    res = ynew-spline_at_tnew
    plt.subplot(212)
    plt.plot(tnew,res,'b.', label='RH rms:' + newrms + ' m')
    plt.plot(tnew[ii],res[ii],'r.',label='3sigma outliers')
    #plt.title('residuals')
    plt.xlabel('day of year'); 
    plt.ylabel('meters')
    plt.legend(loc="upper right")
    plt.grid()
    plt.gca().invert_yaxis()
    Ntot = len(res)
    Nout = len(res[ii])
    print('Percentage of 3-sigma outliers', round(100*Nout/Ntot,2))
    #
    plotname = txtdir + '/' + station + '_final.png'
    plt.savefig(plotname,dpi=300)
    print('png file saved as: ', plotname)
    if pltit:
        plt.show()

    return res

#  should really just mirror it or remove data at the ends
#   going to add more fake data ...
#    first = tnew[0]
#    last = tnew[-1]
#    ii = (tnew <= first + 0.1)
#    jj = (tnew >= last-0.1)
#    first6hours = np.mean(ynew[ii])
#    last6hours = np.mean(ynew[jj])
#    for ii in range(1,6):
#        tnew = np.append(tnew,first-ii/48)
#        ynew = np.append(ynew, first6hours)
#    for ii in range(1,6):
#        tnew = np.append(tnew,last+ii/48)
#        ynew = np.append(ynew, last6hours)


    # now sort them again ....
#   ii = np.argsort(tnew)
#   tnew = tnew[ii]
#   ynew = ynew[ii]

    #ftest = open('testing.txt', 'w+')
    #for i in range(0,len(knots)):
    #    ftest.write('{0:9.4f} \n'.format( knots[i]))
    #ftest.close()
