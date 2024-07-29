# subdaily libraries
import datetime
import math
import matplotlib.pyplot as plt
import numpy as np
from astropy.time import Time

# gnssrefl specific code
import gnssrefl.gps as g
import gnssrefl.gnssir_v2 as guts2

import scipy
import scipy.interpolate as interpolate
from scipy.interpolate import interp1d


def mjd_to_obstimes(mjd):
    """
    takes mjd array and converts to datetime for plotting.

    Parameters
    ----------
    mjd : numpy array of floats
        mod julian date

    Returns
    -------
    dt : numpy array of datetime objects

    """

    dt = Time(mjd,format='mjd').utc.datetime; 

    return dt


def write_spline_output(iyear, th, spline, delta_out, station, txtdir,Hortho):
    """
    Writing the output of the spline fit to the final RH time series.
    No output other than this text file for year 2023 and station name ssss:

    $REFL_CODE/Files/ssss/ssss_2023_spline_out.txt


    I do not think this is used anymore. It has been consolidated with the plot code.

    Parameters
    ----------
    iyear : int
        full year
    th : numpy array
        time values of some kind ... maybe fractional day of years?
    spline: fit, output of interpolate.BSpline
        needs doc
    delta_out : int
        how often you want the splinefit water level written, in seconds
    station : str
        station name
    txtdir : str
        output directory
    Hortho : float
        orthometric height used to convert RH to something more sea level like
        meters
    """

    if delta_out == 0:
        print('No spline values will be written because the interval is set to zero.')
    else:
        firstpoint  = float(th[0]); lastpoint = float(th[-1])
        s1 = math.floor(firstpoint) ; s2 = math.ceil(lastpoint)
        ndays = s2-s1 # number of days
        # how many values you want in the linspace world
        numvals = 1 + int(ndays*86400/delta_out)
        # this should be evenly defined fractional doy
        tplot = np.linspace(s1, s2, numvals,endpoint=True)
        # then fit it
        spline_even = spline(tplot)
        N = len(tplot)

        # but you only want those values when we have data ....
        splinefileout =  txtdir + '/' + station + '_' + str(iyear) + '_spline_out_orig.txt'
        print('Writing evenly sampled file to: ', splinefileout)
        vn = ' gnssrefl v' + str(g.version('gnssrefl'))
        fout = open(splinefileout,'w+')
        fout.write('{0:1s}  {1:30s}  \n'.format('%','station: ' + station + vn))
        fout.write('{0:1s}  {1:30s}  \n'.format('%','This is NOT observational data - be careful when interpreting it.'))
        fout.write('{0:1s}  {1:30s}  \n'.format('%','If the data are not well represented by the spline functions, you will '))
        fout.write('{0:1s}  {1:30s}  \n'.format('%','have a very poor representation of the data. I am also writing out station '))
        fout.write('{0:1s}  {1:30s}  {2:8.3f} \n'.format('%','orthometric height minus RH, where Hortho (m) is ', Hortho  ))
        fout.write('{0:1s}  {1:30s}  \n'.format('%','This assumes RH is measured relative to the L1 phase center.  '))
        fout.write('{0:1s}  {1:30s}  \n'.format('%','MJD             RH(m) YYYY MM DD  HH  MM  SS   quasi-sea-level(m)'))
        fout.write('{0:1s}  {1:30s}  \n'.format('%','(1)              (2)  (3) (4) (5) (6) (7) (8)    (9)'))


        dtime = False
        for i in range(0,N):
            modjul = g.fdoy2mjd(iyear,tplot[i])
            doy = math.floor(tplot[i])
            utc= 24*(tplot[i] - doy)
            bigt,yy,mm,dd,hh,mi,ss = g.ymd_hhmmss(iyear,doy,utc,dtime)
            if (tplot[i] >= firstpoint) & (tplot[i] <= lastpoint):
                fout.write('{0:15.7f}  {1:10.3f} {2:4.0f} {3:3.0f} {4:3.0f} {5:3.0f} {6:3.0f} {7:3.0f} {8:10.3f} \n'.format(
                    modjul, spline_even[i], yy,mm,dd,hh,mi,ss, Hortho-spline_even[i]))
        fout.close()

def testing_nvals(Gval, Rval, Eval, Cval):
    """
    writing the number of observations per constellation as a test. not currently used

    Parameters
    Gval: numpy array
        GPS RH values
    Rval : numpy array
        GLONASS RH values
    Eval : numpy array
        Galileo RH values
    Cval : numpy
        Beidou RH values

    writes to a file - kristine.txt returns nothing

    """
    fouting = open('kristine.txt','w+')
    for i in range(0,len(Gval)):
        fouting.write(' {0:3.0f} {1:4.0f} {2:4.0f} {3:4.0f} {4:4.0f} \n'.format(i, Gval[i], Rval[i], Eval[i], Cval[i]))
    fouting.close()

    return


def numsats_plot(station,tval,nval,Gval,Rval,Eval,Cval,txtdir,fs,hires_figs,year):
    """
    makes the plot that summarizes the number of satellites in each
    constellation per epoch

    Parameters
    ----------
    station : str
        name of the station
    tval : numpy array
        datetime objects?
    nval : numpy array
        number of total satellites at a given epoch
    Gval : numpy array
        number of galileo satellites at an epoch
    Rval : numpy array
        number of glonass satellites at an epoch
    Eval : numpy array
        number of galileo satellites at an epoch
    Cval : numpy array
        number of beidou satellites at an epoch
    txtdir : str
        where results are stored
    fs : int
        fontsize for the plots
    hires_figs : bool
        try to plot high resolution
    year : int
        calendar year

    """

    fig,ax=plt.subplots(figsize=(10,5))
    ax.plot(tval,nval,'ko',label='Total',markersize=3)
    if (np.sum(Gval) > 0):
        ax.plot(tval,Gval,'bo',label='GPS',markersize=3)
    if (np.sum(Rval) > 0):
        ax.plot(tval,Rval,'ro',label='GLO',markersize=3)
    if (np.sum(Eval) > 0):
        ax.plot(tval,Eval,'o',color='orange',label='GAL',markersize=3)
    if (np.sum(Cval) > 0):
        ax.plot(tval,Cval,'co',label='BEI',markersize=3)

    plt.legend(loc="best",fontsize=fs)
    #ax.legend(loc='best')
    plt.title(station + ': number of RH retrievals each day',fontsize=fs)
    plt.xticks(rotation =45,fontsize=fs); plt.yticks(fontsize=fs)
    plt.grid()

    # was trying to do this, but life is short
    #if hires_figs:
#        https://stackoverflow.com/questions/4700614/how-to-put-the-legend-outside-the-plot
    # Shrink current axis's height by 10% on the bottom
        #box = ax.get_position()

        #ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
        #ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=5)

    # Put a legend below current axis
        #ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=4)
        #ax.set_position([box.x0, box.y0 + box.height * 0.5, box.width, box.height ])
        #ax.legend(loc='center left', bbox_to_anchor=(1, 0.3))


    fig.autofmt_xdate()
    plotname = txtdir + '/' + station + '_' + str(year) + '_Subnvals.png'
    if hires_figs:
        plotname = txtdir + '/' + station + '_' + str(year) +'_Subnvals.eps'

    plt.savefig(plotname,dpi=300)
    print('Plot file saved as: ', plotname)


def rh_plots(otimes,tv,station,txtdir,year,d1,d2,percent99):
    """
    overview plots for rh_plot

    Parameters
    ----------
    otimes : numpy array of datetime objects
        observation times
    tv : numpy array
        gnssrefl results written into this variable using loadtxt
    station : str
        station name, only used for the title
    txtdir : str
        directory where the plots will be written to
    year: int
        what year is being analyzed
    d1 : int
        minimum day of year
    d2 : int
        maximum day of year
    percent99 : bool
        whether you want only the 1-99 percentile plotted

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
    fig,(ax2,ax3)=plt.subplots(2,1,sharex=True)
        # put some azimuth information on it
    colors = tv[:,5]
        # ax.plot( otimes, tv[:,2], '.')
        # https://matplotlib.org/stable/gallery/lines_bars_and_markers/scatter_with_legend.html
    # help from felipe nievinski
    #tmp = numpy.percentile(tv[:,2], [1 99])
    #matplotlib.pyplot.ylim(tmp[1], tmp[2])

    scatter = ax2.scatter(otimes,tv[:,2],marker='o', s=10, c=colors)
    colorbar = fig.colorbar(scatter, ax=ax2)
    colorbar.set_label('deg', fontsize=fs)
    ax2.set_ylabel('meters',fontsize=fs)
    ax2.set_title('Azimuth',fontsize=fs)
    #ax1.title.set_text('Azimuth')
    plt.xticks(rotation =45,fontsize=fs); plt.yticks(fontsize=fs)
    fig.suptitle( station.upper() + ' Reflector Heights', fontsize=fs)

    if setlimits:
        ax2.set_xlim((th1, th2))

    # now doing 1 and 99%
    p1 = 0.01; p2 = 0.99
    #lowv, highv = my_percentile(tv[:,2],p1, p2)
    # this crashed my docker build - but it turned out to have nothing to do with it
    yl = np.percentile(tv[:,2] ,[1 ,99])
    print('percentile values',yl)
    # I think this is a typo?
    #lowv = yl[0]; highv = y[1]
    lowv = yl[0]; highv = yl[1]
    
    if percent99:
        ax2.set_ylim((lowv,highv))

    ax2.invert_yaxis()
    ax2.grid(True)

    fig.autofmt_xdate()

#    put some amplitude information on it
    # https://matplotlib.org/stable/gallery/lines_bars_and_markers/scatter_with_legend.html
    colors = tv[:,6]

    scatter = ax3.scatter(otimes,tv[:,2],marker='o', s=10, c=colors)
    colorbar = fig.colorbar(scatter, ax=ax3)
    ax3.set_ylabel('meters',fontsize=fs)
    colorbar.set_label('v/v', fontsize=fs)
    plt.xticks(rotation =45,fontsize=fs); plt.yticks(fontsize=fs)
    ax3.set_title('Amplitude',fontsize=fs)
    ax3.grid(True)
    if setlimits:
        ax3.set_xlim((th1, th2))

    if percent99:
        ax3.set_ylim((lowv, highv ))
    ax3.invert_yaxis()
    fig.autofmt_xdate()

    if percent99:
        plotname = txtdir + '/' + station + '_rh2_99.png'
    else:
        plotname = txtdir + '/' + station + '_rh2.png'


    print('png file saved as: ', plotname)
    plt.savefig(plotname,dpi=300)


def two_stacked_plots(otimes,tv,station,txtdir,year,d1,d2,hires_figs):
    """
    This actually makes three stacked plots - not two, LOL
    It gives an overview for quality control

    Parameters
    ----------
    otimes : numpy array of datetime objects
        observations times
    tv : numpy array
        gnssrefl results written into this variable using loadtxt
    station : str
        station name, only used for the title
    txtdir : str
        where the plots will be written to
    year: int
        what year is being analyzed
    d1 : int
        minimum day of year
    d2 : int
        maximum day of year
    hires_figs : bool
        true for eps instead of png

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
    fs = 12
    fig,(ax1,ax2,ax3)=plt.subplots(3,1,sharex=True,figsize=(10,8))
    #fig,(ax1,ax2,ax3)=plt.subplots(3,1,sharex=True)
    i = (tv[:,10] < 100)
    colors = tv[:,10]
    scatter = ax1.scatter(otimes,tv[:,2],marker='o', s=10, c=colors)
    colorbar = fig.colorbar(scatter, ax=ax1)
    colorbar.set_label('Frequency', fontsize=fs)
    ax1.set_title('Signals',fontsize=fs)
    plt.xticks(rotation =45,fontsize=fs); 
    ax1.set_ylabel('RH (m)',fontsize=fs)
    plt.yticks(fontsize=fs)
    ax1.invert_yaxis()
    ax1.grid(True)
    #fig.suptitle( station.upper() + ' Reflector Heights', fontsize=fs)
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
    ax2.set_ylabel('RH (m)',fontsize=fs)
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
    ax3.set_ylabel('RH (m)',fontsize=fs)
    colorbar.set_label('v/v', fontsize=fs)
    plt.xticks(rotation =45,fontsize=fs); plt.yticks(fontsize=fs)
    ax3.set_title('Amplitude',fontsize=fs)
    ax3.invert_yaxis()
    ax3.grid(True)
    if setlimits:
        ax3.set_xlim((th1, th2))
    fig.autofmt_xdate()

    plotname = txtdir + '/' + station + '_' + str(year) + '_combined.png'
    if hires_figs:
        plotname = txtdir + '/' + station + '_' + str(year) + '_combined.eps'
        plt.savefig(plotname,dpi=300)
    else:
        plt.savefig(plotname,dpi=300)
    print('Plot file saved as: ', plotname)

def stack_two_more(otimes,tv,ii,jj,stats, station, txtdir, sigma,kplt,hires_figs,year):
    """
    makes a plot of the reflector heights before and after minimal editing

    Parameters
    ----------
    otimes : numpy array of datetime objects 
        observation times
    tv : numpy array
        variable with the gnssrefl LSP results
    ii : numpy array
        indices of good data
    jj : numpy array
        indices of bad data
    station : str
        station name
    txtdir : str
        directory where plots will be written
    sigma : float
        what kind of standard deviation is used for outliers (3sigma, 2.5 sigma etc)
    kplt : bool
        make extra plot for kristine
    year : int 
        calendar year
    """
    fs = 10
    otimesarray = np.asarray(otimes)
    # new plot 
    plt.figure(figsize=(10,5))
    plt.plot(tv[:,5],tv[:,2], '.',markersize=4,label='obs')
    plt.plot(tv[ii,5],tv[ii,2], 'ro',markersize=4,label='outliers')
    plt.xlabel('Azimuth (degrees)')
    plt.ylabel('Reflector Height (m)')
    plt.title('Quick Plot of RH with respect to Azimuth')
    plt.gca().invert_yaxis()
    plt.legend(loc="best")
    plt.grid()
    plotname_stem = txtdir + '/' + station + '_' + str(year) + '_outliers_wrt_az'
    if hires_figs:
        plotname = plotname_stem + '.eps'
    else:
        plotname = plotname_stem + '.png'

    plt.savefig(plotname,dpi=300)
    print('Plot file saved as: ', plotname)

    #    fig=plt.figure(figsize=(10,6))
    fig = plt.figure(figsize=(10,6))
    colors = tv[:,5]
# put some amplitude information on it
# ax.plot( otimes, tv[:,2], '.')
# https://matplotlib.org/stable/gallery/lines_bars_and_markers/scatter_with_legend.html


    ax1 = fig.add_subplot(211)
    plt.plot(otimes,tv[:,2], '.',color='gray',label='arcs')
    plt.plot(stats[:,0], stats[:,1], '.',markersize=4,color='blue',label='daily avg')
    slabel = str(sigma) + ' sigma'
    plt.plot(stats[:,0], stats[:,1]-sigma*stats[:,2], '--',color='black',label=slabel)
    plt.plot(stats[:,0], stats[:,1]+sigma*stats[:,2], '--',color='black')
    plt.plot(otimesarray[ii],tv[ii,2], 'r.',markersize=4,label='outliers')
    #plt.plot(otimesarray[ii],tv[ii,2], '.',color='red',label='outliers',markersize=12)
    plt.legend(loc="best",bbox_to_anchor=(0.95, 0.9),prop={"size":fs-2})
    plt.title('Raw ' + station.upper() + ' Reflector Heights', fontsize=fs)
    plt.ylabel('meters',fontsize=fs)
    plt.gca().invert_yaxis()
    plt.xticks(rotation =45,fontsize=fs); plt.yticks(fontsize=fs)
    plt.grid() ; fig.autofmt_xdate()
    # get the limits so you can use thme on the next plot
    #aaa, bbb = plt.ylim()
    savey1,savey2 = plt.ylim()  

    ax2 = fig.add_subplot(212)
    plt.plot(otimesarray[jj],tv[jj,2], '.',color='green',label='arcs')
    plt.gca().invert_yaxis()
    plt.ylabel('meters',fontsize=fs)
    plt.xticks(rotation =45,fontsize=fs); plt.yticks(fontsize=fs)
    plt.title('Edited ' + station.upper() + ' Reflector Heights', fontsize=fs)

    plt.grid() ; fig.autofmt_xdate()
    plotstem = txtdir + '/' + station + '_' + str(year) + '_outliers'
    if hires_figs:
        plotname = plotstem + '.eps'
        plt.savefig(plotname,dpi=300)
    else:
        plotname = plotstem + '.png'
        plt.savefig(plotname,dpi=300)

    plt.ylim((savey1, savey2))
    print('Plot file saved as: ', plotname)
    if kplt:
        fig = plt.figure()
        ax1 = fig.add_subplot(211)
        ddd = - (tv[jj,2] - np.max(tv[jj,2]))
        plt.plot(otimesarray[jj],ddd, '.',color='blue')
        plt.title('Relative Sea Level Measured with Reflected GNSS Signals:' + station.upper(), fontsize=fs)
        plt.ylabel('meters',fontsize=fs)
        plt.xticks(rotation =45,fontsize=fs-1); plt.yticks(fontsize=fs-1)
        plt.ylim((-0.1, 1.1*np.max(ddd)))
        plt.suptitle(f"St Michael, Alaska ", size=12)
        plt.grid()

def writeout_spline_outliers(tvd_bad,txtdir,residual,filename):
    """

    Write splinefit outliers to a text file. 

    Parameters
    ----------
    tvd_bad : numpy array
        output of the lomb scargle calculations
    txtdir : str
        directory for the output, i.e. $REFL_CODE/FiLes/station
    residual : numpy array
        RH outliers in units of meters (!)
    filename : str
        name of file being written

    """
    nr,nc=tvd_bad.shape
    if nr > 0:
        f = txtdir + '/' + filename
        print(nr, ' Outliers written to: ', f)
        fout = open(f, 'w+')
        # put in a header
        fout.write('{0:3s} sat azim deltT-min outlier-m fracDOY MJD  OrigRH meanE PkNoise \n'.format('%'))
        fout.write('{0:3s} (1) (2)   (3)        (4)      (5)    (6)   (7)    (8)   (9)\n'.format('%'))
        for w in range(0,nr):
            fy = tvd_bad[w,1] + tvd_bad[w,4]/24 # fractional day of year
            deltaT = tvd_bad[w,14]
            mjd = tvd_bad[w,15]
            # average elevation angle
            elAv = 0.5*(tvd_bad[w,8] + tvd_bad[w,7])
            fout.write('{0:3.0f} {1:7.2f} {2:7.2f} {3:7.2f} {4:9.3f} {5:15.7f} {6:7.2f} {7:7.2f} {8:5.2f}\n'.format( 
                tvd_bad[w,3], tvd_bad[w,5], deltaT,residual[w],fy,mjd,tvd_bad[w,2],elAv,tvd_bad[w,13]))
        fout.close()

    return

def print_badpoints(t,outliersize,txtdir,real_residuals):
    """
    prints outliers to a file.

    Parameters
    ----------
    t : numpy array
        lomb scargle result array of "bad points". Format given below
    outliersize : float
        outlier criterion, in meters
    txtdir : str
        directory where file is written
    real_residuals : numpy array of floats
        assume this is RH residuals in meters

    Returns
    -------
    writes to a file called outliers.txt in the Files/station area

    """
# format of t 

# (1)  (2)   (3) (4)  (5)     (6)   (7)    (8)    (9)   (10)  (11) (12) (13)    (14)     (15)    (16) (17) (18,19,20,21,22)
# year, doy, RH, sat,UTCtime, Azim, Amp,  eminO, emaxO,NumbOf,freq,rise,EdotF, PkNoise  DelT     MJD  refr  MM DD HH MM SS
# (0)  (1)   (2) (3)  (4)     (5)   6 )    (7)    (8)   (9)  (10) (11) (12)    (13)     (14)    (15)  (16) ... 

    m,n = t.shape
    f = txtdir + '/outliers.txt'
    if (m > 0):
        print(m, ' Outliers written to file: ', f)        
        fout = open(f, 'w+')
        for i in range(0,m):
            fout.write('doy {0:3.0f} sat {1:3.0f} azim {2:6.2f} fr {3:3.0f} pk2noise {4:5.1f} residual {5:5.2f} \n'.format( 
                t[i,1], t[i,3],t[i,5], t[i,10], t[i,13], real_residuals[i] ))
        fout.close()
    else:
        print('no outlier points to write to a file')

def writejsonfile(ntv,station, outfile):
    """
    subdaily RH values written out in json format

    This does not appear to be used

    Parameters
    -----------
    ntv : numpy of floats
        LSP results

    station : str
        4 ch station name

    outfile : str
        filename for output

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

def rhdot_plots(th,correction,rhdot_at_th, tvel,yvel,fs,station,txtdir,hires_figs,year):
    """
    makes the rhdot correction plots

    Parameters
    ----------
    th : numpy array
        time of obs, MJD
    correction : numpy array
        rhcorrections in meters
    rhdot_at_th : numpy array of floats
        spline fit for rhdot in meters
    tvel : numpy array of floats
        time for surface velocity in MJD
    yvel : numpy array of floats
        surface velocity in m/hr
    fs : integer
        fontsize 
    station : str
        station name
    txtdir : str
        file directory for output
    hires_figs : bool
        whether you want eps instead of png 
    year : int
        calendar year

    """
    mjd0 = g.fdoy2mjd(year, th[0] ) # MJD of first point
    # not being used


    fig=plt.figure(figsize=(10,6))
    plt.subplot(2,1,1)
    th_obs = mjd_to_obstimes(th)

    plt.plot(th_obs, correction,'b.')

    plt.ylabel('meters',fontsize=fs);
    #plt.xlim((np.min(th), np.max(th)))
    plt.grid()
    plt.title('The RH correction from RHdot effect ')
    #plt.xlim((th_obs[0], th_obs[-1])) #fig.autofmt_xdate()

    plt.subplot(2,1,2)
    #mjd1 = g.fdoy2mjd(year, tvel[0] ) # MJD of first point
    #tvel_obs = mjd_to_obstimes(tvel+mjd1)

    # ???
    A1 = np.min(th)  ; A2 = np.max(th) 
    jj = (tvel >= A1) & (tvel <= A2)

    plt.plot(th_obs, rhdot_at_th,'b.',label='at GNSS obs')
    # disaster - did not work
    #plt.plot(tvel_obs, yvel,'c-', label='spline fit')

    tvel_obstime = mjd_to_obstimes(tvel[jj])
    plt.plot(tvel_obstime, yvel[jj],'c-', label='spline fit')
    #plt.plot(tvel[jj], yvel[jj],'c-', label='spline fit')

    plt.legend(loc="upper left")
    plt.grid()
    plt.title('surface velocity')
    plt.ylabel('meters/hour'); 
    #plt.xlabel('days of the year') 
    fig.autofmt_xdate()

    #plt.xlim((A1,A2))
    #plt.xlim((th[0], th[-1])) #fig.autofmt_xdate()

    if hires_figs:
        g.save_plot(txtdir + '/' + station + '_rhdot3.eps')
    else:
        g.save_plot(txtdir + '/' + station + '_rhdot3.png')


def find_ortho_height(station,extension):
    """
    Find orthometric (sea level) height used in final subdaily spline output 
    and plots. This value should be defined for the GPS L1 phase center of 
    the GNSS antenna as this is what is assumed in the subdaily code.

    Parameters
    ----------
    station : str
        4 ch station name
    extension : str
        gnssir analysis, extension mode

    Returns
    -------
    Hortho : float
        orthometric height from gnssir json analysis file as 
        defined as Hortho, in meters. If your preferred value 
        for Hortho is not present, it is calculated from the  
        ellipsoidal height and EGM96. 

    """

    lsp = guts2.read_json_file(station, extension)

    if 'Hortho' in lsp:
        # found in the lsp file
        Hortho = lsp['Hortho']
    else:
        # calculate from EGM96
        geoidC = g.geoidCorrection(lsp['lat'],lsp['lon'])
        Hortho = lsp['ht']- geoidC

    return Hortho

def mirror_plot(tnew,ynew,spl_x,spl_y,txtdir,station,beginT,endT):
    """
    Makes a plot of the spline fit to the mirrored RH data
    Plot is saved to txtdir as  station_rhdot1.png

    Parameters
    ----------
    tnew : numpy of floats
        time in MJD
    ynew : numpy of floats
        RH in meters 
    spl_x : numpy of floats
        time in days of year
    spl_y : numpy of floats
        smooth RH, meters
    txtdir : str
        directory for plot
    station : str
        name of station for title
    beginT : float
        first measurement time (MJD) for RH measurement
    endT : float
        last measurement time (MJD) for RH measurement

    """
    fig=plt.figure(figsize=(10,4))
    i = (spl_x > beginT) & (spl_x < endT) # to avoid wonky points in spline
    #if (beginT > 380):
    if True:
        objtime = mjd_to_obstimes(tnew)
        plt.plot(objtime,ynew, 'b.', label='obs+fake obs')
        plt.plot(mjd_to_obstimes(spl_x),spl_y,'-', color='orange',label='spline all')
        plt.plot(mjd_to_obstimes(spl_x[i]),spl_y[i],'c-', label='spline obs')
        plt.xlabel('MJD')
    #else:
    #    plt.plot(tnew,ynew, 'b.', label='obs+fake obs')
    #    plt.plot(spl_x,spl_y,'o-', label='spline for all')
    #    plt.plot(spl_x[i],spl_y[i],'c-', label='spline for obs')
    #    plt.xlabel('days of the year')

    plt.title('Mirrored obs and spline fit ')
    plt.legend(loc="upper left")
    plt.ylabel('meters')
    #plt.xlim((beginT, endT))

    plt.grid()
    fig.autofmt_xdate()

    g.save_plot(txtdir + '/' + station + '_rhdot1.png')
    # do not plot to the screen ... 
    plt.close()

def quickTr(year, doy,frachours):
    """
    takes timing from lomb scargle code (year, doy) and UTC hour (fractional)
    and returns a date string

    Parameters
    ----------
    year : int
        full year
    doy : int
        day of year
    frachours : float
        real-valued UTC hour 

    Returns
    -------
    datestring : str
         date ala YYYY-MM-DD HH:MM:SS
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


def subdaily_resids_last_stage(station, year, th, biasCor_rh, spline_at_GPS, fs, strsig, hires_figs, 
                               txtdir, ii, jj, th_even,spline_whole_time):
    """
    Makes the final residual plot for subdaily (after RHdot and IF correction made).
    Returns the bad points ...


    Allows either the original or multiyear option..


    Parameters
    ----------
    station : str
        4 character station name
    year : int
        calendar year
    th : numpy array of ??
        time variable of some kind, fractional day of year ?
    biasCor_rh : numpy array of floats
        refl hgts that have been corrected for RHdot and IF
    spline_at_GPS : numpy array of floats
        RH derived From the spline fit and calculated at GPS time tags
    fs : int
        font size
    strsig : str
        sigma string to go on the legend
    hires_figs : bool
        whether to save the plots with better resolution
    txtdir : str
        directory where the plot will be saved
    ii : numpy array
        indices of the outliers?
    jj : numpy array
        indices of the values to keep?
    th_even : numpy array
        evenly spaced time values, day of year
    spline_whole_time : numpy array of flots
        splinefit for ???

    Returns
    -------
    badpoints2 : numpy array of floats
         RH residuals
    """
    # this means you are already in MJD ... 
    #if (th[0] > 400):
    if True:
        th_obs = mjd_to_obstimes(th)
        th_even_obs = mjd_to_obstimes(th_even)
    #else:
    #    # convert obs to mjd and then obstimes
    #    mjd0 = g.fdoy2mjd(year, th[0])
    #    th_obs = mjd_to_obstimes(mjd0 + th - th[0])
    # convert the spline to mjd and then obstimes
    #    mjd1 = g.fdoy2mjd(year, th_even[0])
    #    th_even_obs = mjd_to_obstimes(mjd1 + th_even - th_even[0])


    # these are now plotted in datetime via mjd translation
    fig=plt.figure(figsize=(10,5))
    plt.plot(th_obs, biasCor_rh, 'b.', label='RH ' + strsig)
    plt.plot(th_even_obs, spline_whole_time, '-',color='orange',label='spline')
    plt.plot(th_obs[ii], biasCor_rh[ii], 'rx', label='outliers')

    plt.legend(loc="best",fontsize=fs)
    plt.grid() ; plt.gca().invert_yaxis()
    plt.ylabel('meters',fontsize=fs); 
    plt.title(station.upper() + ' RH with RHdot and InterFrequency Corrections Applied',fontsize=fs)
    fig.autofmt_xdate()

    # put hires_figs boolean here
    if hires_figs:
        g.save_plot(txtdir + '/' + station + '_rhdot4.eps')
    else:
        g.save_plot(txtdir + '/' + station + '_rhdot4.png')

    # this figure is not sent to the screen
    fig=plt.figure(figsize=(10,5))
    plt.plot(th_obs, biasCor_rh - spline_at_GPS, 'b.',label='all residuals')
    plt.title('Station:' + station + ' Residuals to new spline fit',fontsize=fs)
    plt.grid()
    plt.ylabel('meters',fontsize=fs)

    plt.plot(th_obs[ii], (biasCor_rh -spline_at_GPS)[ii], 'r.',label='outliers')
    # will write these residauls out to a file
    badpoints2 =  (biasCor_rh -spline_at_GPS)[ii]
    plt.legend(loc="upper left",fontsize=fs)
    fig.autofmt_xdate()

    # print('\n RMS with frequency biases and RHdot taken out (m) ', np.round(newsigma,3) , '\n' )
    if hires_figs:
        g.save_plot(txtdir + '/' + station + '_rhdot5.eps')
    else:
        g.save_plot(txtdir + '/' + station + '_rhdot5.png')

    plt.close() # 

    return badpoints2

def RH_ortho_plot2( station, H0, year,  txtdir, fs, time_rh, rh, gap_min_val,th,spline,delta_out,csvfile,gap_flag):
    """

    Makes a plot of the final spline fit to the data. Output time interval controlled by the user.

    It also now writes out the file with the spline fit

    Parameters
    ----------
    station : str
        name of station, 4 ch
    H0 : float
        datum correction (orthometric height) to convert RH to MSL data, in meters
    year : int
        year of the time series (ultimately should not be needed)
    txtdir : str
       location of plot
    fs : int
        fontsize
    time_rh : numpy of floats
        time of rh values, in fractional doy I believe
    rh : numpy of floats
        refl hgt in meters
    gap_min_val : float
        minimum length gap allowed, in day of year units
    th : numpy floats
        time values in MJD
    spline : output of interpolate.BSpline
        used for fitting 
    delta_out : int
        how often spline is printed, in seconds
    csvfile : bool
        print out csv instead of plain txt
    gap_flag : bool
        whether to write 999 in file where there are gaps
    """

    #print('Entering RH_ortho_plot2')
    firstpoint = float(th[0]); lastpoint = float(th[-1])
    s1 = math.floor(firstpoint); s2 = math.ceil(lastpoint)
    ndays = s2-s1 # number of days
    numvals = 1 + int(ndays*86400/delta_out)
    tp=np.linspace(s1,s2,numvals,endpoint= True)
    #print('RH_ortho_plot2, s1, s2, numvals,ndays')
    #print(s1, s2, numvals,ndays)

    # previous tp definition goes from beginning of the first day to the end of last day - but 
    # does not recognize that the file could have started well beyond that first point 
    # and it might end say 8 hours into the last day
    ii = (tp >= firstpoint) & (tp <= lastpoint)
    tp = tp[ii]

    # this means it is already in MJD ???
    #if (th[0] > 400): 

    if True: 
        # don't think this boolean is used anymore.  it is not
        # truly multiyear, but more a flag that you are using MJD
        multiyear = True
        mjd_new = tp
        #print('multiyear is true, start at ', mjd_new[0])
        mjd_new_obstimes = mjd_to_obstimes(mjd_new)
        spline_new = spline(tp)
    #else:
    #    multiyear = False
    #    mjd1 = g.fdoy2mjd(year, tp[0] ) # 
    #    #print(year, tp[0], mjd1,np.floor(mjd1))
    #    mjd_new = np.floor(mjd1) + (tp - tp[0])
    #    print('multiyear is false, start at ', mjd_new[0])
    #    mjd_new_obstimes = mjd_to_obstimes(mjd_new)
    #    spline_new = spline(tp)

    N_new = len(mjd_new_obstimes)

    # looks like I identified the gaps in day of year units - 
    # but then did the implementation in mjd and then datetime ...
    #splinefileout =  txtdir + '/' + station + '_' + str(year) + '_spline_out.txt'
    if csvfile:
        splinefileout =  txtdir + '/' + station +  '_spline_out.csv'
    else:
        splinefileout =  txtdir + '/' + station +  '_spline_out.txt'


    print('Writing evenly sampled file to: ', splinefileout)
    fout = open(splinefileout,'w+')
    vn = station + ' gnssrefl v' + str(g.version('gnssrefl'))
    fout.write('{0:1s}  {1:30s}  \n'.format('%','station ' + vn))
    fout.write('{0:1s}  {1:60s}  \n'.format('%','TIME TAGS ARE IN UTC/999 values mean there was a large gap and no spline value is available.'))
    fout.write('{0:1s}  {1:30s}  \n'.format('%','This is NOT observational data - be careful when interpreting it.'))
    fout.write('{0:1s}  {1:30s}  \n'.format('%','If the data are not well represented by the spline functions, you will '))
    fout.write('{0:1s}  {1:30s}  \n'.format('%','have a very poor representation of the data. I am also writing out station '))
    fout.write('{0:1s}  {1:30s}  {2:8.3f} \n'.format('%','orthometric height minus RH, where Hortho (m) is ', H0  ))
    #fout.write('{0:1s}  {1:30s}  \n'.format('%','This assumes RH is measured relative to the L1 phase center.  '))
    #fout.write('{0:1s}  {1:30s}  \n'.format('%','MJD, RH(m), YY,MM,DD,HH,MM,SS, quasi-sea-level(m)'))
    if csvfile:
        fout.write('{0:1s}  {1:30s}  \n'.format('%','MJD,             RH(m), YYYY, MM, DD, HH, MM, SS,  quasi-sea-level(m)'))
        fout.write('{0:1s}  {1:30s}  \n'.format('%','(1),              (2),  (3), (4),(5), (6),(7),(8),   (9)'))
    else:
        fout.write('{0:1s}  {1:30s}  \n'.format('%','MJD              RH(m)  YYYY  MM  DD  HH  MM  SS   quasi-sea-level(m)'))
        fout.write('{0:1s}  {1:30s}  \n'.format('%','(1)               (2)   (3)  (4) (5)  (6) (7) (8)    (9)'))


    # difference function to find time between all rh measurements
    gdiff = np.diff( time_rh )
    if multiyear:
        mjdt = time_rh
        mjd = mjdt[0:-1]
    else:
        mjdx = g.fdoy2mjd(year, time_rh[0] ) # 
        mjdt = mjdx + (time_rh - time_rh[0])
        mjd = mjdt[0:-1]


    # find indices of gaps  that are larger than a certain value
    ii = (gdiff > gap_min_val)
    #print('gap_min_val',gap_min_val, gdiff)
    N = len(mjd[ii])
    Ngdiff = len(gdiff)

    dlist = mjd_new_obstimes.tolist()


    # i have not figured this one out yet ... the horror
    #if not multiyear:
    if True:
    # get the integer values to write out  to the text file ...
        theyear = [y.year for y in dlist ]
        xm = [y.month for y in dlist]; xd = [y.day for y in dlist]
        xh = [y.hour for y in dlist]; xmin = [y.minute for y in dlist]
        xs = [y.second for y in dlist]

        if (Ngdiff > 0):
            for i in range(0,Ngdiff):
                if ii[i]:
                    try:
                        e0 = mjd[i] ; e1 = mjd[i+1] # beginning and ending of the gap
                    except:
                        # alerted to this problem by Felipe Nievinski.  
                        print('>>>>  DUNNO, some problem with the spline - maybe gap at end of day',mjd[i])
                        continue
                    bad_indices = (mjd_new > e0) & (mjd_new < e1 )
                    spline_new[bad_indices] = np.nan
                    mjd_new_obstimes[bad_indices] = np.datetime64("NaT")

    # write the spline values to a file, with gaps removed
        for i in range(0,N_new):
            if not np.isnan(spline_new[i]):
                rhout = spline_new[i]
                if csvfile:
                    fout.write('{0:15.7f}, {1:10.3f},{2:4.0f},{3:3.0f},{4:3.0f},{5:3.0f},{6:3.0f},{7:3.0f},{8:10.3f} \n'.format( mjd_new[i], rhout, theyear[i], xm[i], xd[i], xh[i], xmin[i], xs[i], H0-rhout))
                else:
                    fout.write('{0:15.7f}  {1:10.3f} {2:4.0f} {3:3.0f} {4:3.0f} {5:3.0f} {6:3.0f} {7:3.0f} {8:10.3f} \n'.format(mjd_new[i], rhout, theyear[i], xm[i], xd[i], xh[i], xmin[i], xs[i], H0-rhout))
            else:
                if gap_flag: 
                    rhout = spline_new[i]
                    if csvfile:
                        fout.write('{0:15.7f}, {1:10.3f},{2:4.0f},{3:3.0f},{4:3.0f},{5:3.0f},{6:3.0f},{7:3.0f},{8:10.3f} \n'.format( mjd_new[i], 999, theyear[i], xm[i], xd[i], xh[i], xmin[i], xs[i], 999))
                    else:
                        fout.write('{0:15.7f}  {1:10.3f} {2:4.0f} {3:3.0f} {4:3.0f} {5:3.0f} {6:3.0f} {7:3.0f} {8:10.3f} \n'.format(mjd_new[i], 999, theyear[i], xm[i], xd[i], xh[i], xmin[i], xs[i], 999))


    fout.close()

    fig=plt.figure(figsize=(10,5))
    plt.plot(mjd_new_obstimes, H0 -spline_new, 'b-',linewidth=2)
    plt.grid()
    plt.ylabel('meters',fontsize=fs)
    plt.title(station.upper() + ' Water Level from GNSS-IR', fontsize=fs)
    fig.autofmt_xdate()

    pfile = txtdir + '/' + station + '_H0.png'
    g.save_plot(pfile)

    return

def pickup_subdaily_json_defaults(xdir, station, extension):
    """
    picks up an existing gnssir analysis json. augments
    with subdaily parameters if needed. Returns the dictionary.

    Parameters
    ----------
    xdir : str
        REFL_CODE code location
    station : str
        name of station
    extension : str
        possible extension location

    Returns
    -------
    lsp : dictionary 
        contents of gnssir json
    """

    # changed default in subdaily to None instead of '' So have to check
    if extension is None:
        lsp = guts2.read_json_file(station, '',noexit=True)
    else:
        lsp = guts2.read_json_file(station, extension,noexit=True)

    # check json for subdaily settings
    # if values not found, then set them to None

    if 'subdaily_ampl' not in lsp:
        lsp['subdaily_ampl'] = None

    if 'subdaily_spline_outlier1' not in lsp:
        lsp['subdaily_spline_outlier1'] = None

    if 'subdaily_spline_outlier2' not in lsp:
        lsp['subdaily_spline_outlier2'] = None

    if 'subdaily_knots' not in lsp:
        lsp['subdaily_knots'] = None

    if 'subdaily_delta_out' not in lsp:
        lsp['subdaily_delta_out'] = None

    if 'subdaily_alt_sigma' not in lsp:
        lsp['subdaily_alt_sigma'] = None

    if 'subdaily_sigma' not in lsp:
        lsp['subdaily_sigma'] = None

    if 'subdaily_subdir' not in lsp:
        lsp['subdaily_subdir'] = None

    return lsp

def flipit3(tvd,col):
    """
    Third version of the flipit code. It takes a time series of RH values, extracts 
    24 hours of observations from the beginning and end of the series, uses
    them as fake data to make the spline fit stable.  
    Also fill the temporal gaps with fake data
    Previous versions assumed you were going to have full days of data at the beginning
    and end of the series.

    This version uses MJD rather than day of year for x-axis

    Parameters
    ----------
    tvd : numpy array of floats
        output of LSP runs. 
    col : integer
        column number (in normal speak) of the RH results
        in python-speak, this will have one subtracted from it

    Returns
    -------
    tnew : numpy array of floats
        time in MJD
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

    # these are in MJD 
    day0= tnew[0] # first observation time
    dayN = tnew[-1] # last observation time

    # these are the times relative to time zero
    middle = tnew-day0

    # use the first day
    ii = tnew < (day0+1)
    leftTime = -(tnew[ii]-day0)
    leftY = ynew[ii]

    # now use the last day. no idea if this will work
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

def the_last_plot(tv,station,plotname):
    """
    simple - reveresed - reflector height plot

    Parameters
    station : str
        station name, four characters
    tv : numpy array
        output of the subdaily code
    plotname : str
        where the plot should be stored

    """
    fs = 10
    obstimes = mjd_to_obstimes(tv[:,15])
    final_rh = tv[:,24]
    # new plot
    fig=plt.figure(figsize=(10,4))
    plt.plot(obstimes,final_rh, 'b-')
    plt.title
    plt.ylabel('meters')
    plt.title(station.upper() + ' : GNSS-IR Reflector Height') 
    plt.gca().invert_yaxis()
    plt.grid()
    fig.autofmt_xdate()

    plt.savefig(plotname,dpi=300)
    print('Plot file for final RH saved as: ', plotname)
    # don't plot to the screen
    plt.close()

