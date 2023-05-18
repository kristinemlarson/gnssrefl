import numpy as np
import gnssrefl.gps as g
import sys

def decipher_argt(filename):
    """

    Returns
    -------
    t, prn, az, elv, snr, freq = read_nmea(fname)#read nmea files

    """
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
                    if (eleA < 30) & (dat > 0):
                        if (sat < 33):
                            igps = igps + 1
                            prn.append(sat)
                            freq.append('1')
                            t.append(sod) ; snr.append(dat) ; az.append(azimA) ; elv.append(eleA)
                        if (sat > 64) & (sat <=88):
                            iglo = iglo + 1
                            newsat = sat + 100  # this is wrong - but to be consistent with error in nmea2snr
                            prn.append(newsat)
                            t.append(sod) ; snr.append(dat) ; az.append(azimA) ; elv.append(eleA)
                            freq.append('1')
                        if (sat > 200) & (sat <=240):
                            igal = igal + 1
                            prn.append(sat)
                            freq.append('1')
                            t.append(sod) ; snr.append(dat) ; az.append(azimA) ; elv.append(eleA)

            except:
                iii = 0
    print(igal)
    print(iglo)

    return t,prn,az,elv,snr,freq



