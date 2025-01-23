import argparse
import numpy as np
import gnssrefl.gps as g
import os
import sys


def check_l2(i,savebase,nsat_line1, lines,nlin,l2index,year,doy,screenstats):
    """
    Parameters
    ----------
    i : int
        line number index in RINEX file
    savebase : str
        list of satellites at first epoch
    nsat_line1 : int
        number of satellites in first epoch
    nlin :  int
        number of lines per satellite allocated in RINEX file
    l2index : int
        index of L2 observable
    year : int
        full year
    doy : int
        day of year
    screenstats : bool
        print extra info to the screen

    """
    l2c_sat, l5_sat = g.l2c_l5_list(year,doy)
    ii = i+2
    if (nsat_line1 > 12):
        base2 = lines[i+2][31:80].strip()
        savebase = savebase + base2
        ii = i + 3
    if (nsat_line1 > 24):
        base3 = lines[i+3][31:80].strip()
        savebase = savebase + base3
        ii = i + 4
    if (nsat_line1 > 36):
        print('Too many satellites - submit a PR to update the code.')
        sys.exit()

    print('Satellites at first epoch:', savebase, '\n')
    lines2read = nsat_line1 * nlin
    #print('linesto read ', lines2read)
    isat = 0 ; l2psats = 0; foundGPS = 0 ; l2cfound = 0
    total_gps = 0

    # startI is to start the incrementing in the right line
    # l2i is the index on a single line (rather than how RINEX stored it)
    if l2index < 5:
        startI = 0
        l2i = l2index*16
    elif l2index >= 5 | l2index < 10:
        startI = 1
        l2i = (l2index - 5)*16
    elif l2index >= 10:
        startI = 2
        l2i = (l2index - 10)*16
    else:
        print('Too many observables - I am tired of reading RINEX 2.11 files.')
        print('Feel free to fix this code and submit a pull request')
        sys.exit()

    if screenstats:
        print('loop' , ii, ii+lines2read, nlin)
    for ij in range(ii, ii+lines2read,nlin):
        if savebase[isat:isat+1] != 'G':
            #print('Skipping ', savebase[isat:isat+3])
            okok = 1
        else:
            foundGPS = foundGPS + 1
            GPSnum = int ( savebase[isat+1:isat+3] )
            total_gps = total_gps + 1
            if GPSnum in l2c_sat:
                if screenstats: 
                    print('found GPS satellite that could be L2C quality ', GPSnum)
                l2cfound = l2cfound + 1
            else:
                if screenstats: 
                    print('found non-L2C transmitting GPS satellite ', GPSnum)


            for k in range(startI,startI+1):
                eek = lines[ij+k][l2i:l2i+16]
                if screenstats:
                    print('Checking LLI status on ', eek)
                # 4 is what RINEX 2.11 uses for non-code tracking
                if (eek[14:15] == ' '): 
                    if screenstats: 
                        print('       possibly good L2C data')
                elif (eek[14:15] =='0') : 
                    if screenstats: 
                        print('       possibly good L2C data')
                else:
                    if (int(eek[14:15]) >= 4): 
                        l2psats = l2psats + 1
                        if screenstats: 
                            print('       Unfortunately this appears to be low-quality L2P data')
                if float(eek[0:14]) == 0: 
                    if screenstats: 
                        print('       Observation appears to be zero. So that is not good')
                    l2psats = l2psats + 1


        isat = isat + 3

    print('\nFound ', l2cfound, ' GPS satellites that could possibly be L2C in first epoch')
    print('Your file seems to have ', total_gps-l2psats, ' valid L2C SNR observations')  

def check_rinex_file(rinexfile,screenstats):
    """
    commandline tool to look at header information in a RINEX file
    tries to look for existence of L2C data

    Example
    -------

    check_rinex_file p0311520.21o

    Parameters
    ----------
    rinexfile : str
        name of the RINEX 2.11 file
    screenstats : bool
        extra info sent to the screen

    """
    last = rinexfile[-12:]
    year = 2000 + int(last[-3:-1])
    doy = int(last[4:7])
    # assume no coordinates in the file
    recx=0; recy = 0; recz = 0
    if os.path.exists(rinexfile):
        f=open(rinexfile,'r')
        lines = f.read().splitlines(True)
        lines.append('') # do not know why this is here
        eoh=0
        firstO = True
        for i,line in enumerate(lines):
            #print('reading ', line)
            eoh+=1
            base = line[0:60].strip()
            if ("END OF HEADER" in line) or (eoh > 250):

                print('Observables: ',obs)
                observables = obs.split()
                #print(Nobservables)
                if numobs > 20:
                    print('Too many observables for this simple code.')
                    print('Current max is 20 ... feel free to submit PR')
                    sys.exit()
                # first line of satellites
                base = lines[i+1][0:60].strip()
                savebase = lines[i+1][32:80].strip() 

                nsat_line1 = int(base[28:31])
                print('Number of satellites at first epoch: ' , nsat_line1)
                base2 = ''
                ii = i+2 # this is an index in the RINEX file
                if 'L2' in observables:
                    l2index = observables.index('L2')
                    if screenstats:
                        print('l2index in python speak ',l2index)
                    check_l2(i,savebase,nsat_line1, lines,nlin,l2index,year,doy,screenstats)
                    
                else:
                    print('\nWe cannot check for L2C unless the L2 observable is present')

                #print('\n')
                #if ('G' in savebase):
                #    print('Found GPS Data')
                #if ('E' in savebase):
                #    print('Found Galileo Data')
                #if ('R' in savebase): 
                #    print('Found Glonass Data')
                #print('\n')
                break
            else:
                desc = line[60:80].strip()
            if ('APPROX POSITION XYZ') in desc:
                print('Receiver coordinates (m):', line[:60].strip(),'\n')
                base = line[0:60]

                recx = float(base[0:14])
                recy = float(base[14:28])
                recz = float(base[28:42])
                #print(recx,recy,recz)
            if ('REC #') in desc:
                print('Receiver information: ', line[:60].strip())
            if ('ANT #') in desc:
                print('Antenna information:  ',line[:60].strip())
            if ('INTERVAL') in desc:
                print('Sampling interval    :  ',line[:60].strip())
            if ('TYPES OF OBSERV') in desc:
                thisline = line[:60].strip()
                if firstO:
                    firstO = False
                    numobs = int(line[0:6].strip())
                    print('Number of observables',numobs)
                    if (np.remainder(numobs,5) == 0 ):
                        nlin = int(numobs/5)
                    else:
                        nlin = int(numobs/5) + 1
                    #print('number of lines/sat ', nlin)
                    obs = line[6:60]
                else:
                    obs = obs + '     ' + thisline


        if ('S' not in obs):
            print('WARNING: no SNR observables in this file. Exiting')
            sys.exit()
        #else:
        #    if 'S1' in obs:
        #        print('L1 SNR data column found')
        #    if 'S2' in obs:
        #        print('L2 SNR data column found')
        #    if 'S5' in obs:
        #        print('L5 SNR data column found')

        if (recx == 0) or (recy == 0):
            print('WARNING: useful receiver coordinates are not provided.')
            print('You need coordinates for gnssrefl to work properly. Exiting.')
            sys.exit()
    else:
        print('File was not found ', rinexfile)
        return

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("rinexfile", help="rinexfile 2.11 name", type=str)
    parser.add_argument("-screenstats", help="extra info will print to screen, default F. ", type=str)
    args = parser.parse_args()
    screenstats = False
    if args.screenstats == 'T':
        screenstats = True
    rinexfile = args.rinexfile
    if os.path.exists(rinexfile):
        check_rinex_file(rinexfile,screenstats)
    else:
        print('Your input file: ', rinexfile, ' does not exist ')

if __name__ == "__main__":
    main()

