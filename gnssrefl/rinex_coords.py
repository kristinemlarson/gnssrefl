# -*- coding: utf-8 -*-
import argparse
import subprocess
import gnssrefl.gps as g

def main():
    """
    checks the first 100 lines of a rinex file in a quest to determine
    the approximate Cartesian coordinates, which are also displayed 
    on the screen in LLH. It does not care if it is rinex, hatanaka rinex,
    or rinex3. But it does require it to not be gzipped or unix compressed.
    If you would like that option, please submit a PR.

    Example
    -------
    rinex_coords p1013550.22o

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("rinexfile", help="filename ", type=str)

    args = parser.parse_args()


    fname = args.rinexfile
    cmd = 'head -100 ' + fname  + ' | grep POS'
    line=subprocess.getoutput(cmd)
    x= float(line.split()[0])
    y= float(line.split()[1])
    z= float(line.split()[2])
    xyz = [x,y,z]

    print("Cartesian (m) %15.4f %15.4f %15.4f " % (x, y, z) )
    lat,lon,h = g.xyz2llhd(xyz)
    print("Lat Lon Ht (deg deg m) %14.9f %14.9f %9.3f " % (lat, lon, h) )

if __name__ == "__main__":
    main()
