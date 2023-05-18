import numpy as np
import gnssrefl.gps as g
import os
import subprocess
import sys

def decipher_argt(station,filename,outputfile,idec,snrname,orbfile,recx,csnr):
    """

    Parameters
    ----------
    station : str
        4 char id
    filename : str
        NMEA output from Argentina
    outputfile : str
    idec : int
        decimation interval, sec
    snrname : str
        ultimaet output file
    orbfile : str
        sp3 filename
    recx : list of floats
        Cartesian station coordinates in meters
    csnr: str
        2 ch snr file choice, i.e. '66' or '99'

    Returns
    -------
    t, prn, az, elv, snr, freq = read_nmea(fname)#read nmea files

    """
    t = [] ; prn = [] ; az = [] ; elv = []; snr = [] ; freq = []
    # i do not know why the people that this code are using strings 
    # for frequency ... but so as to not break the code
    igal = 0; iglo = 0; igps = 0
    print(recx)

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
                    if (eleA < 30) & (dat > 0):
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
    print(igal,igps,iglo)
    # write to file tod, iprn, s1, freq
    fout = open(outputfile, 'w+')
    fout.write('{0:15.4f} {1:15.4f} {2:15.4f} \n'.format(recx[0], recx[1],recx[2]) )
    for i in range(0,len(t)):
        if ( (int(t[i]) % idec) == 0):
            fout.write('{0:8.0f} {1:3.0f} {2:6.2f} {3:1.0f} \n'.format(t[i], prn[i], snr[i],freq[i]) )
    fout.close()


    #snrname = snrdir + rinex3[0:-3] + 'snr66'

    in1 = g.binary(outputfile)
    in2 = g.binary(snrname)
    in3 = g.binary(orbfile)

    if (len(snrname) > 132) or (len(orbfile) > 132):
        print('The orbit or SNR file name is too long.')
        print('Make your environment variable names shorter.')
        sys.exit()
    in4 = g.binary(csnr)

    message = 'None '
    # make sure this exists
    if not os.path.isdir('logs'):
        subprocess.call(['mkdir', 'logs'])
    errorlog = 'logs/' + station + '_hybrid_error.txt'
    in5 = g.binary(errorlog)
    #nmea_snr.foo(in1,in2,in3,in4,in5)


