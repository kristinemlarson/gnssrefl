# codes for subdaily module. primarily for tidal applications
import argparse
import datetime
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import warnings

from datetime import date

# support code
import gnssrefl.gnssir_v2 as guts2
import gnssrefl.gps as g

import gnssrefl.sd_libs as sd


import scipy
import scipy.interpolate as interpolate
from scipy.interpolate import interp1d
import math

#KL trying to move plots and output files to sd_libs.py


def output_names(txtdir, txtfile,csvfile,jsonfile):
    """
    figures out what the names of the outputs are going to be

    Parameters
    ----------
    txtdir : str
        the directory where the results should be written out
    txtfile : str
        name of the output file 
    csvfile : bool
        cl input whether the output file should be csv format
    jsonfile : bool
        cl input for whether the output file should be in the json format

    Returns
    -------
    writetxt : bool
        whether output should be plain txt
    writecsv : bool
        whether output should be csv format
    writejson : bool
        whether output should be json format
    outfile : str
        output filename

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
    writes out the subdaily results. currently only works for plain txt

    >> this code should be moved to the library

    Parameters
    ----------
    input : str
        output filename
    station : str
        4 character station name, lowercase
    nvt : numpy multi-dimensional
        the variable with the LSP results read via np.loadtxt
    writecsv : bool
        whether the file output is csv
    extraline: bool
        whether the header has an extra line

    """
    # this is lazy - should use shape
    RHdot_corr= kwargs.get('RHdot_corr',[])

    newRH = kwargs.get('newRH',[])

    newRH_IF = kwargs.get('newRH_IF',[])

    original = False
    if len(RHdot_corr) + len(newRH) + len(newRH_IF) == 0:
        original = True
        #print('LSP series being written')
    # 
    write_IF_corrected = False
    if len(newRH_IF) > 0:
        print('\nIF corrected values being written - make sure you use the correct column! \n')
        write_IF_corrected = True
    extra = False
    if len(RHdot_corr) > 0:
        print('\nRHdot corrected values being written - make sure you use the correct column \n')
        extra = True

    N= len(ntv)
    nr,nc = ntv.shape
    if nr == 0:
        print('No results in this file, so nothing to write out.')
        return
    print(nr, ' observations will be written to:')
    print(outfile)
    N= nr
    fout = open(outfile, 'w+')
    if extra:
        write_out_header(fout,station,extraline,extra_columns=True)
    else:
        if write_IF_corrected:
            write_out_header(fout,station,extraline, IF=True)
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
            if original:
                fout.write(" {0:4.0f},{1:3.0f},{2:7.3f},{3:3.0f},{4:6.3f},{5:6.2f},{6:6.2f},{7:6.2f},{8:6.2f},{9:4.0f},{10:3.0f},{11:2.0f},{12:8.5f},{13:6.2f},{14:7.2f},{15:12.6f},{16:1.0f},{17:2.0f},{18:2.0f},{19:2.0f},{20:2.0f},{21:2.0f} \n".format(year, doy, rh,ntv[i,3],UTCtime,ntv[i,5],ntv[i,6],ntv[i,7],ntv[i,8], ntv[i,9], ntv[i,10],ntv[i,11], ntv[i,12],ntv[i,13], ntv[i,14], ntv[i,15], ntv[i,16],month,day,hour,minute, int(second)))

            if extra: 
                fout.write(" {0:4.0f},{1:3.0f},{2:7.3f},{3:3.0f},{4:6.3f},{5:6.2f},{6:6.2f},{7:6.2f},{8:6.2f},{9:4.0f},{10:3.0f},{11:2.0f},{12:8.5f},{13:6.2f},{14:7.2f},{15:12.6f},{16:1.0f},{17:2.0f},{18:2.0f},{19:2.0f},{20:2.0f},{21:2.0f},{22:10.3f},{23:10.3f} \n".format(year, doy, rh,ntv[i,3],UTCtime,ntv[i,5],ntv[i,6],ntv[i,7],ntv[i,8], ntv[i,9], ntv[i,10],ntv[i,11], ntv[i,12],ntv[i,13], ntv[i,14], ntv[i,15], ntv[i,16],month,day,hour,minute, int(second), newRH[i],RHdot_corr[i]))
            if write_IF_corrected:
                print('this option (IF correction) has not been implemented yet for csv files')

        else:
            if write_IF_corrected:
                fout.write(" {0:4.0f} {1:3.0f} {2:7.3f} {3:3.0f} {4:6.3f} {5:6.2f} {6:6.2f} {7:6.2f} {8:6.2f} {9:4.0f} {10:3.0f} {11:2.0f} {12:8.5f} {13:6.2f} {14:7.2f} {15:12.6f} {16:1.0f} {17:2.0f} {18:2.0f} {19:2.0f} {20:2.0f} {21:2.0f} {22:10.3f} {23:10.3f} {24:10.3f} \n".format(year, doy, rh,ntv[i,3], 
                    UTCtime,ntv[i,5],ntv[i,6],ntv[i,7],ntv[i,8], ntv[i,9], ntv[i,10],ntv[i,11], 
                    ntv[i,12],ntv[i,13], ntv[i,14], ntv[i,15], ntv[i,16],month,day, hour,minute, 
                    int(second), ntv[i,22], ntv[i,23], newRH_IF[i] ))

            if extra:
                    fout.write(" {0:4.0f} {1:3.0f} {2:7.3f} {3:3.0f} {4:6.3f} {5:6.2f} {6:6.2f} {7:6.2f} {8:6.2f} {9:4.0f} {10:3.0f} {11:2.0f} {12:8.5f} {13:6.2f} {14:7.2f} {15:12.6f} {16:1.0f} {17:2.0f} {18:2.0f} {19:2.0f} {20:2.0f} {21:2.0f} {22:10.3f} {23:10.3f} \n".format(year, doy, rh, ntv[i,3], 
                        UTCtime,ntv[i,5],ntv[i,6],ntv[i,7],ntv[i,8], ntv[i,9], ntv[i,10],ntv[i,11], ntv[i,12],ntv[i,13], ntv[i,14], 
                        ntv[i,15], ntv[i,16],month,day,hour,minute, int(second), newRH[i], RHdot_corr[i]))

            if original:
                fout.write(" {0:4.0f} {1:3.0f} {2:7.3f} {3:3.0f} {4:6.3f} {5:6.2f} {6:6.2f} {7:6.2f} {8:6.2f} {9:4.0f} {10:3.0f} {11:2.0f} {12:8.5f} {13:6.2f} {14:7.2f} {15:12.6f} {16:1.0f} {17:2.0f} {18:2.0f} {19:2.0f} {20:2.0f} {21:2.0f} \n".format(year, doy, rh,ntv[i,3],UTCtime,ntv[i,5],
                    ntv[i,6],ntv[i,7],ntv[i,8], ntv[i,9], ntv[i,10],ntv[i,11], ntv[i,12],ntv[i,13], ntv[i,14], 
                    ntv[i,15], ntv[i,16],month,day,hour,minute, int(second)))
    fout.close()


def readin_and_plot(station, year,d1,d2,plt2screen,extension,sigma,writecsv,azim1,azim2,ampl,
        peak2noise,txtfile,h1,h2,kplt,txtdir,default_usage,hires_figs,fs,**kwargs):
    """
    Reads in RH results and makes various plots to help users assess the quality of the solution

    This is basically "section 1" of the code

    Parameters
    ----------
    station : str
        4 character station name
    year : int
        full year
    d1 : int
        first day of year evaluated
    d2 : int 
        last day of year evaluated
    plt2screen : bool
        if True plots are displayed to the screen
    extension : str
        allow user to specify an extension for results (i.e. gnssir was run using extension string)
    sigma : float
         how many standard deviations away from mean you allow for the crude outlier detector.  
    writecsv : bool
         whether output is written in csv format. 
    azim1 : float
        minimum azimuth value (degrees)
    azim2 : float
        maximum azimuth value (degrees)
    ampl : float
        minimum LSP amplitude allowed
    peak2noise : float
        minim peak2noise value to set solution good
    txtfile : str
        name of plain text output file
    h1 : float
        minimum reflector height (m)
    h2 : float
        maximum reflector height (m)
    kplt : bool
        special plot made 
    txtdir : str
        directory where the results will be written
    default_usage : bool
        flag as to whether you are using this code for subdaily or for rh_plot.
        this changes the plots a bit.
    hires_figs: bool
        whether to switch from png to eps
    fs : int
        fontsize for figure axes

    Returns
    -------
    tv : numpy array
        LSP results (augmented)
    otimes : datetime object 
        times of observations 
    fname : str
        initial result file - colated
    fname_new : str
        result file with outliers removed

    """

    # felipe nievinski alternate definition
    alt_sigma = kwargs.get('alt_sigma', False)
    # fontsize for plot labels and such
    xdir = os.environ['REFL_CODE']
    print('Will remove daily outliers greater than ', sigma, ' sigma')
    if not os.path.exists(txtdir):
        os.makedirs(txtdir)
    print('Plot to the screen has been set to ', plt2screen)

    print('>>>>>>>>>>>>>>>>>>>>>>>> readin RH data <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    if txtfile == '':
        print('Read in the RH retrievals for ', year, ' and these days: ',d1,d2)
        if len(extension) > 0:
            print('Using the results in the ', extension , ' subdirectory.')
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
                    if (day >= d1) & (day <= d2):
                        fname = direc + f
                        try:
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore")
                                a = np.loadtxt(fname,comments='%')
                            if len(a) > 0:
                                tv = np.append(tv, a,axis=0)
                        except:
                            print('some issue with ',fname)

    else:
        print('using external file of concatenated results', txtfile)
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
    real_residuals = np.empty(shape=[0,1])
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
            if alt_sigma:
            # make sigma clipping more robust against outliers:
            # https://en.wikipedia.org/wiki/Median_absolute_deviation#Relation_to_standard_deviation
                rhavg = np.median(tv[ii,2]); 
                rhstd = np.median(abs(tv[ii,2]-rhavg))/0.6745;            
            else:
                rhavg = np.mean(tv[ii,2]); 
                rhstd = np.std(tv[ii,2]); 

            newl = [dtime, rhavg, rhstd]
            stats = np.append(stats, [newl], axis=0)
            if rhstd == 0:
                rhstd = 1
                
            b = ( tv[ii,2] - rhavg*np.ones( len(tv[ii,2]) ))/ rhstd
            bb =  tv[ii,2] - rhavg*np.ones( len(tv[ii,2]) )
            
            residuals = np.append(residuals, b)
            real_residuals = np.append(real_residuals, bb)
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

        minAz = float(np.min(tv[:,5])) ; maxAz = float(np.max(tv[:,5]))

        if default_usage:
            sd.numsats_plot(station,tval,nval,Gval,Rval,Eval,Cval,txtdir,fs,hires_figs,year)
            # was testing some things out
            #testing_nvals(Gval, Rval, Eval, Cval)

            sd.two_stacked_plots(otimes,tv,station,txtdir,year,d1,d2,hires_figs)
            sd.stack_two_more(otimes,tv,ii,jj,stats, station, txtdir,sigma,kplt,hires_figs,year)
            sd.print_badpoints(tv[ii,:],residuals[ii],txtdir,real_residuals[ii])
        else:
            # make both plots cause life is short
            # I do not think this is currently used ... 
            sd.rh_plots(otimes,tv,station,txtdir,year,d1,d2,True)
            sd.rh_plots(otimes,tv,station,txtdir,year,d1,d2,False)

        #plt.show()


    # now write things out - using txtdir variable sent 
    if writecsv: 
        fname =     txtdir  + '/' + station + '_' + str(year) + '_subdaily_all.csv'
        fname_new = txtdir  + '/' + station + '_' + str(year) + '_subdaily_edit.csv'
    else:
        fname =     txtdir  + '/' + station + '_' + str(year) + '_subdaily_all.txt'
        fname_new = txtdir  + '/' + station + '_' + str(year) + '_subdaily_edit.txt'

    extraline = ''

    editedtv = tv[jj,:]
    nr,nc = editedtv.shape

    # write out the initial timeseries which are basically the concatenated values for multiple days
    write_subdaily(fname,station,tvoriginal,writecsv,extraline)

    if default_usage:
        print('Edited observations',nr)
        extraline = 'outliers removed/restrictions'
        write_subdaily(fname_new,station,editedtv,writecsv,extraline)
        NV = len(tvoriginal)
        print('Percent of observations removed: ', round(100*(NV-nr)/NV,2))
    
    # now return the names of the output files ... 

    return tv,otimes, fname, fname_new


def fract_to_obstimes(spl_x):
    """
    this does not seem to be used

    Parameters
    ----------
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

    Parameters
    ----------
    x : numpy of floats
        time of observations in fractional days

    y : numpy of floats
        reflector heights in meters

    knots_per_day : int
        number of knots per day

    Returns
    -------
    xx : numpy of floats
        regularly spaced observations

    spline(xx): numpy of floats
        spline value at those times

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

    Parameters
    ----------
    fout : fileID

    station : str
        4 character station name

    extraline : bool
        not sure why this is here

    """
    extra_columns = kwargs.get('extra_columns',False)
    IFcol = kwargs.get('IF',False)
    xxx = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    fout.write('% Results for {0:4s} calculated on {1:20s} \n'.format(  station, xxx ))
    fout.write('% gnssrefl, https://github.com/kristinemlarson \n')
    if len(extraline) > 0:
        fout.write('% IMPORTANT {0:s} \n'.format(  extraline ))
    fout.write('% Traditional phase center corrections have NOT been applied \n')
    if extra_columns:
        fout.write("% (1)  (2)   (3) (4)  (5)     (6)   (7)    (8)    (9)   (10)  (11) (12) (13)    (14)     (15)    (16) (17) (18,19,20,21,22)    (23)        (24) \n")
        fout.write("% year, doy, RH, sat,UTCtime, Azim, Amp,  eminO, emaxO,NumbOf,freq,rise,EdotF, PkNoise  DelT     MJD  refr  MM DD HH MM SS   RH with      RHdot \n")
        fout.write("%             m       hours   deg   v/v    deg   deg                1/-1       ratio    minute        1/0                    RHdotCorr    Corr m    \n")
    else:
        if IFcol:
            fout.write('% Reflector heights set to the L1-phase center are in column 25 \n')
            fout.write("% (1)  (2)   (3) (4)  (5)     (6)   (7)    (8)    (9)   (10)  (11) (12) (13)    (14)     (15)    (16) (17) (18,19,20,21,22)   (23)      (24)    (25)\n")
            fout.write("% year, doy, RH, sat,UTCtime, Azim, Amp,  eminO, emaxO,NumbOf,freq,rise,EdotF, PkNoise  DelT     MJD  refr  MM DD HH MM SS  RH with    RHdot     RH with  \n")
            fout.write("%             m       hours   deg   v/v    deg   deg                1/-1       ratio    minute        1/0                   RHdotCorr  Corr m    IF Corr  m  \n")
        else:
            fout.write("% (1)  (2)   (3) (4)  (5)     (6)   (7)    (8)    (9)   (10)  (11) (12) (13)    (14)     (15)    (16) (17) (18,19,20,21,22)\n")
            fout.write("% year, doy, RH, sat,UTCtime, Azim, Amp,  eminO, emaxO,NumbOf,freq,rise,EdotF, PkNoise  DelT     MJD  refr  MM DD HH MM SS \n")
            fout.write("%             m       hours   deg   v/v    deg   deg                1/-1       ratio    minute        1/0                  \n")



def apply_new_constraints(tv,azim1,azim2,ampl,peak2noise,d1,d2,h1,h2):
    """
    cleaning up the main code. this sorts data and applies various "commandline" constraints
    tv is the full set of results from gnssrefl

    Parameters
    ----------
    tv : numpy array
        lsp results
    azim1 : float
        min azimuth (deg)
    azim2 : float
        max azimuth (deg)
    ampl : float
        required amplitude for periodogram
    peak2noise : float
        require peak2noise criterion
    d1 : int
        min day of year
    d2 : int
        max day of year
    h1 : float
        min reflector height (m)
    h2 : float
        max reflector height (m)

    Returns
    -------
    tv : numpy array
        edited from input
    t : numpy of floats
        crude time for obs, in fractional days
    rh : numpy of floats
        reflector heights (m)
    firstdoy : int
        first day of year
    lastdoy : int 
        last day of year
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


def flipit(tvd,col):
    """
    take RH values from the first and last day and attaches
    them as fake data to make the spline fit stable.  
    Also fill the temporal gaps with fake data

    Parameters
    ----------
    tvd : numpy array of floats
        output of LSP runs. 
    col : integer
        column number (in normal speak) of the RH results
        in python-speak, this has one subtracted

    Returns
    -------
    tnew : numpy array of floats
        time in days of year
    ynew : numpy array
        RH in meters 

    """
    nr,nc = np.shape(tvd)
    print(nr,nc)
    # sort it just to make sure ...
    tnew = tvd[:,1] + tvd[:,4]/24
    # change from normal columns to python columns
    ynew = tvd[:,col-1]

    # these are in days of the year
    day0= np.floor(tnew[0]) # first day
    dayN = np.ceil(np.max(tnew)) # last day

    # these are the times relative to time zero
    middle = tnew-day0

    # use the first day
    ii = tnew < (day0+1)
    leftTime = -(tnew[ii]-day0)
    leftY = ynew[ii]

    # now use the last day
    ii = tnew > (dayN-1)
    rightY = np.flip(ynew[ii])
    rightTime = tnew[ii] -day0 + 1 

    tmp= np.hstack((leftTime,middle)) ; 
    th = np.hstack((tmp,rightTime))

    tmp = np.hstack((leftY, ynew )) ; 
    h = np.hstack((tmp, rightY))

    # and sort it ...
    ii = np.argsort(th)
    th = th[ii] ; h = h[ii]

    th = th + day0 # add day0 back in

    # now fill the gaps ... 
    fillgap = 1/24 # one hour fake values
    # ???
    gap = 5/24 # up to five hour gap allowed before warning

    tnew =[] ; ynew =[]; faket = [];
    # fill in gaps using variables called tnew and ynew
    Ngaps = 0
    for i in range(1,len(th)):
        d= th[i]-th[i-1] # delta in time in units of days ?
        if (d > gap):
            x0 = th[i-1:i+1] ; h0 = h[i-1:i+1]

            # only print out the gap information the first time thru
            if col == 3:
                print('Gap on doy:', int(np.floor(x0[0])), ' lasting ', round(d*24,2), ' hours ')
            #print(d,x0,h0)
            Ngaps = Ngaps + 1
            f = scipy.interpolate.interp1d(x0,h0)
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


    if (Ngaps > 3) and (col == 3):
        print('\nThis is a beta version of the rhdot/spline fit code - and does not')
        print('work well with gaps. You have been warned!\n')

    # sort again
    ii = np.argsort( tnew) 
    tnew = tnew[ii]
    ynew = ynew[ii]

    return tnew, ynew


def rhdot_correction2(station,fname,fname_new,pltit,outlierV,outlierV2,**kwargs):
    """
    Part two of subdaily.  It computes rhdot correction and interfrequency bias correction for RH 
    time series. This code assumes you have at least removed crude outliers in the previous section of the 
    subdaily code.

    Parameters
    ----------
    station : str
        4 char station name
    fname : list of str
        input filename(s) 
    fname_new : str
        output filename for results
    pltit : bool
        whether you want plots to the screen
    outlierV : float
       outlier criterion, in meters  used in first go thru
       if None, then use 3 sigma (which is the default)
    outlierV2 : float
       outlier criterion, in meters  used in second go thru
       if None, then use 3 sigma (which is the default)
    delta_out : float, optional
        seconds for smooth output
    txtdir : str
        if wanting to set your own output directory
    apply_if_corr : bool, optional
        whether you want to apply the IF correction
        default is true
    apply_rhdot : bool, optional
        whether you want to apply the rhdot correction
        default is true
    gap_min_val : float, optional
        gap allowed in last spline, in hours
    knots2 : int, optional
        a secondary knot value if you want the final output 
        to use a different one than the one used for outliers and 
        RH dot


    """
    # output will go to REFL_CODE/Files unless txtdir provided
    xdir = os.environ['REFL_CODE']

    gap_min_val = kwargs.get('gap_min_val',6.0)
    gap_min_val = gap_min_val/24 # change to DOY units

    val = kwargs.get('txtdir',[])

    if len(val) == 0:
        txtdir = xdir + '/Files/'
    else:
        txtdir = val

    year = kwargs.get('year',0)

    # extension now input
    extension = kwargs.get('extension','')

    delta_out = kwargs.get('delta_out',0)
    if (delta_out  == 0):
        splineout = False
    else:
        splineout = True

    if_corr = kwargs.get('if_corr',True)
    if if_corr:
        apply_if_corr = True
    else:
        apply_if_corr = False

    apply_rhdot  = kwargs.get('apply_rhdot',True)
    if apply_rhdot:
        apply_rhdot_corr = True
    else:
        apply_rhdot_corr = False

    # probably a better way - but this is it for now ....
    gotit = kwargs.get('hires_figs',True)
    if gotit:
        hires_figs = True
        print('Requested high resolution figures')
    else:
        hires_figs = False

    fs = kwargs.get('fs',12)

    #print('output directory: ', txtdir)

#   how often do you want velocity computed (per day)
    perday = 24*20 # so every 3 minutes
    # making a knot every three hours ...
    # knots_per_day = 8
    knots_default = 8
    knots_per_day= kwargs.get('knots',8)


    knots2 = kwargs.get('knots2',knots_per_day)
    if knots2 is None:
        knots2_per_day = knots_per_day
    else:
        knots2_per_day = knots2

    print('knots2 ', knots2_per_day) 

    knots_test = kwargs.get('knots_test',0)
    if (knots_test== 0):
        knots_test = knots_per_day

    print('\n>>>>>>>>>>>>>>>>>>>> Entering second section of subdaily code <<<<<<<<<<<<<<<<<<<<<<<<')
    print('\nComputes rhdot correction and interfrequency bias correction for subdaily')

    # read in the lomb scargle values which are the output of gnssir i.e. the reflector heights
    nfiles = len(fname)
    if nfiles == 1:
        multiyear = False
        print('\nInput filename:', fname[0])
        tvd = np.loadtxt(fname[0],comments='%')
    else:
        multiyear = True
        for i in range(0,nfiles):
            print('\nInput filename:', fname[i])
            newl = np.loadtxt(fname[i], comments='%')
            if i == 0:
                tvd = newl
            else:
                tvd = np.vstack((tvd, newl))

    if len(tvd) == 0:
        print('empty input file')
        return

    print('\nOutput filename: ', fname_new)
    print('\nMinimum gap allowed in spline output, in day units', gap_min_val)

    # sort the data in time
    # 2024-jan-3 change to use MJD
    #ii = np.argsort( (tvd[:,1]+tvd[:,4]/24) ).T
    ii = np.argsort( tvd[:,15] ).T
    tvd = tvd[ii,:]


    if multiyear : 
        # use MJD
        th= tvd[:,15] ; h = tvd[:,2]
        tnew, ynew = flipit2(tvd,3)
    else:
        # use day of year for the spline fits
        th= tvd[:,1] + tvd[:,4]/24; h = tvd[:,2]
        tnew, ynew = flipit(tvd,3)

    # this is the edot factor - 
    # this was computed by gnssir as the mean of the tangent(eangles) over an arc,
    # divided by edot (the time rate of change of elevation angle, initially rad/sec,
    # but then converted to rad/hour).  Thus this parameter has units  rad/(rad/hour) >>>> hours
    # it is multiplied by RHDot in meters/hour, which gives you a correction value in meters
    xfac = tvd[:,12]



    Ndays = tnew.max()-tnew.min()
    numKnots = int(knots_per_day*(Ndays))
    print('First and last time values in the spline', '{0:8.3f} {1:8.3f} '.format (tnew.min(), tnew.max()) )
    print('Number of RH obs and Days ', len(h), np.round(Ndays,3))
    print('Average num of RH obs per day', '{0:5.1f} '.format (len(h)/Ndays) )
    print('Knots per day: ', knots_per_day, ' Number of knots: ', numKnots)
    # currently using 3 sigma
    print('Outlier criterion provided by user for the first splinefit (m):', outlierV)
    print('Outlier criterion provided by user for the second splinefit (m):', outlierV2)


    firstKnot_in_minutes = 15
    t1 = tnew.min()+firstKnot_in_minutes/60/24
    t2 = tnew.max()-firstKnot_in_minutes/60/24
    knots =np.linspace(t1,t2,num=numKnots)

    t, c, k = interpolate.splrep(tnew, ynew, s=0, k=3,t=knots,task=-1)


    spline = interpolate.BSpline(t, c, k, extrapolate=False)
    # this is to get  RHdot, evenly spaced data - units of days
    N = int(Ndays*perday)
    xx = np.linspace(tnew.min(), tnew.max(), N)
    spl_x = xx; spl_y = spline(xx)
    # these are spline values at the RH observation times
    spl_at_GPS_times = spline(th) 

    sd.mirror_plot(tnew,ynew,spl_x,spl_y,txtdir,station,th[0],th[-1])



    plot_begin = np.floor(np.min(th))
    plot_end =np.ceil(np.max(th)) 

    obsPerHour= perday/24


    tvel = spl_x[1:N]
    yvel = obsPerHour*np.diff(spl_y)

    rhdot_at_th = np.interp(th, tvel, yvel)
    # RH dot correction
    correction = xfac*rhdot_at_th

    # 2023 august 25
    if not apply_rhdot :
        print('You requested RHdot correction NOT be applied.')
        correctedRH = h
    else:
    # corrected reflector height
        correctedRH = h-correction

    # this is RH with the RHdot correction
    residual_before = h - spl_at_GPS_times
    residual_after = correctedRH - spl_at_GPS_times
    sigmaBefore = np.std(residual_before)
    sigmaAfter  = np.std(residual_after)

    label1 = 'w/o RHdot ' + str(np.round(sigmaBefore,3)) + 'm'
    label2 = 'w RHdot ' + str(np.round(sigmaAfter,3)) + 'm'

    # start the figure, convert from doy to MJD to obstime
    mjd0 = g.fdoy2mjd(year,th[0])
    th_obs = sd.mjd_to_obstimes(mjd0 + th-th[0])

    if multiyear :
        print('exiting')
        th_obs = sd.mjd_to_obstimes(th)

    fig=plt.figure(figsize=(10,6))
    plt.subplot(2,1,1)
    plt.plot(th_obs, h, 'b.', label=label1,markersize=4)
    iw = (spl_x > th[0]) & (spl_x < th[-1])

    # change to datetime
    if multiyear:
        spl_x_obs = sd.mjd_to_obstimes(spl_x[iw])
        plt.plot(spl_x_obs, spl_y[iw], 'c--', label='spline') # otherwise wonky spline makes a goofy plot
    else:
        tm_mjd = g.fdoy2mjd(year, spl_x[iw][0])
        spl_x_obs = sd.mjd_to_obstimes(tm_mjd + spl_x[iw] - spl_x[iw][0] )
        plt.plot(spl_x_obs, spl_y[iw], 'c--', label='spline') # otherwise wonky spline makes a goofy plot

    plt.plot(th_obs,correctedRH,'m.',label=label2,markersize=4)

    print('\nRMS no RHdot correction (m)', '{0:6.3f}'.format ( sigmaBefore))
    print('RMS w/ RHdot correction (m)', '{0:6.3f} \n'.format ( sigmaAfter ))

    plt.gca().invert_yaxis()
    plt.legend(loc="upper left")
    plt.ylabel('meters',fontsize=fs)
    plt.title( station.upper() + ' Reflector Heights',fontsize=fs)
    outlierstring = str(outlierV) + '(m) outliers'
    plt.yticks(fontsize=fs); plt.xticks(fontsize=fs)
    plt.grid()
    fig.autofmt_xdate()


    plt.subplot(2,1,2)
    plt.plot(th_obs, residual_after,'r.',label='all pts')

    if outlierV is None:
    # use 3 sigma
        OutlierLimit = 3*sigmaAfter
        print('Using three sigma outlier criteria')
    else:
        OutlierLimit = float(outlierV)
        print('User-defined splinefit outlier value (m): ', OutlierLimit)

    tvd_bad = tvd[np.abs(residual_after) >  OutlierLimit, :]
    #tvd_bad = tvd[np.abs(residual_after) >  3*sigmaAfter, :]


    #kk = np.abs(residual_after) > 3*sigmaAfter
    kk = np.abs(residual_after) > OutlierLimit
    tvd_confused = tvd[kk,:]

    sd.writeout_spline_outliers(tvd_confused,txtdir,residual_after[kk],'outliers.spline.txt')

    # keep values within 3 sigma 
    #ii = np.abs(residual_after) < 3*sigmaAfter
    ii = np.abs(residual_after) <= OutlierLimit
    tvd_new = tvd[ii,:]
    correction_new = correction[ii]
    correctedRH_new = correctedRH[ii]
    NV = len(correctedRH)

    plt.plot(th_obs[ii], residual_after[ii],'b.',label='kept pts')
    plt.grid()
    plt.ylabel('meters',fontsize=fs)
    plt.legend(loc="upper left",fontsize=fs)
    plt.yticks(fontsize=fs); plt.xticks(fontsize=fs)
    fig.autofmt_xdate()

    if hires_figs:
        g.save_plot(txtdir + '/' + station + '_rhdot2.eps')
    else:
        g.save_plot(txtdir + '/' + station + '_rhdot2.png')

    # update the residual vector as well
    residual_after = residual_after[ii]

    # make the RHdot plot as well. if multiyear, Skip for now
    if not multiyear:
        sd.rhdot_plots(th,correction,rhdot_at_th, tvel,yvel,fs,station,txtdir,hires_figs,year)

    writecsv = False ; extraline = ''
    # write out the new solutions with RHdot and without 3 sigma outliers
    # this should be changed to take into account apply_rhdot_corr
    write_subdaily(fname_new,station,tvd_new,writecsv,extraline,newRH=correctedRH_new, RHdot_corr=correction_new)
    nr,nc = tvd_new.shape
    print('Percent of observations removed:', round(100*(NV-nr)/NV,2))

    # now make yet another vector - this time to apply bias corrections
    # this is horrible code and needs to be fixed
    biasCorrected_RH = correctedRH_new

    print('----------------------------------------------------------\n')
    print('Check inter-frequency biases for GPS, Glonass, Galileo, and Beidou \n')

    if 1 not in tvd_new[:,10]:
        print('Biases are computed with respect to the average of all constellations')
        L1exist = False
    else:
        print('Biases will be computed with respect to L1 GPS')
        L1exist = True

    tvd_new = np.loadtxt(fname_new,comments='%')
    nr,nc = tvd_new.shape
    onecol = np.zeros((nr,1)) # 

    # add a column for the IF correction
    tvd_new = np.hstack((tvd_new,onecol))
    nr,nc = tvd_new.shape

    print('Freq  Bias  Sigma   NumObs ')
    print('       (m)   (m)       ')
    for f in [1, 2, 20, 5, 101, 102, 201, 205,206,207,208,302,306,307]:
        ff = (tvd_new[:,10] == f)
        ret = residual_after[ff]
        if len(ret) > 0:
            bias = float(np.mean(ret))
            if f == 1: # save this bias
                L1bias = bias
            if L1exist: # apply L1bias so that everything is relative to L1
                bias = bias - L1bias

            tvd_new[ff,24] = tvd_new[ff,22] - bias

            # print stats to the screen
            sig = float(np.std(ret))
            print('{0:3.0f} {1:7.3f} {2:7.3f} {3:6.0f}'.format (f, bias, sig, len(ret) ) )


    if not apply_if_corr:
        print('You chose not to correct for IF biases.')
        print('Since the spline fit is written out after this stage of the ')
        print('code, please submit a pull request to changes the logic. Exiting')
        #if pltit:
        #    plt.show()
        return tvd_new, correction
    print('----------------------------------------------------------\n')

    # now try to write the bias corrected values
    # first attempt was wrong because i forgot to sort the corrected column in biasCorrected_RH
    #bias_corrected_filename = fname_new + 'IF'; extraline = ''; writecsv = False
    biasCor_rh = tvd_new[:,24]
    #write_subdaily(bias_corrected_filename,station,tvd_new, writecsv,extraline, newRH_IF=biasCor_rh)

    # now use the bias corrected value

 
    # add mirror time series at beginning and end of series for spline
    if multiyear:
        th = tvd_new[:,15] # use MJD now
        column = 25 # tells the code which column to use. 
        tnew, ynew = flipit2(tvd_new,column)
    else:
        th = tvd_new[:,1] + tvd_new[:,4]/24 # days of year, fractional
        column = 25 # tells the code which column to use. 
        tnew, ynew = flipit(tvd_new,column)

    Ndays = tnew.max()-tnew.min()
    print('trying knots2')
    knots_per_day = knots2_per_day

    numKnots = int(knots_per_day*(Ndays))
    #

    firstKnot_in_minutes = 15
    t1 = tnew.min()+firstKnot_in_minutes/60/24
    t2 = tnew.max()-firstKnot_in_minutes/60/24
    knots =np.linspace(t1,t2,num=numKnots)


    t, c, k = interpolate.splrep(tnew, ynew, s=0, k=3,t=knots,task=-1)
    # compute spline - use for times th
    spline = interpolate.BSpline(t, c, k, extrapolate=False)

    # calculate spline values at GPS time tags
    spline_at_GPS = spline(th)
    # for the plot I did 30 minutes - but that is not the same as what
    # is used for the final output.  Might as well have them be the same
    half_hourly = int(48*(th[-1] - th[0]))
    # evenly spaced spline values for the plot
    # I do not think these variables are used anymore

    #print(th[0], th[-1], half_hourly)
    th_even = np.linspace(th[0], th[-1],half_hourly ); 
    spline_whole_time = spline(th_even)

    newsigma = np.std(biasCor_rh-spline_at_GPS)
    strsig = str(round(newsigma,3)) + '(m)'

    if outlierV2 is None:
        # use 3 sigma to find outliers
        OutlierLimit = 3*sigmaAfter
        print('Using three sigma outlier criteria')
        ii = np.abs(biasCor_rh -spline_at_GPS)/newsigma > 3
        jj = np.abs(biasCor_rh -spline_at_GPS)/newsigma <= 3
    else:
        OutlierLimit = float(outlierV2)
        print('User-defined splinefit outlier value (m): ', OutlierLimit)
        # throw out
        ii = np.abs(biasCor_rh -spline_at_GPS) > OutlierLimit
        # points to keep
        jj = np.abs(biasCor_rh -spline_at_GPS) <= OutlierLimit

    
    # make the plot externally now
    badpoints2 = sd.subdaily_resids_last_stage(station, year, th, biasCor_rh, spline_at_GPS, 
                                               fs, strsig, hires_figs,txtdir, ii,jj,th_even, spline_whole_time)
    H0 = sd.find_ortho_height(station,extension)
    # this writes out spline file and makes plot .... 
    sd.RH_ortho_plot2( station, H0, year, txtdir, fs, th[jj],biasCor_rh[jj],gap_min_val,th,spline,delta_out)
    print('\nRMS with frequency biases and RHdot taken out (m) ', np.round(newsigma,3) , '\n' )


    # write out the files with RH dot and IF bias corrected - and again without 3 sigma outliers
    bias_corrected_filename = fname_new + 'IF'; extraline = ''; writecsv = False
    biasCor_rh = tvd_new[jj,24]
    write_subdaily(bias_corrected_filename,station,tvd_new[jj,:], writecsv,extraline, newRH_IF=biasCor_rh)

    new_outliers = tvd_new[ii,:]

    # write outliers to a file ... again ... 
    sd.writeout_spline_outliers(new_outliers,txtdir,badpoints2,'outliers.spline2.txt')


    return tvd, correction


def my_percentile(rh,p1, p2):
    """
    numpy percentile was crashing docker build
    this is a quick work around

    Parameters
    ----------
    rh : numpy array
        reflector heights, but could be anything really
    p1 : float
        low percentage (from 0-1)
    p2 : float
        high percentage (from 0-1)

    Returns
    -------
    low : float
        low value (using input percentile)
    highv : float
        high value (using input percentile)

    """

    sorted_rh = np.sort(rh)
    N = len(sorted_rh)
    N1 = int(np.round(p1*N))
    N2 = int(np.round(p2*N))

    # calculate the low and high values at these percentiles
    lowv = sorted_rh[N1] 
    highv = sorted_rh[N2]

    return  lowv, highv

def flipit2(tvd,col):
    """
    take RH values from the first and last day and attaches
    them as fake data to make the spline fit stable.  
    Also fill the temporal gaps with fake data

    This version uses MJD rather than day of year for x-axis

    Parameters
    ----------
    tvd : numpy array of floats
        output of LSP runs. 
    col : integer
        column number (in normal speak) of the RH results
        in python-speak, this has one subtracted

    Returns
    -------
    tnew : numpy array of floats
        time in days of year
    ynew : numpy array
        RH in meters 

    """
    nr,nc = np.shape(tvd)
    #print(nr,nc)
    # sort it just to make sure ...
    #tnew = tvd[:,1] + tvd[:,4]/24
    # use MJD
    tnew = tvd[:,15]
    # change from normal columns to python columns
    ynew = tvd[:,col-1]

    # these are in days of the year
    day0= np.floor(tnew[0]) # first day
    dayN = np.ceil(np.max(tnew)) # last day

    # these are the times relative to time zero
    middle = tnew-day0

    # use the first day
    ii = tnew < (day0+1)
    leftTime = -(tnew[ii]-day0)
    leftY = ynew[ii]

    # now use the last day
    ii = tnew > (dayN-1)
    rightY = np.flip(ynew[ii])
    rightTime = tnew[ii] -day0 + 1 

    tmp= np.hstack((leftTime,middle)) ; 
    th = np.hstack((tmp,rightTime))

    tmp = np.hstack((leftY, ynew )) ; 
    h = np.hstack((tmp, rightY))

    # and sort it ...
    ii = np.argsort(th)
    th = th[ii] ; h = h[ii]

    th = th + day0 # add day0 back in

    # now fill the gaps ... 
    fillgap = 1/24 # one hour fake values
    # ???
    gap = 5/24 # up to five hour gap allowed before warning

    tnew =[] ; ynew =[]; faket = [];
    # fill in gaps using variables called tnew and ynew
    Ngaps = 0
    for i in range(1,len(th)):
        d= th[i]-th[i-1] # delta in time in units of days ?
        if (d > gap):
            x0 = th[i-1:i+1] ; h0 = h[i-1:i+1]

            # only print out the gap information the first time thru
            if col == 3:
                print('Gap on MJD:', int(np.floor(x0[0])), ' lasting ', round(d*24,2), ' hours ')
            #print(d,x0,h0)
            Ngaps = Ngaps + 1
            f = scipy.interpolate.interp1d(x0,h0)
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


    if (Ngaps > 3) and (col == 3):
        print('\nThis is a beta version of the rhdot/spline fit code - and does not')
        print('work well with gaps. You have been warned!\n')

    # sort again
    ii = np.argsort( tnew) 
    tnew = tnew[ii]
    ynew = ynew[ii]

    return tnew, ynew

