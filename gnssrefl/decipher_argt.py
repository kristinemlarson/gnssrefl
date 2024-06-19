import numpy as np
import gnssrefl.gps as g
import os
import subprocess
import sys

import gnssrefl.xnmeasnr as xnmeasnr


def decipher_argt(station,filename,idec,snrname,orbfile,recx,csnr,year,month,day):
    """
    This is an attempt to properly model the satellite orbits.  It uses GNSS orbits
    from the GFZ and Fortran to compute azimuth and elevation angle.  
    Right now it is L1 only, but does allow Galileo, GPS, and Glonass.
    It does require that someone send a proper station location.

    This code was written specifically for a dataset collected in Argentina.
    It is not in NMEA format but was parsed from it.


    Parameters
    ----------
    station : str
        4 char id
    filename : str
        NMEA output from Argentina
    idec : int
        decimation interval, sec
    snrname : str
        ultimate output file
    orbfile : str
        sp3 filename
    recx : list of floats
        Cartesian station coordinates in meters
    csnr: str
        2 ch snr file choice, i.e. '66' or '99'
    year : int
        full yaer
    month : int
        calendar month
    day : int
        calendar day

    """
    if (len(snrname) > 132) or (len(orbfile) > 132):
        print('The orbit or SNR file name is too long.')
        print('Make your environment variable names shorter.')
        sys.exit()
    t = [] ; prn = [] ; az = [] ; elv = []; snr = [] ; freq = []
    # i do not know why the people that this code are using strings 
    # for frequency ... but so as to not break the code
    igal = 0; iglo = 0; igps = 0

    with open(filename, 'r') as f:
        lines = f.read().splitlines(True)
        for i in  range(0,86400):
            try:
                line = lines[i]
                obs = line.split(';')
                N = len(obs)
                time = obs[0]
                Hr = int(time[11:13] )
                minutes = int(time[14:16] )
                seconds = int(time[17:19] )
                sod =  Hr*3600 + minutes*60 + seconds

                for el in range(4,N-4,4):
                    sat = int(obs[el])
                    eleA = float(obs[el+3])
                    azimA = float(obs[el+2])
                    dat = float(obs[el+1])
                    if (eleA < 35) & (dat > 0):
                        if (sat < 33):
                            igps = igps + 1
                            prn.append(sat)
                            freq.append(1)
                            t.append(sod) ; snr.append(dat) ; az.append(azimA) ; elv.append(eleA)
                        if (sat > 64) & (sat <=88):
                            iglo = iglo + 1
                            newsat = sat + 100  -64 
                            prn.append(newsat)
                            t.append(sod) ; snr.append(dat) ; az.append(azimA) ; elv.append(eleA)
                            freq.append(1)
                        if (sat > 200) & (sat <=240):
                            igal = igal + 1
                            prn.append(sat)
                            freq.append(1)
                            t.append(sod) ; snr.append(dat) ; az.append(azimA) ; elv.append(eleA)

            except:
                iii = 0
    #print(igal,igps,iglo)
    message = 'None '
    xdir = os.environ['REFL_CODE']
    logdir = xdir + '/logs'
    # make sure this directory exists
    if not os.path.isdir(logdir):
        subprocess.call(['mkdir', logdir])

    # temporary file - will be deleted
    outputfile = logdir + '/' + station + 'tmp.txt'
    # write to file tod, iprn, s1, freq
    fout = open(outputfile, 'w+')
    fout.write('{0:15.4f}{1:15.4f}{2:15.4f} \n'.format(recx[0], recx[1],recx[2]) )
    fout.write('{0:6.0f}{1:6.0f}{2:6.0f} \n'.format(year, month, day) )
    for i in range(0,len(t)):
        # might as well decimate
        if ( (int(t[i]) % idec) == 0):
            fout.write('{0:8.0f} {1:3.0f} {2:6.2f} {3:1.0f} \n'.format(t[i], prn[i], snr[i],freq[i]) )
    fout.close()

    errorlog = logdir + '/' + station + '_nmea2snr_error.txt'

    in1 = g.binary(outputfile)
    in2 = g.binary(snrname)
    in3 = g.binary(orbfile)
    in4 = g.binary(csnr)
    in5 = g.binary(errorlog)
    xnmeasnr.foo(in1,in2,in3,in4,in5)
    subprocess.call(['rm',outputfile])


def new_azel(station,tmpfile,snrname,orbfile,csnr):
    """
    This is an attempt to properly model the satellite orbits.  It uses GNSS orbits
    from the GFZ and Fortran to compute azimuth and elevation angle.  
    Right now it is L1 only, but does allow Galileo, GPS, and Glonass.
    It does require that someone send a proper station location.


    Parameters
    ----------
    tmpfile: str
        NMEA output from Argentina
    snrname : str
        ultimaet output file
    orbfile : str
        sp3 filename
    csnr: str
        2 ch snr file choice, i.e. '66' or '99'

    """
    if (len(snrname) > 132) or (len(orbfile) > 132):
        print('The orbit or SNR file name is too long.')
        print('Make your environment variable names shorter.')
        sys.exit()
    # make sure this directory exists
    if not os.path.isdir('logs'):
        subprocess.call(['mkdir', 'logs'])

    errorlog = 'logs/' + station + '_nmea2snr_error.txt'

    in1 = g.binary(tmpfile)
    in2 = g.binary(snrname)
    in3 = g.binary(orbfile)
    in4 = g.binary(csnr)
    in5 = g.binary(errorlog)
    xnmeasnr.foo(in1,in2,in3,in4,in5)
    print('removing temporary file')
    subprocess.call(['rm',tmpfile])
