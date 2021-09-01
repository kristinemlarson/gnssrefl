# command line tool to check a rinexfile for minimal
# information, i.e. receiver coordinates, SNR data.
# Kristine Larson August 30, 2021
import argparse
import os
import sys

def check_rinex_header(rinexfile):
    """
    command tool to look at header information
    """
    # assume no coordinates in the file
    recx=0; recy = 0; recz = 0
    if os.path.exists(rinexfile):
        f=open(rinexfile,'r')
        lines = f.read().splitlines(True)
        lines.append('') # do not know why this is herej
        eoh=0
        firstO = True
        for i,line in enumerate(lines):
            eoh+=1
            base = line[0:60].strip()
            if ("END OF HEADER" in line) or (eoh > 70):
                break
            else:
                desc = line[60:80].strip()
            if ('APPROX POSITION XYZ') in desc:
                print('Receiver coordinates (m):', line[:60].strip())
                base = line[0:60]

                recx = float(base[0:14])
                recy = float(base[14:28])
                recz = float(base[28:42])
                #print(recx,recy,recz)
            if ('REC #') in desc:
                print('Receiver information: ', line[:60].strip())
            if ('ANT #') in desc:
                print('Antenna information:  ',line[:60].strip())
            if ('TYPES OF OBSERV') in desc:
                thisline = line[:60].strip()
                if firstO:
                    firstO = False
                    numobs = int(line[0:6].strip())
                    print('Number of observables',numobs)
                    obs = line[6:60]
                else:
                    obs = obs + '     ' + thisline
        print(obs)
        if ('S' not in obs):
            print('WARNING: no SNR observables in this file')
        else:
            print('SNR data found')
        if (recx == 0) or (recy == 0):
            print('WARNING: useful receiver coordinates are not provided.')
    else:
        print('File was not found ', rinexfile)
        return

def main():

# must input start and end year
    parser = argparse.ArgumentParser()
    parser.add_argument("rinexfile", help="rinexfile name", type=str)
    args = parser.parse_args()
    rinexfile = args.rinexfile
    check_rinex_header(rinexfile)

if __name__ == "__main__":
    main()

