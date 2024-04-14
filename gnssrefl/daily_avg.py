# library for daily_avg_cl.py
import argparse
import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import warnings
import time

from datetime import date

# my code
import gnssrefl.gps as g
import gnssrefl.sd_libs as sd
#

def fbias_daily_avg(station):
    """
    reads QC-RH values and the daily averages
    computes residuals and estimate the frequency
    bias for all available frequencies which is printed to the screen

    Parameters
    ----------
    station : str
        station name - 4char - lowercase

    """
    xdir = os.environ['REFL_CODE']

    fname =  xdir + '/Files/' + station + '_dailyRH.txt'
    if os.path.exists(fname):
        tv = np.loadtxt(fname,comments='%')
        if len(tv) == 0:
            print('No results. Exiting.')
            return
    else:
        print('no input', fname)
        return

    fname =  xdir + '/Files/' + station + '_allRH.txt'
    if os.path.exists(fname):
        tvall = np.loadtxt(fname,comments='%')
        if len(tvall) == 0:
            print('No results. Exiting.')
            return
    else:
        print('no input', fname)
        return


# start and end year
    minyear = int(min(tv[:,0])) ; maxyear = int(max(tv[:,0]))
    print('begin/end year: ', minyear, maxyear)
# list of hte frequencies used

    flist = np.unique(tvall[:,6])

    if len(flist) == 0:
        print('There are no results.')
        return

    if len(flist) == 1:
        print('There is only one frequency in this file, so there is no point to computing a frequency bias.')
        return

    # loop thru the frequencies
    for ifr in range(0,len(flist)):
        ijk = 0
        dd = []
        # look thru the years
        for y in range(minyear,maxyear+1):
            ii = (tv[:,0] == y)
            thisyear = tv[ii,:]
            ii = (tvall[:,0] == y)
            thisyearAll = tvall[ii,:]
            # and the days
            for d in range(1, 367):
                kk = (thisyear[:,1] == d);
                N = len(thisyear[kk,1])
                if (N == 1): # found a result on this day
                    RH = thisyear[kk,2]
                    k3 = (thisyearAll[:,1] == d);
                    NAll = len(thisyearAll[k3,1])
                    tt = thisyearAll[k3,1]/365.25 + thisyearAll[k3,0]
                    f= thisyearAll[k3,6]
                    residual =  thisyearAll[k3,2] - RH
                    vv = (f == flist[ifr])
                    if (len(residual[vv]) > 0):
                        avg = np.mean(residual[vv])
                        dd.append(avg)
        print(" Frequency %3.0f %8.3f m " % (int(flist[ifr]), np.mean(dd)) )
        ijk = ijk + 1



def readin_plot_daily(station,extension,year1,year2,fr,alldatafile,csvformat,
        howBig,ReqTracks,azim1,azim2,test,subdir,plot_limits):
    """
    worker code for daily_avg_cl.py

    It reads in RH files created by gnssir. Applies median filter and saves average results 
    for further analysis

    if there is only one RH on a given day - there is no median value and thus nothing will 
    be saved for that day.  

    Parameters
    ----------
    station : str
        station name, 4 ch, lowercase

    extension : str
        folder extension - usually empty string 

    year1 : integer
        first year

    year2 : integer
        last year 

    fr : integer
        0 for all frequencies.  otherwise, it must be a legal frequency (101 for Glonass L1)

    alldatafile : str
        name of the output filename

    csvformat : boolean
        whether you want output as csv format

    howBig : float
        criterion for the median filter, i.e. how far in meters 
        can a RH be from the median for that day, in meters

    ReqTracks : integer
        is the number of retrievals required per day

    azim1 : integer
        minimum azimuth, degrees

    azim2 : integer
        maximum azimuth, degrees

    test: bool

    subdir : str
        subdirectory for output files

    subdir : bool
        whether plot limits for the median filter are shown

    Returns
    -------
    tv : numpy array
        with these values [year, doy, meanRHtoday, len(rh), month, day, stdRH, averageAmplitude]
        len(rh) is the number of RH on a given day
        stdRH is the standard deviation of the RH values (meters)
        averageAmplitude is in volts/volts

    obstimes : list of datetime objects 
        observation times

    """
    print('Median Filter', howBig, ' Required number of tracks/day ', ReqTracks)
    xdir = os.environ['REFL_CODE']
    print('All RH retrievals - including bad ones - will be written to: ' )
    alldatafile2 = alldatafile + '.noqc'
    print(alldatafile2, '\n')

    noqc = open(alldatafile2, 'w+')
    # put in a header
    noqc.write(" {0:s}  \n".format('% NO QUALITY CONTROL AT ALL' ))
    noqc.write(" {0:s}  \n".format('% year,doy, RH(m),Mon, Day, Azim, freq,sat,LSPamp,pk2n,UTC(hr)' ))
    noqc.write(" {0:s}  \n".format('% (1), (2), (3),  (4), (5),  (6), (7), (8), (9),   (10), (11)' ))


    print('All RH retrievals that meet your median filter and ReqTracks criteria will be written to: ' )
    print(alldatafile, '\n')
    allrh = open(alldatafile, 'w+')
    # put in a header
    allrh.write(" {0:s}  \n".format('% year,doy,RH(m),Mon,day, azim,freq,sat,LSPamp,pk2n,UTC(hr)' ))
    allrh.write(" {0:s}  \n".format('% (1), (2),(3), (4),(5),  (6), (7), (8), (9),  (10), (11)' ))

    fs = 12
    NotEnough = 0
    tv = np.empty(shape=[0, 8])
    tv_median = np.empty(shape=[0, 9])
    tvall = np.empty(shape=[0, 7])
    tv_list = []
    tv_median_list = []
    #
    ngps = []; nglo = [] ; ngal = []; nbei = []
    obstimes = []; medRH = []; meanRH = [] ; alltimes = []; meanAmp = []
    tttimes = []
    fig,ax=plt.subplots()
    year_list = np.arange(year1, year2+1, 1)
    NumFiles = 0
    test_alltimes = []
    test_good = []
    s1 = time.time()
    for yr in year_list:
        direc = xdir + '/' + str(yr) + '/results/' + station + '/' + extension + '/'
        # counter for the legends
        nle = 0
        # i understand why python people like this - but then the results are not sorted ...
        if os.path.isdir(direc):
            all_files = os.listdir(direc)
            all_files = np.sort(all_files)
            #print('Number of files in ', yr, len(all_files))
            for f in all_files:
                fname = direc + f
                L = len(f)
        # file names must have 7 characters in them ...  and end in txt for that matter
                if (L == 7):
                    NumFiles +=  1
        # check that it is a file and not a directory and that it has something/anything in it
                    try:
                        # trying to turn off the annoying empty file warnings
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            a = np.loadtxt(fname,skiprows=3,comments='%')
                        nr,nc=a.shape
                        if (nr > 0):
                            nle = nle + 1
                            # add the new azimuth constraint here ... 2022sep04
                            www = (a[:,5] > azim1 ) & (a[:,5] < azim2 )
                            a = a[www,:]

                            y = a[:,0] +a[:,1]/365.25; rh = a[:,2] ; 
                            frequency = a[:,10]; azimuth = a[:,5]; sat = a[:,3]; amplitude=a[:,6]
                            # added utc to the all RH file
                            utcTime = a[:,4]; 
                            yr = int(a[0,0]); doy = int(a[0,1])
                            d = datetime.date(yr,1,1) + datetime.timedelta(doy-1)
                            peak2noise = a[:,13]

                            medv = np.median(rh)
                            # 0 means use all frequencies.  otherwise, you can specify 
                            # this is applying the medial filter
                            if fr == 0:
                                cc = (rh < (medv+howBig))  & (rh > (medv-howBig))
                            else:
                                cc = (rh < (medv+howBig))  & (rh > (medv-howBig)) & (frequency == fr)
                            good =rh[cc]; goodT =y[cc]; goodAmp = amplitude[cc]
                            gazim = azimuth[cc]; gsat = sat[cc]; gamp = amplitude[cc]; gpeak2noise = peak2noise[cc]
                            gfreq = frequency[cc]
                            # added 21may14
                            gutcTime = utcTime[cc]

                            # write out everyting including bad retrievals
                            dumb= write_out_all(noqc, csvformat, len(rh), yr, doy, d, rh, azimuth, frequency, sat,amplitude,peak2noise,utcTime,[])
                            
                            # tvall no longer being used as a variable but still sending it to the function.
                            # unfortunately the info is not sorted - because of the way the directory listing works....
                            NG = len(good)

        # only save if there are some minimal number of values
                            if (len(good) >= ReqTracks):

                                # write out the individual tracks that made your met your QC metrics ...
                                tvall = write_out_all(allrh, csvformat, NG, yr, doy, d, good, gazim, gfreq, gsat,gamp,gpeak2noise,gutcTime,tvall)

                                rh = good
                                # this is the plot with all the data -not the daily average
                                alltimes = []

                                # put in the real time (as opposed to just year,month day)
                                #filler = datetime.datetime(year=yr, month=d.month, day=d.day, hour = hrr, minute=mm, second = ss)
                                for w in range(0,len(good)):
                                    hrr = int(np.floor(gutcTime[w])) # 
                                    mm = int(60*(gutcTime[w] - hrr )); ss = 0
                                    filler = datetime.datetime(year=yr, month=d.month, day=d.day, hour = hrr, minute=mm, second = ss)
                                    alltimes.append(filler)
                                # 
                                # this probably should not be inside the loop
                                # maybe this makes it slow? will try accumulating it all and plot outside the loop
                                #test_alltimes.append(alltimes)
                                #test_good.append(good)

                                ax.plot(alltimes,good,'b.')

                                # this are stats for the daily averages - is this slowing it down? - apparently not
                                # turned off for now
                                if True:
                                    ijk = (gsat  < 100); 
                                    ngps = np.append(ngps, len(gsat[ijk]))

                                    ijk = (gsat  > 300);  # beidou
                                    nbei = np.append(nbei, len(gsat[ijk]))
   
                                    ijk = (gsat > 100) * (gsat < 200);  # glonass
                                    nglo = np.append(nglo, len(gsat[ijk]))

                                    ijk = (gsat > 200) * (gsat < 300); # galileo
                                    ngal = np.append(ngal, len(gsat[ijk]))

                                obstimes.append(datetime.datetime(year=yr, month=d.month, day=d.day, hour=12, minute=0, second=0))

                                medRH.append(medv)
                                #medRH =np.append(medRH, medv)
                                # store the meanRH after the outliers are removed using simple median filter
                                meanRHtoday = np.mean(good)

                                stdRHtoday = np.std(good)
                                #meanRH =np.append(meanRH, meanRHtoday)
                                #
                                # july 7, 2022
                                meanRH.append(meanRHtoday)
                                #meanAmp = np.append(meanAmp, np.mean(goodAmp))
                                # updated this to include mean amplitude 2021 november 8
                                meanAmp.append(np.mean(goodAmp))
                                newl = [yr, doy, meanRHtoday, len(rh), d.month, d.day, stdRHtoday, np.mean(goodAmp)]
                                # a new variable is not really needed - but I did not want to oerwrite working code
                                newl_plus_median = [yr, doy, meanRHtoday, len(rh), d.month, d.day, stdRHtoday, np.mean(goodAmp),medv]

                                # maybe this is slow??
                                #tv = np.append(tv, [newl],axis=0)
                                #tv_median = np.append(tv_median, [newl_plus_median],axis=0)
                                # see if this works
                                tv_list.append(newl)
                                tv_median_list.append(newl_plus_median)

                                k += 1
                            else:
                                NotEnough = NotEnough + 1
                    except:
                        okok = 1;
            #ax.plot(test_alltimes,test_good,'b.')
        else:
            abc = 0; # dummy line
    #meanRH = np.asarray(meanRH)

    s2 = time.time()
    #print(s2-s1, ' seconds')
    tv = np.asarray(tv_list)
    tv_median = np.asarray(tv_median_list)

    # not sure you can sort obstimes
    dumb_time = tv_median[:,0] + tv_median[:,1]/365.25
    # sort it ...
    ii = np.argsort(dumb_time)
    tv_median = tv_median[ii,:]
    # i have a function for this now - though it asks for MJD
    for www in range(0,len(tv_median)):
        filler = datetime.datetime(year=int(tv_median[www,0]), 
                month=int(tv_median[www,4]), day=int(tv_median[www,5]), hour = 12, minute=0, second = 0)
        tttimes.append(filler)

    # plot the median 
    #ax.plot(tttimes, tv_median[:,8],'k.',label='median value')
    ax.plot(tttimes, tv_median[:,8],'ks',markerfacecolor='white',label='median value',markersize=4)
    # if requested, also show the limits for the median filter
    if plot_limits:
        ax.plot(tttimes, tv_median[:,8]+howBig,'-',color='gray',label='median+limit')
        ax.plot(tttimes, tv_median[:,8]-howBig,'-',color='gray',label='median-limit')

    plt.ylabel('meters',fontsize=fs)
    plt.title('All Reflector Heights for ' + station.upper() + ' when QC is applied: ' ,fontsize=fs)
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)
    plt.gca().invert_yaxis()
    # this command changes the x-axis
    fig.autofmt_xdate()
    #plt.legend(loc="upper right")
    plt.legend(loc="best")
    plt.grid()

    print('A total of ', NumFiles, ' days were evaluated.')
    print( NotEnough, ' days did not meet the threshold set for a dependable daily average')
    if NumFiles > 1:
        pltname = xdir + '/Files/' + subdir + '/' + station + '_AllRH.png'
        print('All RH png file saved as: ', pltname)
        plt.savefig(pltname)


    # close the all RH output files
    allrh.close()
    noqc.close()

    # quick plot of the results without QC
    quick_raw(alldatafile2,xdir, station,subdir)

    # plot the number of retrievals vs time
    txtdir =  xdir + '/Files/' + subdir 
    nr,nc = tv.shape
    if (nr > 0) & (NumFiles > 1):
        daily_avg_stat_plots(obstimes,meanRH,meanAmp, station,txtdir,tv,ngps,nglo,ngal,nbei,test)

    return tv, obstimes

def quick_raw(alldatafile2,xdir,station,subdir):
    """
    quick plot of the raw RH data.  No QC

    Parameters
    ----------
    alldatafile2 : str
        name of the raw file to be read
    xdir : str
        code environ variable (I think)
    station : str
        4 ch station name
    subdir : str
        subdirectory name for results in xdir/Files

    """
    if os.path.exists(alldatafile2):
       # turn off warning
       with warnings.catch_warnings():
           warnings.simplefilter("ignore")
           raw = np.loadtxt(alldatafile2,comments='%')
       if len(raw) == 0:
           print('There are no RH data.  At all.  Exiting')
           sys.exit()

       ns= len(raw.shape)
       if ns == 2:
           nr,nc = raw.shape
       elif ns == 1:
           nr = 1

       if ns > 0:
           plt.figure()
           plt.plot(raw[:,0] + raw[:,1]/365.25, raw[:,2], 'b.')
           plt.grid()
           plt.xlabel('year')
           plt.ylabel('reflector height (m)')
           plt.title(station + ': Completely raw RH data ... no QC applied ')
           pltname = xdir + '/Files/' + subdir + '/' + station + '_AllRH_noQC.png'
           plt.savefig(pltname)
           print('All RH png file without QC saved as: ', pltname)


def daily_avg_stat_plots(obstimes,meanRH,meanAmp, station,txtdir,tv,ngps,nglo,ngal,nbei,test):
    """
    plots of results for the daily avg code
      
    Parameters
    ----------
    obstimes : datetime object 

    meanRH : numpy array
        daily averaged Reflector Height values in meters

    meanAmp : numpy array
        daily average RH amplitude

    station : str
        4 character station name

    txtdir : str
        directory for the results

    tv : ??
         is the variable of daily results

    ngps : numpy array
        number of gps satellites each day

    nglo : numpy array
        number of glonass satellites each day

    ngal : numpy array
        number of galileo satellites each day

    nbei : numpy array
        number of beidou satellites each day

    test : bool

    """
#   new plot

    fs = 12 # fontsize
    fig,ax=plt.subplots()
    ax.plot(obstimes,meanRH,'b.')
    fig.autofmt_xdate()
    plt.ylabel('Reflector Height (m)',fontsize=fs)
    today = str(date.today())
    #plt.title(station.upper() + ': Daily Mean Reflector Height, Computed ' + today,fontsize=fs)
    plt.title(station.upper() + ': Daily Mean Reflector Height',fontsize=fs)
    plt.grid()
    plt.xticks(fontsize=fs); plt.yticks(fontsize=fs)

    plt.gca().invert_yaxis()
    pltname = txtdir + '/' + station + '_RH.png'
    plt.savefig(pltname)
    print('Daily average RH png file saved as: ', pltname)

    minyear = int(np.min(tv[:,0])); maxyear = int(np.max(tv[:,0]))
    maxA = np.max(meanAmp); minA = np.min(meanAmp)
    #print(minyear,maxyear,minA,maxA)
    fig,ax=plt.subplots()
    ax.plot(obstimes,meanAmp,'b.',label='Amplitude')
    
    # 
    if test:
        for dy in range(minyear, maxyear+1):
            d1 = datetime.datetime(year=dy, month =11, day = 1)
            d2 = datetime.datetime(year=dy, month =6, day = 1)
            if dy == minyear:
                ax.plot([d1, d1], [minA, maxA], 'k-',label='Nov 1')
                ax.plot([d2, d2], [minA, maxA], 'k--',label='Jun 1')
            else:
                ax.plot([d1, d1], [minA, maxA], 'k-')
                ax.plot([d2, d2], [minA, maxA], 'k--')

        plt.legend(loc="upper left")

    fig.autofmt_xdate()
    plt.ylabel('Amplitude (v/v)',fontsize=fs)
    today = str(date.today())
    #plt.title(station.upper() + ': Daily Mean Reflection Amplitude, Computed ' + today,fontsize=fs)
    plt.title(station.upper() + ': Daily Mean Reflection Amplitude', fontsize=fs)
    plt.grid()
    plt.xticks(fontsize=fs); plt.yticks(fontsize=fs)
    pltname = txtdir + '/' + station + '_RHamp.png'
    plt.savefig(pltname)
    print('Daily average RH amplitude file saved as: ', pltname)


    # added constellation specific info
    fig,ax=plt.subplots()
    plt.plot(obstimes, tv[:,3],'k.',label='Total',markersize=3)
    if (np.sum(ngps) > 0):
        plt.plot(obstimes, ngps,'b.',label='GPS',markersize=3)
    if (np.sum(nglo) > 0):
        plt.plot(obstimes, nglo,'r.',label='GLO',markersize=3)
    if (np.sum(ngal) > 0):
        plt.plot(obstimes, ngal,'.',label='GAL',color='orange',markersize=3)
    if (np.sum(nbei) > 0):
        plt.plot(obstimes, nbei,'.',label='BEI',color='green',markersize=3)

    #plt.legend(loc="upper left")
    #ax.legend(bbox_to_anchor=(1.02, 1.02))
    plt.legend(loc="best")
    fig.autofmt_xdate()
    plt.title(station.upper() + ': Number of values used in the daily average',fontsize=fs)
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)
    plt.grid()
    pltname = txtdir + '/' + station + '_nvals.png'
    plt.savefig(pltname)
    print('Number of values used in average RH file saved as: ', pltname)


def write_out_RH_file(obstimes,tv,outfile,csvformat,station,extension):
    """
    write out the daily average RH values 

    Parameters
    ----------
    obstimes : datetime object
        time of observation
    tv : numpy array
        content of a LSP results file
    outfile : string
        full name of output file
    csvformat : boolean
        true if you want csv format output
    station : str
        4 ch station name
    extension : str, optional
        analysis extension name

    """
    # ignore extension for now
    Hortho = sd.find_ortho_height(station,extension)
    # sort the time tags
    nr,nc = tv.shape
    # nothing to write 
    if (nr < 1):
        return
    print('\nDaily average RH file written to: ', outfile)
    ii = np.argsort(obstimes)
    # apply time tags to a new variable
    ntv = tv[ii,:]
    N,M = np.shape(ntv)
    xxx = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    fout = open(outfile, 'w+')
    #  header of a sorts
    # change comment value from # to %
    # 2021 november 8 added another column that has mean amplitude
    # 2024 march 10 added a column with orthometric height
    fout.write("{0:48s} \n".format( '% station:' + station + ' calculated on ' + xxx ))
    fout.write("% Daily average reflector heights (RH) calculated using the gnssrefl software \n")
    fout.write("% Nominally you should assume this average is associated with 12:00 UTC hours \n")
    fout.write("% year doy   RH    numval month day RH-sigma RH-amp  Hortho-RH\n")
    fout.write("%            (m)                       (m)    (v/v)     (m) \n")
    fout.write("% (1)  (2)   (3)    (4)    (5)  (6)   (7)     (8)       (9) \n")

    # these print statements could be much smarter
    if csvformat:
        for i in np.arange(0,N,1):
            dv = Hortho - ntv[i,2]
            fout.write(" {0:4.0f},  {1:3.0f},{2:7.3f},{3:3.0f},{4:4.0f},{5:4.0f},{6:7.3f},{7:6.2f},{8:7.3f} \n".format(ntv[i,0], 
                ntv[i,1], ntv[i,2],ntv[i,3],ntv[i,4],ntv[i,5],ntv[i,6],ntv[i,7],dv ))
    else:
        for i in np.arange(0,N,1):
            dv = Hortho - ntv[i,2]
            fout.write(" {0:4.0f}   {1:3.0f} {2:7.3f} {3:3.0f} {4:4.0f} {5:4.0f} {6:7.3f} {7:6.2f} {8:7.3f} \n".format(ntv[i,0], 
                ntv[i,1], ntv[i,2],ntv[i,3],ntv[i,4],ntv[i,5],ntv[i,6], ntv[i,7],dv))
    fout.close()


def write_out_all(allrh, csvformat, NG, yr, doy, d, good, gazim, gfreq, gsat,gamp,gpeak2noise,gutcTime,tvall ):
    """
    writing out all the RH retrievals to a single file: file ID is allrh)
    tvall had everything in it,  but it was slowing everything down, so i do not do anything with it.

    Parameters
    ----------
    allrh : fileID for writing

    csvformat : bool
        whether you are writing to csv file

    NG : int
        number of lines of results

    yr : int
        year

    doy : int
        day of year

    d : datetime object

    good : float
        reflector height - I think

    gazim : numpy array of floats
        azimuths

    gfreq : numpy array of int
        frequencies

    gsat : numpy array of int
        satellite numbers

    gamp : numpy array of floats
        amplitudes of periodograms

    gpeak2noise : numpy array of floats
        peak 2 noise for periodograms

    gutcTime : numpy array of floats
        time of day in hours 

    tvall :  ??

    Returns
    -------
    tvall : ??

    """
    if (NG > 0):
        # don't really need MM and DD, but ...
        if csvformat:
            for ijk in range(0,NG):
                biggerline = [yr, doy, good[ijk],d.month, d.day, gazim[ijk], gfreq[ijk]]
                #tvall = np.append(tvall, [biggerline],axis=0)
                allrh.write(" {0:4.0f},  {1:3.0f},{2:7.3f}, {3:2.0f}, {4:2.0f},{5:6.1f},{6:4.0f},{7:4.0f},{8:6.2f},{9:6.2f},{10:6.2f}\n".format(yr, doy, good[ijk],d.month, d.day, gazim[ijk], gfreq[ijk], gsat[ijk],gamp[ijk],gpeak2noise[ijk], gutcTime[ijk]))
        else:
            for ijk in range(0,NG):
                biggerline = [yr, doy, good[ijk],d.month, d.day, gazim[ijk], gfreq[ijk]]
                #print(biggerline)
                #tvall = np.append(tvall, [biggerline],axis=0)
                allrh.write(" {0:4.0f}   {1:3.0f} {2:7.3f} {3:2.0f} {4:2.0f} {5:6.1f} {6:4.0f} {7:4.0f} {8:6.2f} {9:6.2f} {10:6.2f}\n".format(yr, doy, good[ijk],d.month, d.day, gazim[ijk], gfreq[ijk], gsat[ijk],gamp[ijk],gpeak2noise[ijk],gutcTime[ijk]))


    return tvall
