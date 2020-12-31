# various codes to update a SNR file to use new orbits
import numpy as np
import os
import subprocess
# my code
import gnssrefl.gps as g
import gnssrefl.rinex2snr as rnx



def rerun_lsp(station, year, doy, snrEnd, mac):
    """
    if an SNR file has been remade, this allows you to rerun the LSP code
    should change that code to a callable function, but hey, not there yet.
    kristine larson
    """
    print('try to run the LSP code')
    if (mac == True):
        subprocess.call(['gnssir', station, str(year), str(doy), '-snr',str(snrEnd)])
    else:
# use digital ocean setup - change to new package
        subprocess.call(['gnssir', station, str(year), str(doy), '-snr', str(snrEnd) ])

def gnss_stats(ffull):
    """
    send the filename and return the status, whihc is 0
    for gps only, 100 for gps+glonass, 200 for gps+glonass+galileo etc
    """
    # default 
    print('check the GNSS status of a file')
    stat = 0 # which is basically to do nothing ...
    x=np.loadtxt(ffull, comments='%')
    if len(x) > 0:
    # sat is in collumn 0
        sat = x[:,0] 
        glonass = len( x[(sat > 100) & (sat < 200),0] )
        gps = len( x[(sat < 33) ,0])
        galileo =  len( x[(sat > 200) & (sat < 300),0] )
        beidou =  len( x[(sat > 300) & (sat < 400),0] )
        if gps > 0:
            stat = 0
        if (gps > 0) & (glonass > 0):
            stat = 100
        if (gps > 0) & (glonass > 0) & (galileo > 0):
            stat = 200
        if (gps > 0) & (glonass > 0) & (galileo > 0) & (beidou > 0):
            stat = 300

        print('Obs: ', gps, 'GPS', glonass, 'GLO', galileo, 'GAL',beidou, 'B')
    return stat 

def check_gnss(station,year,doy,snrEnd,goal,dec_rate,receiverrate):
    """
    input snr filename (without directory)
    goal (as describedd in gnss_Stats), dec_rate (0 for nothing)
    and receiverrate ('low' or 'high')
    """
    exedir = os.environ['EXE']
    fortran = True # because it is me
    archive = 'all'
    rrate = receiverrate
    nol = False
    overwrite = True
    mac = False
    if exedir == '/Users/kristine/bin':
        mac = True

    fname,fname_xz = g.define_filename(station,year,doy,snrEnd)
    yy,month,day, cyyyy, cdoy, YMD = g.ydoy2useful(year,doy)
    f=fname

    print('decimation and receiver rate',dec_rate,receiverrate)

    xit = False
    if os.path.exists(fname):
        print('SNR file exists')
        xit = True
    elif os.path.exists(fname_xz): 
        print('xz file exists -unxz it ')
        subprocess.call(['unxz',fname_xz])
        xit = True
    if xit:
        satstat = gnss_stats(fname) 
        print('Current File Status',orbch(satstat))

        if (satstat < 100) and (goal == 100 ):
            print('Orbit goal: ',orbch(goal))
            orbtype = 'jax'
            f,orbdir,foundit=g.getsp3file_mgex(year,month,day,orbtype)
            if foundit:
                subprocess.call(['rm',fname]) # remove old file and make a new one
                rnx.run_rinex2snr(station, [year], [doy], snrEnd, orbtype, rrate,dec_rate,archive,fortran,nol,overwrite)
                rerun_lsp(station, year, doy, snrEnd, mac)
            else:
                print('bummer,no JAXA, I guess, try GFZ')
                orbtype = 'gbm'
                f,orbdir,foundit=g.getsp3file_mgex(year,month,day,orbtype)
                if foundit:
                    print('found GFZ orbit - make file')
                    rnx.run_rinex2snr(station, [year], [doy], snrEnd, orbtype, rrate,dec_rate,archive,fortran,nol,overwrite)
                    rerun_lsp(station, year, doy, snrEnd, mac)
                else:
                    print('no GFZ, will have to try GRG?')
        if (satstat < 200) and (goal == 200 ):
            print('Orbit goal: ',orbch(goal))
            orbtype = 'gbm'
            f,orbdir,foundit=g.getsp3file_mgex(year,month,day,orbtype)
            if foundit:
                subprocess.call(['rm',fname]) # remove old file and make a new one
                rnx.run_rinex2snr(station, [year], [doy], snrEnd, orbtype, rrate,dec_rate,archive,fortran,nol,overwrite)
                rerun_lsp(station, year, doy, snrEnd, mac)
            else:
                print('bummer,no GFZ orbit, I guess, try GRG')
                orbtype = 'grg'
                f,orbdir,foundit=g.getsp3file_mgex(year,month,day,orbtype)
                if foundit:
                    subprocess.call(['rm',fname]) # remove old file and make a new one
                    print('found French orbit - make snr file')
                    rnx.run_rinex2snr(station, [year], [doy], snrEnd, orbtype,rrate,dec_rate,archive,fortran,nol,overwrite)
                    rerun_lsp(station, year, doy, snrEnd, mac)
                else:
                    print('No German orbits. No French orbits. Were there ever American orbits?  Nah.')
        if (satstat == 200) and (goal == 200 ):
            print('You have what you wanted', satstat,goal)
        if (satstat == 100) and (goal == 100 ):
            print('You have what you wanted', satstat,goal)

    else:
        print('No SNR file was found, so attempt to create it')
        foundit = False
        print('Orbit goal: ',orbch(goal))
        if (goal == 100):
            orbtype = 'jax'
            f,orbdir,foundit=g.getsp3file_mgex(year,month,day,orbtype)
            if foundit:
                rnx.run_rinex2snr(station, [year], [doy], snrEnd, orbtype, rrate,dec_rate,archive,fortran,nol,overwrite)
                rerun_lsp(station, year, doy, snrEnd, mac)
            else:
                orbtype = 'gbm' ; print('try GFZ')
                f,orbdir,foundit=g.getsp3file_mgex(year,month,day,orbtype)
                if foundit: 
                    rnx.run_rinex2snr(station, [year], [doy], snrEnd, orbtype, rrate,dec_rate,archive,fortran,nol,overwrite)
                rerun_lsp(station, year, doy, snrEnd, mac)
        if (goal == 200):
            orbtype = 'gbm' ; print('try GFZ')
            f,orbdir,foundit=g.getsp3file_mgex(year,month,day,orbtype)
            if foundit:
                print('trying to use GBM')
                rnx.run_rinex2snr(station, [year], [doy], snrEnd, orbtype,rrate,dec_rate,archive,fortran,nol,overwrite)
                rerun_lsp(station, year, doy, snrEnd, mac)
            else:
                print('using French orbits, GRG '); orbtype = 'grg'
                f,orbdir,foundit=g.getsp3file_mgex(year,month,day,orbtype)
                if foundit:
                    rnx.run_rinex2snr(station, [year], [doy], snrEnd,orbtype,rrate,dec_rate,archive,fortran,nol,overwrite)
                    rerun_lsp(station, year, doy, snrEnd, mac)
        if (goal == 300):
            print('Sorry - I have not coded this up yet')

    return True

def orbch(goal):
    ch = ''
    if goal == 0:
        ch='GPS only'
    if goal == 100:
        ch='GPS+Glonass'
    if goal == 200:
        ch='GPS+Glonass+Galileo'
    if goal == 300:
        ch='GNSS'

    return ch
