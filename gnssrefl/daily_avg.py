# library for daily_avg_cl.py
# Kristine Larson May 2019
import argparse
import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import warnings

from datetime import date

# my code
import gnssrefl.gps as g
#
# changes to output requested by Kelly Enloe for JN
# two text files will now always made - but you can override the name of the average file via command line

def readin_plot_daily(station,extension,year1,year2,fr,alldatafile,csvformat,howBig,ReqTracks):
    """
    worker code for daily_avg_cl.py
    reads in daily files
    inputs:
    station
    extension (usually '')
    year1 and year2 if you want to specify beginning and ending years
    fr is 0 for all frequencies.  otherwise, it must be a legal frequency
    alldatafile is the output filename
    csvformat is a boolean for the output file. if true, csv file written instead of plain txt
    howBig is criterion for the median filter, i.e. how far in meters can a RH be from the median for that day
    ReqTracks is the number of retrievals required per day

    21may14 added utcTime to allRH file

    author: kristine larson
    """
    xdir = os.environ['REFL_CODE']
    print('All RH retrievals will be written to: ', alldatafile)
    allrh = open(alldatafile, 'w+')
    # put in a header
    allrh.write(" {0:s}  \n".format('% year,doy, RH(m), Month, day, azimuth(deg),freq, satNu, LSP amp,pk2noise,UTC(hr)' ))

    fs = 12
    NotEnough = 0
# putting the results in a np.array, with this ordering
# [yr, doy, meanRHtoday, len(rh), d.month, d.day, stdRHtoday]
    tv = np.empty(shape=[0, 7])
    obstimes = []; medRH = []; meanRH = [] ; alltimes = []
    fig,ax=plt.subplots()
    year_list = np.arange(year1, year2+1, 1)
    NumFiles = 0
    for yr in year_list:
        direc = xdir + '/' + str(yr) + '/results/' + station + '/' + extension + '/'
        if os.path.isdir(direc):
            all_files = os.listdir(direc)
            #print('Number of files in ', yr, len(all_files))
            for f in all_files:
                fname = direc + f
                L = len(f)
        # file names must have 7 characters in them ... 
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
                            y = a[:,0] +a[:,1]/365.25; rh = a[:,2] ; 
                            frequency = a[:,10]; azimuth = a[:,5]; sat = a[:,3]; amplitude=a[:,6]
                            # added utc to the all RH file
                            utcTime = a[:,4]; 
                            yr = int(a[0,0]); doy = int(a[0,1])
                            d = datetime.date(yr,1,1) + datetime.timedelta(doy-1)
                            peak2noise = a[:,13]

                            medv = np.median(rh)
                            # 0 means use all frequencies.  otherwise, you can specify 
                            if fr == 0:
                                cc = (rh < (medv+howBig))  & (rh > (medv-howBig))
                            else:
                                cc = (rh < (medv+howBig))  & (rh > (medv-howBig)) & (frequency == fr)
                            good =rh[cc]; goodT =y[cc]
                            gazim = azimuth[cc]; gsat = sat[cc]; gamp = amplitude[cc]; gpeak2noise = peak2noise[cc]
                            gfreq = frequency[cc]
                            # added 21may14
                            gutcTime = utcTime[cc]
                            
                            NG = len(good)
                            if (NG > 0):
                                if csvformat:
                                    for ijk in range(0,NG):
                                        allrh.write(" {0:4.0f},  {1:3.0f},{2:7.3f}, {3:2.0f}, {4:2.0f},{5:6.1f},{6:4.0f},{7:4.0f},{8:6.2f},{9:6.2f},{10:6.2f}\n".format(yr, 
                                            doy, good[ijk],d.month, d.day, gazim[ijk], gfreq[ijk], gsat[ijk],gamp[ijk],gpeak2noise[ijk], gutcTime[ijk]))
                                else:
                                    for ijk in range(0,NG):
                                        allrh.write(" {0:4.0f}   {1:3.0f} {2:7.3f} {3:2.0f} {4:2.0f} {5:6.1f} {6:4.0f} {7:4.0f} {8:6.2f} {9:6.2f} {10:6.2f}\n".format(yr, 
                                            doy, good[ijk],d.month, d.day, gazim[ijk], gfreq[ijk], gsat[ijk],gamp[ijk],gpeak2noise[ijk],gutcTime[ijk]))

        # only save if there are some minimal number of values
                            if (len(good) > ReqTracks):
                                rh = good
                                # this is the plot with all the data -not the daily average
                                alltimes = []
                                filler = datetime.datetime(year=yr, month=d.month, day=d.day)
                                for w in range(0,len(good)):
                                    alltimes.append(filler)
                                ax.plot(alltimes,good,'b.')

                                # this is for the daily average
                                obstimes.append(datetime.datetime(year=yr, month=d.month, day=d.day, hour=12, minute=0, second=0))
                                medRH =np.append(medRH, medv)
            # store the meanRH after the outliers are removed using simple median filter
                                meanRHtoday = np.mean(good)
                                stdRHtoday = np.std(good)
                                meanRH =np.append(meanRH, meanRHtoday)
            # add month and day just cause some people like that instead of doy
            # added standard deviation feb14, 2020
                                newl = [yr, doy, meanRHtoday, len(rh), d.month, d.day, stdRHtoday]
                                tv = np.append(tv, [newl],axis=0)
                                k += 1
                            else:
                                #print('not enough retrievals on ', yr, d.month, d.day, len(good))
                                NotEnough = NotEnough + 1
                    except:
                        okok = 1;
        else:
            abc = 0; # dummy line
    fig.autofmt_xdate()
    plt.ylabel('meters',fontsize=fs)
    plt.title('All Reflector Heights for Station: ' + station.upper(),fontsize=fs)
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)
    plt.gca().invert_yaxis()
    plt.grid()
#   new plot
    print('A total of ', NumFiles, ' days were evaluated.')
    print( NotEnough, ' days did not meet the threshold set for a dependable daily average')


    # close the file with all the RH values'
    allrh.close()

    # plot the number of retrievals vs time
    txtdir =  xdir + '/Files'
    daily_avg_stat_plots(obstimes,meanRH,station,txtdir,tv)

    return tv, obstimes

def daily_avg_stat_plots(obstimes,meanRH,station,txtdir,tv):
    """
    make some plots of results - moved here to make it cleaner
    inputs: obstimes is datetime object
    mean RH are in meters, station name, txtdir (where the results go)
    and tv is the variable of daily results
    """
#   new plot
    fs = 12
    fig,ax=plt.subplots()
    ax.plot(obstimes,meanRH,'b.')
    fig.autofmt_xdate()
    plt.ylabel('Reflector Height (m)',fontsize=fs)
    today = str(date.today())
    plt.title(station.upper() + ': Daily Mean Reflector Height, Computed ' + today,fontsize=fs)
    plt.grid()
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)

    plt.gca().invert_yaxis()
    pltname = txtdir + '/' + station + '_RH.png'
    plt.savefig(pltname)
    print('Daily average RH png file saved as: ', pltname)

    fig,ax=plt.subplots()
    plt.plot(obstimes, tv[:,3],'b.')
    fig.autofmt_xdate()
    plt.title(station.upper() + ': Number of values used in the daily average',fontsize=fs)
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)
    plt.grid()


def write_out_RH_file(obstimes,tv,outfile,csvformat):
    """
    given obstimes (datetime) and tv variable with LombScargle data
    and output filename, write out daily average RH values
    csvformat is a boolean.
    """
    print('Daily average RH file written to: ', outfile)
    # sort the time tags
    ii = np.argsort(obstimes)
    # apply time tags to a new variable
    ntv = tv[ii,:]
    N,M = np.shape(ntv)
    xxx = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    fout = open(outfile, 'w+')
    #  header of a sorts
    # change comment value from # to %
    fout.write("{0:28s} \n".format( '% calculated on ' + xxx ))
    fout.write("% Daily average reflector heights (RH) calculated using the gnssrefl software \n")
    fout.write("% year doy   RH    numval month day RH-sigma\n")
    fout.write("% year doy   (m)                      (m)\n")
    fout.write("% (1)  (2)   (3)    (4)    (5)  (6)   (7)\n")
    if csvformat:
        for i in np.arange(0,N,1):
            fout.write(" {0:4.0f},  {1:3.0f},{2:7.3f},{3:3.0f},{4:4.0f},{5:4.0f},{6:7.3f} \n".format(ntv[i,0], 
                ntv[i,1], ntv[i,2],ntv[i,3],ntv[i,4],ntv[i,5],ntv[i,6]))
    else:
        for i in np.arange(0,N,1):
            fout.write(" {0:4.0f}   {1:3.0f} {2:7.3f} {3:3.0f} {4:4.0f} {5:4.0f} {6:7.3f} \n".format(ntv[i,0], 
                ntv[i,1], ntv[i,2],ntv[i,3],ntv[i,4],ntv[i,5],ntv[i,6]))
    fout.close()


