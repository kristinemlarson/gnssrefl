import numpy as np
import os
import subprocess
import gps as g


def rerun_lsp(station, year, doy, snrEnd, mac):
    """
    if an SNR file has been remade, this allows you to rerun the LSP code
    should change that code to a callable function, but hey, not there yet.
    kristine larson
    """
    if (mac == True):
# use poetry package manager
        subprocess.call(['poetry','run', 'python','gnssIR_lomb.py', station, str(year), str(doy), str(snrEnd), '0'])
    else:
# use digital ocean setup - change to new package
        subprocess.call(['gnssir', station, str(year), str(doy), '-snr', str(snrEnd) ])

def gnss_stats(ffull):
    """
    send the filename and return the status, whihc is 0
    for gps only, 100 for gps+glonass, 200 for gps+glonass+galileo etc
    """
    # default 
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

        print('Number of obs: ', gps,glonass,galileo, beidou)
    return stat 

def check_gnss(station,year,doy,snrEnd,goal,dec_rate,receiverrate):
    """
    input snr filename (without directory)
    goal (as describedd in gnss_Stats), dec_rate (0 for nothing)
    and receiverrate ('low' or 'high')
    """
    exedir = os.environ['EXE']
    mac = False
    if exedir == '/Users/kristine/bin':
        mac = True

    fname,fname_xz = g.define_filename(station,year,doy,snrEnd)
    yy,month,day, cyyyy, cdoy, YMD = g.ydoy2useful(year,doy)
    f=fname
    #year,month,day = g.ydoy2ymd(year, doy)

    print('decimation and receiver rate',dec_rate,receiverrate)

    xit = False
    if os.path.exists(fname):
        print('snr file exists')
        xit = True
    elif os.path.exists(fname_xz): 
        print('xz file exists ??')
        subprocess.call(['unxz',fname_xz])
        xit = True
    if xit:
        satstat = gnss_stats(fname) 
        print('satstat',satstat)

        if (satstat < 100) and (goal == 100 ):
            print(' gps only was found but you want gps and glonass')
            orbtype = 'jax'
            f,orbdir,foundit=g.getsp3file_mgex(year,month,day,orbtype)
            if foundit:
                subprocess.call(['rm',fname]) # remove old file and make a new one
                g.quick_rinex_snrC(year, doy, station, snrEnd, orbtype,receiverrate,dec_rate,'all')
                rerun_lsp(station, year, doy, snrEnd, mac)
            else:
                print('bummer,no JAXA, I guess, try GFZ')
                orbtype = 'gbm'
                f,orbdir,foundit=g.getsp3file_mgex(year,month,day,orbtype)
                if foundit:
                    print('found GFZ orbit - make file')
                    g.quick_rinex_snrC(year, doy, station, snrEnd, orbtype,receiverrate,dec_rate,'all')
                    rerun_lsp(station, year, doy, snrEnd, mac)
                else:
                    print('no GFZ, will have to try GRG?')
        if (satstat < 200) and (goal == 200 ):
            print('no galileo but you wanted galileo')
            orbtype = 'gbm'
            f,orbdir,foundit=g.getsp3file_mgex(year,month,day,orbtype)
            if foundit:
                subprocess.call(['rm',fname]) # remove old file and make a new one
                g.quick_rinex_snrC(year, doy, station, snrEnd, orbtype,receiverrate,dec_rate,'all')
                rerun_lsp(station, year, doy, snrEnd, mac)
            else:
                print('bummer,no GFZ orbit, I guess, try GRG')
                orbtype = 'grg'
                f,orbdir,foundit=g.getsp3file_mgex(year,month,day,orbtype)
                if foundit:
                    subprocess.call(['rm',fname]) # remove old file and make a new one
                    print('found French orbit - make snr file')
                    g.quick_rinex_snrC(year, doy, station, snrEnd, orbtype,receiverrate,dec_rate,'all')
                    rerun_lsp(station, year, doy, snrEnd, mac)
                else:
                    print('No German orbits. No French orbits. There never were American orbits, so I give up.')
        if (satstat == 200) and (goal == 200 ):
            print('you have what you wanted', satstat,goal)
        if (satstat == 100) and (goal == 100 ):
            print('you have what you wanted', satstat,goal)

    else:
        print('no snr file was found, so attempt to create it')
        foundit = False
        if (goal == 100):
            orbtype = 'jax'
            f,orbdir,foundit=g.getsp3file_mgex(year,month,day,orbtype)
            if foundit:
                g.quick_rinex_snrC(year, doy, station, snrEnd, orbtype,receiverrate,dec_rate,'all')
                rerun_lsp(station, year, doy, snrEnd, mac)
        # otherwise, use the other orbit sources because they should have galileo
            else:
                orbtype = 'gbm' ; print('try GFZ')
                f,orbdir,foundit=g.getsp3file_mgex(year,month,day,orbtype)
                if foundit:
                    g.quick_rinex_snrC(year, doy, station, snrEnd, orbtype,receiverrate,dec_rate,'all')
                    rerun_lsp(station, year, doy, snrEnd, mac)
                else:
                    print('using French orbit'); orbtype = 'grg'
                    f,orbdir,foundit=g.getsp3file_mgex(year,month,day,orbtype)
                    if foundit:
                        g.quick_rinex_snrC(year, doy, station, snrEnd, orbtype,receiverrate,dec_rate,'all')
                        rerun_lsp(station, year, doy, snrEnd, mac)


    return True
