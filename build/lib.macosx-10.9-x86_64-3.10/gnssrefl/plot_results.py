# very simple code to pick up all the RH results and make a plot.
# only getting rid of the biggest outliers using a median filter
# Kristine Larson May 2019
# June 30, 2019 added extension to results directory
# require you to have a minimum number of points to use for a daily average
# was previously using a default value
import argparse
import datetime
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
from datetime import date
#

def main():
# where the results are stored
    xdir = os.environ['REFL_CODE'] 

# must input start and end year
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year1", help="first year", type=int)
    parser.add_argument("year2", help="end year", type=int)
    parser.add_argument("medfilter", help="median filter", type=float)
    parser.add_argument("ReqTracks", help="required number of tracks", type=int)
# optional inputs: filename to output daily RH results 
    parser.add_argument("-txtfile", "--txtfile", default='None', type=str, help="txtfile for output")
    parser.add_argument("-noscreen", "--noscreen", default='None', type=str, help="toggle to not plot to screen")
    parser.add_argument("-extension", "--extension", default='None', type=str, help="extension for solution names")
    args = parser.parse_args()
    station = args.station
    year1= args.year1
    year2= args.year2
    medfilter= args.medfilter
    txtfile = args.txtfile
    ReqTracks = args.ReqTracks
    noscreen = args.noscreen
    if args.extension == 'None':
        extension = ''
    else:
        extension = args.extension

# where the summary files will be written to
    txtdir = xdir + '/Files' 

    if not os.path.exists(txtdir):
        print('make an output directory', txtdir)
        os.makedirs(txtdir)

# outliers limit, defined in meters
    howBig = medfilter;
    k=0
# added standard deviation 2020 feb 14, changed n=6
    n=7
# now require it as an input
# you can change this - trying out 80 for now
#ReqTracks = 80
# putting the results in a np.array, year, doy, RH, Nvalues, month, day
    tv = np.empty(shape=[0, n])
    obstimes = []; medRH = []; meanRH = [] 
    plt.figure()
    yearEnd = year2 + 1
    year_list = np.arange(year1,yearEnd,1)
    print('Years to examine: ',year_list)
    for yr in year_list:
        direc = xdir + '/' + str(yr) + '/results/' + station + '/' + extension + '/'
        print('looking at ', yr, direc)
        if os.path.isdir(direc):
            all_files = os.listdir(direc)
            for f in all_files:
                fname = direc + f
                L = len(f)
        # file names have 7 characters in them ... 
                if (L == 7):
        # check that it is a file and not a directory and that it has something/anything in it
                    try:
                        a = np.loadtxt(fname,skiprows=3,comments='%').T
                        numlines = len(a) 
                        if (len(a) > 0):
                            y = a[0] +a[1]/365.25; rh = a[2] ; doy = int(np.mean(a[1]))
        # change from doy to month and day in datetime
                            d = datetime.date(yr,1,1) + datetime.timedelta(doy-1)
                            medv = np.median(rh)
                            cc = (rh < (medv+howBig))  & (rh > (medv-howBig))
                            good =rh[cc]; goodT =y[cc]
        # only save if there are some minimal number of values
                            if (len(good) > ReqTracks):
                                rh = good
                                obstimes.append(datetime.datetime(year=yr, month=d.month, day=d.day, hour=12, minute=0, second=0))
                                medRH =np.append(medRH, medv)
                                plt.plot(goodT, good,'.')
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
                                print('not enough retrievals on ', yr, d.month, d.day, len(good))
                    except:
                        print('problem reading ', fname, ' so skipping it')
        else:
            print('that directory does not exist - so skipping')
    plt.ylabel('Reflector Height (m)')
    plt.title('GNSS station: ' + station)
    plt.gca().invert_yaxis()
    plt.grid()
    if (noscreen == 'None'):
        plt.show()
    fig,ax=plt.subplots()
    ax.plot(obstimes,meanRH,'.')
    fig.autofmt_xdate()
    plt.ylabel('Reflector Height (m)')
    today = str(date.today())
    plt.title(station.upper() + ': Daily Mean Reflector Height, Computed ' + today)
    plt.grid()
    plt.gca().invert_yaxis()
    pltname = txtdir + '/' + station + '_RH.png'
    plt.savefig(pltname)
    print('png file saved: ', pltname)

    if (noscreen == 'None'):
        plt.show()

    if txtfile == 'None':
        print('no txt output requested ')
    else:
    # sort the time tags
        ii = np.argsort(obstimes)
    # apply time tags to a new variable
        ntv = tv[ii,:]
        N,M = np.shape(ntv)
        outfile = txtdir + '/' + txtfile
        xxx = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        print('output file: ', outfile)
        fout = open(outfile, 'w+')
    # change comment value from # to %
        fout.write("{0:28s} \n".format( '% calculated on ' + xxx ))
        fout.write("% year doy   RH    numval month day RH-sigma\n")
        fout.write("% year doy   (m)                      (m)\n")
        fout.write("% (1)  (2)   (3)    (4)    (5)  (6)   (7)\n")
        for i in np.arange(0,N,1):
            fout.write(" {0:4.0f}   {1:3.0f} {2:7.3f} {3:3.0f} {4:4.0f} {5:4.0f} {6:7.3f} \n".format(ntv[i,0], 
                ntv[i,1], ntv[i,2],ntv[i,3],ntv[i,4],ntv[i,5],ntv[i,6]))
        fout.close()

if __name__ == "__main__":
    main()
