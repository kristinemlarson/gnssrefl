# subdaily libraries
import datetime
import math
import matplotlib.pyplot as plt
import numpy as np
from astropy.time import Time

# my code
import gnssrefl.gps as g
import gnssrefl.gnssir_v2 as guts2

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


def write_spline_output(splineout, iyear, th, spline, delta_out, station, txtdir,Hortho):
    """
    Writing the output of the spline fit to the final RH time series.
    No output other than this text file.

    Parameters
    ----------
    splineout : bool
        whether file should be created
    iyear : int
        full year
    th : numpy array
        time values of some kind ... maybe fractional day of years?
    spline: fit
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

    if splineout:
        if delta_out == 0:
            print('No spline values will be written because the interval is set to zero.')
        else:
            firstpoint  = th[0]; lastpoint = th[-1]
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
            splinefileout =  txtdir + '/' + station + '_' + str(iyear) + '_spline_out.txt'
            print('Writing evenly sampled file to: ', splinefileout)
            fout = open(splinefileout,'w+')
            fout.write('{0:1s}  {1:30s}  \n'.format('%','This is NOT observational data - be careful when interpreting it.'))
            fout.write('{0:1s}  {1:30s}  \n'.format('%','If the data are not well represented by the spline functions, you will '))
            fout.write('{0:1s}  {1:30s}  \n'.format('%','have a very poor representation of the data. I am also writing out station '))
            fout.write('{0:1s}  {1:30s}  {2:8.3f} \n'.format('%','orthometric height minus RH, where Hortho (m) is ', Hortho  ))
            fout.write('{0:1s}  {1:30s}  \n'.format('%','This assumes RH is measured relative to the L1 phase center.  '))
            fout.write('{0:1s}  {1:30s}  \n'.format('%','MJD, RH(m), YY,MM,DD,HH,MM,SS, quasi-sea-level(m)'))

            dtime = False
            for i in range(0,N):
                modjul = g.fdoy2mjd(iyear,tplot[i])
                doy = math.floor(tplot[i])
                utc= 24*(tplot[i] - doy)
                bigt,yy,mm,dd,hh,mi,ss = g.ymd_hhmmss(iyear,doy,utc,dtime)
                if (tplot[i] > firstpoint) & (tplot[i] < lastpoint):
                    fout.write('{0:15.7f}  {1:10.3f} {2:4.0f} {3:2.0f} {4:2.0f} {5:2.0f} {6:2.0f} {7:2.0f} {8:10.3f} \n'.format(modjul, 
                        spline_even[i], yy,mm,dd,hh,mi,ss, Hortho-spline_even[i]))
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


def numsats_plot(station,tval,nval,Gval,Rval,Eval,Cval,txtdir,fs,hires_figs):
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

    """

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
    plotname = txtdir + '/' + station + '_Subnvals.png'
    if hires_figs:
        plotname = txtdir + '/' + station + '_Subnvals.eps'
        plt.savefig(plotname,dpi=300)
    else:
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

    plotname = txtdir + '/' + station + '_combined.png'
    if hires_figs:
        plotname = txtdir + '/' + station + '_combined.eps'
        plt.savefig(plotname,dpi=300)
    else:
        plt.savefig(plotname,dpi=300)
    print('Plot file saved as: ', plotname)

def stack_two_more(otimes,tv,ii,jj,stats, station, txtdir, sigma,kplt,hires_figs):
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
    if hires_figs:
        plotname = txtdir + '/' + station + '_outliers_wrt_az.eps'
    else:
        plotname = txtdir + '/' + station + '_outliers_wrt_az.png'

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
    if hires_figs:
        plotname = txtdir + '/' + station + '_outliers.eps'
        plt.savefig(plotname,dpi=300)
    else:
        plotname = txtdir + '/' + station + '_outliers.png'
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
        time of obs, day of year
    correction : numpy array
        rhcorrections in meters
    rhdot_at_th : numpy array of floats
        spline fit for rhdot in meters
    tvel : numpy array of floats
        time for surface velocity in days of year
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
    #th_obs = mjd_to_obstimes(th+mjd0)


    fig=plt.figure(figsize=(10,6))
    plt.subplot(2,1,1)
    plt.plot(th, correction,'b.')
    plt.ylabel('meters',fontsize=fs);
    plt.xlim((np.min(th), np.max(th)))
    plt.grid()
    plt.title('The RH correction from RHdot effect ')
    #plt.xlim((th_obs[0], th_obs[-1])) #fig.autofmt_xdate()

    plt.subplot(2,1,2)
    #mjd1 = g.fdoy2mjd(year, tvel[0] ) # MJD of first point
    #tvel_obs = mjd_to_obstimes(tvel+mjd1)

    # ???
    A1 = np.min(th)  ; A2 = np.max(th) 
    jj = (tvel >= A1) & (tvel <= A2)

    plt.plot(th, rhdot_at_th,'b.',label='at GNSS obs')
    # disaster - did not work
    #plt.plot(tvel_obs, yvel,'c-', label='spline fit')
    plt.plot(tvel[jj], yvel[jj],'c-', label='spline fit')
    plt.legend(loc="upper left")
    plt.grid()
    plt.title('surface velocity')
    plt.ylabel('meters/hour'); plt.xlabel('days of the year') 
    plt.xlim((A1,A2))
    #plt.xlim((th[0], th[-1])) #fig.autofmt_xdate()

    if hires_figs:
        g.save_plot(txtdir + '/' + station + '_rhdot3.eps')
    else:
        g.save_plot(txtdir + '/' + station + '_rhdot3.png')


def RH_ortho_plot( station, H0, year, th_even, spline_whole_time,txtdir, fs, time_rh, rh, gap_min_val):
    """
    Makes a plot of the final spline fit to the data. Output time interval controlled by the user.

    Parameters
    ----------
    station : str
        name of station, 4 ch
    H0 : float
        datum correction (orthometric height) to convert RH to MSL data, in meters
    year : int
        year of the time series (ultimately should not be needed)
    th_even : numpy of floats
        time in fractional days of of year, I think
    spline_whole_time : numpy of floats
        RH values (m)
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
    """


    # difference function to find time between all rh measurements
    gdiff = np.diff( time_rh )
    mjdx = g.fdoy2mjd(year, time_rh[0] ) # 
    mjdt = mjdx + (time_rh - time_rh[0])
    mjd = mjdt[0:-1]

    # MJD of the gdiff values
    # mjd = time_rh[0:-1] + mjdx
    #print('base value ', year, time_rh[0], mjdx, mjd[-1])

    # find indices of gaps  that are larger than a certain value
    ii = (gdiff > gap_min_val)
    N = len(mjd[ii])
    Ngdiff = len(gdiff)

    # figure out mjd of the first point
    mjd0 = g.fdoy2mjd(year, th_even[0])
    mjd_even = mjd0 + (th_even - th_even[0])  
    mjd_even_obstimes = mjd_to_obstimes(mjd_even)


    if (Ngdiff > 0):
        for i in range(0,Ngdiff):
            if ii[i]:
                e0 = mjd[i] ; e1 = mjd[i+1] # beginning and ending of the gap
                #newl = [ e0, e1 ]
                #print('gap', mjd[i],mjd[i+1])
                bad_indices = (mjd_even > e0) & (mjd_even < e1 )
                #mjd_even[bad_indices] = np.nan
                mjd_even_obstimes[bad_indices] = np.datetime64("NaT")


    fig=plt.figure(figsize=(10,5))
    plt.plot(mjd_even_obstimes, H0 -spline_whole_time, 'c')
    #plt.plot(mjd_even, H0 -spline_whole_time, 'c')
    plt.grid()
    plt.ylabel('meters',fontsize=fs)
    plt.title(station.upper() + ' Water Level ', fontsize=fs)
    fig.autofmt_xdate()

    pfile = txtdir + '/' + station + '_H0.png'
    g.save_plot(pfile)

def find_ortho_height(station,extension):
    """
    find orthometric (sea level) height used in plots

    Parameters
    ----------
    station : str
        4 ch station name
    extension : str
        gnssir analysis, extension mode

    Returns
    -------
    Hortho : float
        orthometric height from gnssir json analysis file.  calculates 
        it if not in the file
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
        time in days of year, including the faked data, used for splines
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
        first time (day of year) real RH measurement
    endT : float
        last time (day of year) for first real RH measurement

    """
    fig=plt.figure(figsize=(10,4))

    plt.plot(tnew,ynew, 'b.', label='obs+fake obs')
    i = (spl_x > beginT) & (spl_x < endT) # to avoid wonky points in spline
    plt.plot(spl_x[i],spl_y[i],'c-', label='spline')
    plt.title('Mirrored obs and spline fit ')
    plt.legend(loc="upper left")
    plt.ylabel('meters')
    plt.xlabel('days of the year')
    plt.xlim((beginT, endT))
    plt.grid()
    g.save_plot(txtdir + '/' + station + '_rhdot1.png')
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


def subdaily_resids_last_stage(station, year, th, biasCor_rh, spline_at_GPS, fs, strsig, hires_figs, 
                               txtdir, ii, jj, th_even,spline_whole_time):
    """
    Makes the final residual plot for subdaily (after RHdot and IF correction made).
    Returns the bad points ...


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
    # convert to mjd and then obstimes
    mjd0 = g.fdoy2mjd(year, th[0])
    th_obs = mjd_to_obstimes(mjd0 + th - th[0])
    mjd1 = g.fdoy2mjd(year, th_even[0])
    th_even_obs = mjd_to_obstimes(mjd1 + th_even - th_even[0])


    fig=plt.figure(figsize=(10,5))
    plt.plot(th_obs, biasCor_rh, 'b.', label='RH ' + strsig)
    plt.plot(th_even_obs, spline_whole_time, 'c-',label='spline')
    plt.plot(th_obs[ii], biasCor_rh[ii], 'rx', label='outliers')

    plt.legend(loc="best",fontsize=fs)
    plt.grid() ; plt.gca().invert_yaxis()
    plt.ylabel('meters',fontsize=fs); 
    #plt.xlabel('days of the year',fontsize=fs)
    plt.title(station.upper() + ' RH with RHdot and InterFrequency Corrections Applied',fontsize=fs)
    fig.autofmt_xdate()

    # put hires_figs boolean here
    if hires_figs:
        g.save_plot(txtdir + '/' + station + '_rhdot4.eps')
    else:
        g.save_plot(txtdir + '/' + station + '_rhdot4.png')

    fig=plt.figure(figsize=(10,5))
    plt.plot(th_obs, biasCor_rh - spline_at_GPS, 'b.',label='all residuals')
    plt.title('Station:' + station + ' Residuals to new spline fit',fontsize=fs)
    plt.grid()
    plt.ylabel('meters',fontsize=fs)
    #plt.xlabel('days of the year',fontsize=fs)

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

    plt.close() # dont send this figure to the screen

    return badpoints2