import datetime
import numpy as np
import matplotlib.pyplot as plt
import sys


import gnssrefl.gps as g

def time_limits(wateryear,longer,end_doy):
    """
    pick up some time values for windowing RH/snow depth data

    Parameters
    ----------
    wateryear : int
        water year
    longer : bool
        whether you want a longer plot
    end_doy : int
        last day of the year in the water year you want snow depth calculated for 

    Returns
    -------
    starting : float
        start time, fractional (year + doy/365.25)
    ending : float
        end time, fractional (year + doy/365.25)
    left : datetime
        beginning for the plot in datetime
    right : datetime
        end for the plot in datetime
    """
    year = wateryear
    # now compute snow depth
    if longer:
        startdoy, cdoy, cyyyy, cyy = g.ymd2doy(year-1,8,1)
        # for plot
        left = datetime.datetime(year=year-1, month=8, day = 1)
    else:
        startdoy, cdoy, cyyyy, cyy = g.ymd2doy(year-1,10,1)
        left = datetime.datetime(year=year-1, month=10, day = 1)

    # xaxis limit for the plot
    if end_doy is None: 
        right = datetime.datetime(year=year, month=6, day = 30)
        enddoy, cdoy, cyyyy, cyy = g.ymd2doy(year,6,30)
    else:
        # doy to mmdd and vice versa.  grrr
        yy,mm,dd, cyyyy, cdoy, YMD = g.ydoy2useful(year,end_doy)

        right = datetime.datetime(year=year, month=mm, day = dd)
        enddoy, cdoy, cyyyy, cyy = g.ymd2doy(year,mm,dd)

    # simple minded extracting the data for given limits
    starting = year-1 + startdoy/365.25
    ending = year + enddoy/365.25

    return starting, ending, left, right


def writeout_snowdepth_v0(station,outputfile, usegps, snowAccum,yerr):
    """
    writes plain txt file with snow depth results

    Parameters
    ----------
    station : str
        4 char station name
    outputfile : str
        location of output file (plain txt)
    usegps : numpy array
        LSP results (year, doy, RH etc
    snowAccum: numpy array
        snow accumulation results in meters
    yerr: numpy array
        standard deviation of snow depth in meters

    Returns
    -------
    gobst : numpy array
        datetime useful for plotting

    """
    fout = open(outputfile, 'w+')
    line1 = '% snow depth for station ' + station
    line1a = '% values < 0.05 meters set to zero. bare soil based on average of all values.'
    line2 = '% year   doy  snowD(m) Std(m) Month Day   Nvals'
    line3 = '%  (1)   (2)    (3)     (4)   (5)   (6)    (7)'
    fout.write("{0:s}  \n".format(line1))
    fout.write("{0:s}  \n".format(line1a))
    fout.write("{0:s}  \n".format(line2))
    fout.write("{0:s}  \n".format(line3))


# make a datetime array for plotting the gps results
    gobst = np.empty(shape=[0, 1])
    for i in range(0,len(usegps)):
        y=int(usegps[i,0])
        m=int(usegps[i,4])
        d=int(usegps[i,5])
        doy=int(usegps[i,1])
        # number of values in the average
        nvals =int(usegps[i,3])
        # this is what we did in pboh2o
        if snowAccum[i] < 0.05:
            snowAccum[i] = 0

        gobst = np.append(gobst, datetime.datetime(year=y, month=m, day=d) )
        fout.write("{0:4.0f} {1:3.0f}  {2:8.3f}  {3:8.3f}  {4:2.0f}  {5:2.0f}   {6:3.0f} \n".format(y,doy,snowAccum[i], yerr[i], m, d, nvals))

    fout.close()

    return gobst

def writeout_azim(station, outputfile,usegps,snowAccum):
    """
    writes plain txt file with snow depth results
    this is for the azimuth leveling version

    Parameters
    ----------
    station : str
        4 char station name
    outputfile : str
        location of output file (plain txt)
    usegps : numpy array
        LSP results (year, doy, RH etc
    snowAccum: numpy array
        snow accumulation results in meters

    Returns
    -------
    gobst : numpy array 
        datetime useful for plotting
    snowAccum: numpy array 
        snow depth that has passed QC (meters)
    snowAccumError: numpy array 
        standard deviation of daily snow depth retrievals (meters)

    """
    yerr = 0;
# make a datetime array for plotting the gps results
    gobst = np.empty(shape=[0, 1])
    # open file and make a header
    fout = open(outputfile, 'w+')
    line0 = '% gnssrefl snow depth for station ' + station
    line1 = '% values < 0.05 meters set to zero. bare soil based on azimuth averages.'
    line2 = '% year   doy  snowD(m) Std(m) Month Day   Nvals'
    line3 = '%  (1)   (2)    (3)     (4)   (5)   (6)   (7) '
    fout.write("{0:s}  \n".format(line0))
    fout.write("{0:s}  \n".format(line1))
    fout.write("{0:s}  \n".format(line2))
    fout.write("{0:s}  \n".format(line3))

    # first need to make a daily average of results that passed hte azimuth bare soil
    # get the year values
    yvals = np.unique(usegps[:,0])
    snow = []
    yerr = []
    std= []
    for y in yvals:
        y=int(y) # make sure y is an integer
        for d in range(1,367): # life is short - just do all day of years
            i = (usegps[:,0] == y) & (usegps[:,1]== d)
            nvals = len(usegps[i,0])
            if (nvals >  0):
                snowv = np.mean(snowAccum[i])
                # std never lower than 2.5 cm
                std = max(0.025, np.std(snowAccum[i]))
        # this is what we did in pboh2o - 
                if snowv < 0.05:
                    snowv = 0
                # month and day
                mm = int(np.unique(usegps[i,3]))
                dd = int(np.unique(usegps[i,4]))
                # make up a list of results for the plot - will convert to np array later
                snow.append(snowv)
                yerr.append(std)

                gobst = np.append(gobst, datetime.datetime(year=y, month=mm, day=dd) )
                fout.write("{0:4.0f} {1:3.0f}  {2:8.3f}  {3:8.3f}  {4:2.0f}  {5:2.0f}   {6:3.0f} \n".format(y, d, snowv, std, mm, dd,nvals))
                #print(y,d,snowv)

    fout.close()
    if len(snow) == 0:
        print('Very likely this failed - and you do not have enough bare soil values')
    snow = np.asarray(snow)
    std = np.asarray(std)

    return gobst, snow, std


def snow_simple(station,gps,year,longer, doy1,doy2,bs,plt, end_dt,outputpng,outputfile,minS,maxS,barereq_days,end_doy):
    """
    simple snow depth algorithm

    Parameters
    ----------
    station : str
        4 ch station name
    gps : numpy array
        output of daily average RH file
        (year,doy,RH etc)
    year : int
        water year
    longer : bool
        whether you want the plot to include late summer
    doy1 : int
        day of year, beginning of bare soil 
    doy2 : int
        day of year, ending of bare soil 
    bs : int
        bare soil year
    plt : bool
        whether you want the plots displayed to the screen
    end_dt: datetime
        I think this is the datetime for the optional end of the plot  
    outputpng : str
        name of the output (plot) png file
    outputfile : str
        name of the output snowdepth txt file
    minS : float
        minimum snowdepth for plot (m)
    maxS : float
        maximum snowdepth for plot (m)
    barereq_days: int
        min number of days to believe a bare soil average
    end_doy : int
        last day of year you want a snow depth value for

    """
    ii = (gps[:,1] >= doy1) & ((gps[:,1] <= doy2) & (gps[:,0] == bs))

    baresoil = gps[ii,2]
    if len(baresoil) == 0:
        print('No values in the bare soil definition. Exiting')
        print('Current settings are ', bs, ' for days ', doy1, doy2)
        sys.exit()

    # require at least 15 values (set in snowdepth_cl.py)
    NB = barereq_days
    print('Found ', len(baresoil), ' daily bare soil values')
    if len(baresoil) < NB:
        print('Current settings for bare soil are year/', bs, ' for days ', doy1, doy2)
        print('Code requires: ', NB)
        sys.exit()

    noSnowRH = np.mean(baresoil)
    print('Bare Soil RH: ', '{0:7.3f}'.format( noSnowRH),'(m)' )

    starting, ending, left, right = time_limits(year, longer,end_doy)

    t = gps[:,0] + gps[:,1]/365.25
    ii = (t >= starting) & (t <=ending)
    usegps = gps[ii,:]
    if len(usegps) == 0:
        print('No data in this water year. Exiting')
        sys.exit()

    snowAccum = noSnowRH - usegps[:,2]
    # we do not allow negative snow depth ... or at least not < -0.025
    ii = (snowAccum > -0.025)
    usegps = usegps[ii,:]
    snowAccum = snowAccum[ii]
    # error bar is just the std about the mean.  so it is likely bigger than needed.
    yerr = usegps[:,6]

    gobst = writeout_snowdepth_v0(station,outputfile, usegps, snowAccum,yerr)

    # make a plot
    snowplot(station,gobst,snowAccum,yerr,left,right,minS,maxS,outputpng,plt,end_dt)


def snowplot(station,gobst,snowAccum,yerr,left,right,minS,maxS,outputpng,pltit,end_dt):
    """
    creates and displays snow depth plot. Saves to outputpng

    Parameters
    ----------
    station : str
        name of GNSS station
    gobts : datetime object
        time of measurements in datetime format
    snowAccum : numpy array
        snow depth (meters)
    yerr : numpy array
        snow depth error (meters)
    left : datetime obj
        min x-axis limit
    right : datetime obj
        max x-axis limit
    minS : float
        minimum snow depth (m)
    maxS : float
        maximum snow depth (m)
    outputpng : str
        name of output png file
    pltit : bool
        whether plot should be displayed to the screen
    end_dt : datetime
        user provided override date for the end of the plot
        if None, then ignore
    """
    fig,ax=plt.subplots()
    # try this
    ax.errorbar(gobst, snowAccum, yerr=yerr, fmt='.', color='blue')
#    plt.plot(gobst, snowAccum, 'b.',label='GPS-IR')
    plt.title('Snow Depth: ' + station)
    plt.ylabel('meters')
    plt.grid()

    if (end_dt is None):
        plt.xlim((left, right))
    else:
        plt.xlim((left, end_dt))

    fig.autofmt_xdate()
    if (minS is not None) and (maxS is not None):
        plt.ylim((-0.05+minS,maxS))

    plt.savefig(outputpng, dpi=300)
    if pltit:
        plt.show()

    return

def snow_azimuthal(station,gps,year,longer, doy1,doy2,bs,plt, end_dt,outputpng,outputfile,minS,maxS,barereq_days,end_doy):
    """
    azimuthal snow depth algorithm
    tries to determine the bare soil correction in 20 degree azimuth swaths

    Parameters
    ----------
    station : str
        4 ch station name
    gps : numpy array
        output of daily average RH file
        (year,doy,RH etc)
    year : int
        water year
    longer : bool
        whether you want the plot to include late summer
    doy1 : int
        day of year, beginning of bare soil
    doy2 : int
        day of year, ending of bare soil
    bs : int
        bare soil year
    plt : bool
        whether you want the plots displayed to the screen
    end_dt: datetime
        I think this is the datetime for the optional end of the plot
    outputpng : str
        name of the output (plot) png file
    outputfile : str
        name of the output snowdepth txt file
    minS : float
        minimum snowdepth for plot (m)
    maxS : float
        maximum snowdepth for plot (m)
    barereq_days : int 
        number of days required to trust a bare soil average
    end_doy : int
        last day of year you want to compute snow depth for

    """
    ii = (gps[:,1] >= doy1) & ((gps[:,1] <= doy2) & (gps[:,0] == bs))

    baresoilAll = gps[ii,:]
    baresoil = gps[ii,2] # 
    if len(baresoil) == 0:
        print('No values in the bare soil definition. Exiting')
        print('Current settings are ', bs, ' for days ', doy1, doy2)
        sys.exit()

    # require at least 15 values (this is not very useful)
    # this constraint is actually done later ...
    # could be removed
    NB = barereq_days
    if len(baresoil) < NB:
        print('Not enough values to define baresoil: ', NB)
        sys.exit()

    starting, ending, left, right = time_limits(year, longer,end_doy)

    # window current water year's data to within time limits
    t = gps[:,0] + gps[:,1]/365.25
    ii = (t >= starting) & (t <=ending)
    usegps = gps[ii,:]
    if len(usegps) == 0:
        print('No data in this water year. Exiting')
        sys.exit()

    # now get bare soil value for each 20 degree azimuth range
    # year, doy, snowAccum, avgAzim, Nval

    rebase = np.empty(shape=[0, 12])

    # how many degrees of azimuth are used in each "bare soil" correction
    delA = 20
    for az in range(0,360-delA,delA):
        # bare soil in the azimuth range
        jj = ( baresoilAll[:,5] >= az)  & (baresoilAll[:,5] <= (az+delA))
        pout = baresoilAll[jj,:]
        nr,nc=np.shape(pout)

        # all RH in the azimuth range
        kk = (usegps[:,5] > az) & (usegps[:,5] < (az+delA))
        # number of unique days where a bare soil retrieval exists
        ndoy = len(np.unique(pout[:,1]))
        if ndoy > NB:
            # what is the average RH value for this azimuth bin for bare soil
            bsoil = np.mean(pout[:,2])
            print('In azim. range ', az, az+delA, np.round(bsoil,2), '(m), nvals:', len(pout[:,2]),ndoy)

            gps_in_azim = usegps[kk,:]
            nr,nc = np.shape(gps_in_azim)

            onecol = bsoil + np.zeros((nr,1)) #

            # add a column with bare soil value
            newone = np.hstack((gps_in_azim, onecol))
            # then stack vertically
            rebase = np.vstack((rebase,newone))
            nr,nc=np.shape(rebase); #print(nr,nc)

    # calculate snow accumulation, remove negative values
    snowAccum = rebase[:,11]-rebase[:,2]
    # do not allow negative snow depth
    ii = (snowAccum > -0.025)
    rebase = rebase[ii,:]
    snowAccum = snowAccum[ii]

    #  write out results
    gobst,snowAccum,yerr = writeout_azim(station, outputfile,rebase,snowAccum)

    # make a plot
    snowplot(station,gobst,snowAccum,yerr,left,right,minS,maxS,outputpng,plt,end_dt)



