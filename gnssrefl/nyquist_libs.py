import numpy as np
import os

import matplotlib.pyplot as plt
from matplotlib.figure import Figure


import gnssrefl.gps as g
import gnssrefl.refl_zones as rz

def pickup_files_nyquist(station,recv,obsfile,constel,e1,e2,reqsamplerate,hires_figs):
    """

    Parameters
    ----------
    station : str
        lowercase four character station name
    recv : numpy array
         Cartesian coordinates of station (m)
    obsfile : str
        name of orbit file
    constel : int
        requested constellation (1-4)
    e1 : float
        min elevation angle (deg)
    e2 : float
        max elevation angle (deg)
    reqsamplerate : float
        sample rate of receiver
    hires_figs : bool
        whether you want eps instead of png 

    """
    # for rising and setting arcs
    azlist = np.empty(shape=[0, 3])
    # max number of satellites in each constellation
    # blank,gps, glonass, galileo, beidou
    LV = [0,32,26,36,46]

    # these are in degrees and meters
    lat, lon, nelev = g.xyz2llhd(recv)
    # unit vectors for up, East, and North
    u, East,North = g.up(np.pi*lat/180,np.pi*lon/180)

    f = read_the_orbits(obsfile,constel)

#   examine all satellites - allN will have the nyquists in a list
    allN = np.empty(shape=[0, 2])
    e5 = 5.0
    lv = LV[constel] + 1
    for prn in range(1,lv):
        azlist = np.empty(shape=[0, 3])
        # find the orbit data for that prn number
        newf = f[ (f[:,0] == prn) ]
        if len(newf) > 0:
        # use this to get rising and setting first
            tvsave=rz.calcAzEl_newish(prn, newf,recv,u,East,North)
            nr,nc=tvsave.shape
            #print('shape of tvsave', nr,nc)
            el = tvsave[:,1] - e5
            for j in range(0,nr-1):
                az = round(tvsave[j,2],2)
                newl = [az, prn, e5]
                if ( (el[j] > 0) & (el[j+1] < 0) ) :
                    azlist = np.append(azlist, [newl], axis=0)
                if ( (el[j] < 0) & (el[j+1] > 0) ) :
                    azlist = np.append(azlist, [newl], axis=0)
            # so now you have a list of azimuths
            nrr,ncc = azlist.shape

            # for each rising or setting arc
            for k in range(0,nrr):
                azriseset = azlist[k,0]
                elev = tvsave[:,1]; azims = tvsave[:,2]; t = tvsave[:,3]
                # figure out the nyquist
                nq=rz.nyquist_simple(t,elev,azims, e1,e2,azriseset,reqsamplerate)
                # and then save it
                if not np.isnan(nq):
                    newl=[float(azriseset), float(nq)]
                    allN = np.append(allN, [newl], axis=0);
    nm = ['','GPS','GLONASS','GALILEO','BEIDOU']
    info = str(reqsamplerate) + ' sec sample rate/elev angles '  + str(e1) + '-' + str(e2) + ' ' + nm[constel]

    ny_plot(station,allN,info,hires_figs)


def ny_plot(station,allN, info,hires_figs):
    """
    allN is a numpy array of azimuth(deg)/nyquist(m)
    info is only needed for the title

    Parameters
    ----------
    station : str
        4 char station name

    allN : numpy array ?
        azimuth and nyquist answers
    info : str
        information for the title
    hires_figs : bool
        whether you want eps instead of png

    Returns
    -------
    pngfile : str
        name of plot file

    """
    # wavelengths in meters, being lazy
    l1 = 0.19029360
    l2 = 0.24421
    l5 = 0.254828048
    # defaults
    plot_l2 = True
    plot_l5 = True
    if 'GALILEO' in info:
        plot_l2 = False
    if 'GLONASS' in info:
        plot_l5 = False
    if 'BEIDOU' in info:
        # the beidou signal names are all messed up
        # but that is how they are stored in the RINEX files...
        plot_l5 = False

    #fig = Figure(figsize=(8,4),dpi=360)
    #fig,ax = fig.subplots()
    fig, ax = plt.subplots(figsize=(10,6))
    ax.plot(allN[:,0],allN[:,1],'bo',label='L1')
    if plot_l2:
        ax.plot(allN[:,0],l2*allN[:,1]/l1,'ro',label='L2')
    if plot_l5: 
        ax.plot(allN[:,0],l5*allN[:,1]/l1,'co',label='L5')
    ax.set_title(station + ': Maximum Resolvable RH /' + info, fontsize=14)
    ax.grid()
    ax.set_xlabel('Azimuth (deg)')
    ax.set_ylabel('meters')
    ax.set_xlim(0,360)
    ax.legend(loc="best")

    # checks that directory exists
    g.checkFiles(station, '')

    xdir = os.environ['REFL_CODE'] + '/Files/' + station + '/'


    # a little backwards ... 
    if hires_figs : 
        pngfile = xdir + station + '_maxRH.eps'
        fig.savefig(pngfile, format="eps")
    else:
        pngfile = xdir + station + '_maxRH.png'
        fig.savefig(pngfile, format="png")
    plt.show()
    print('Plot file stored in: ', pngfile)

    txtfile = xdir + station + '_maxRH.txt'
    print(txtfile)
    nr,nc = allN.shape
    N = len(allN)
    fout = open(txtfile, 'w+')
    fout.write('{0:s}  {1:s} \n'.format('%', station + ' ' + info ))
    fout.write('{0:s}  {1:s} \n'.format('%', 'Maximum Resolvable Reflector Height' ))
    for i in range(0,N):
        fout.write('{0:7.2f}  {1:7.2f} \n'.format(allN[i,0], allN[i,1]))
    fout.close()
    print('Writing txtfile to ', txtfile)

def read_the_orbits(obsfile,constel):
    """
    Parameters
    ----------
    obsfile : str
        name of the orbit file to be read
    constel : int
        which constellation (1-4), 1 for gps, 2 for glonass etc
    """
    f = np.genfromtxt(obsfile,comments='%')
    if (constel == 4):
        #print('found beidou')
        i = (f[:,0] < 38) | (f[:,0] > 40)
        f=f[i,:]
    return f

