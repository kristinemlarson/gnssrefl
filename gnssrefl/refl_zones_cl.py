#reflection zones command line function

import argparse
import numpy as np
import os
import sys

import gnssrefl.gps as g
import gnssrefl.refl_zones as rf


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('station', help='station', type=str)
    parser.add_argument('-azim1', help='start azimuth (0-360) ', type=int)
    parser.add_argument('-azim2', help='end azimuth (0-360) ', type=int)
    parser.add_argument('-el_list', nargs="*",type=float,  help='elevation angle list, e.g. 5 10 15  (default)')
    parser.add_argument('-lat', help='Latitude (deg), if station not in database', type=float, default=None)
    parser.add_argument('-lon', help='Longitude (deg), if station not in database', type=float, default=None)
    parser.add_argument('-el_height', help='Ellipsoidal height (m) if station not in database', type=float)
    parser.add_argument('-fr', help='1, 2, or 5 ', type=int)
    parser.add_argument('-RH', help='Reflector height (meters). Default is sea level', type=str, default=None)
    parser.add_argument('-system', help='default=gps, options are galileo, glonass, beidou', type=str)
    parser.add_argument('-output', help='default is the station name', type=str,default=None)


    args = parser.parse_args().__dict__

    return {key: value for key, value in args.items() if value is not None}

def reflzones(station: str, azim1: int=0, azim2: int=360, lat: float=0, lon: float=0, el_height: float=0, RH: str=None, fr: int = 1, el_list: float= [5, 10, 15],system: str = 'gps', output: str = None):
    """
    creates KML file for reflection zones to be used in Google Earth

    Parameters
    ----------
    station :  str
        station name
    azim1 : int
        min azimuth angle in deg

    azim2 : int
        max azimuth angle in deg
    lat : float 
        latitude  in deg

    lon : float
        longitude in deg

    el_height : float
        ellipsoidal height in m

    RH : str
        user input reflector height (m)

    fr : int
        frequency (1,2, or 5 allowed)

    el_list : list of float 
        elevation angles desired (deg)

    system : str
        name of constellation (gps,glonass,galileo, beidou allowed)

    output : str
        name for kml file, i.e. if you input test, the filename will be test.kml

    Returns
    -------
    Creates a KML file

    """

    # check that you have the files for the orbits on your local system
    foundfiles = rf.save_reflzone_orbits()    
    if not foundfiles:
        print('The orbit files needed for this code were either not found')
        print('or not downloaded successfully. They should be in the REFL_CODE/Files directory') 
        sys.exit()


    # check that EGM96 file is in your local directory
    foundfile = g.checkEGM()
    if (RH == None) and (not foundfile):
        print('EGM96 file is not online. It should be in the REFL_CODE/Files directory')

    # check the station coordinates in our database from the station name
    xlat, xlon, xel_height = g.queryUNR_modern(station)

    # if none found, they will need to have been input on the command line
    if (xlat == 0) and (xlon == 0):
        print('Using the input from the command line')
    else:
        lat = xlat; lon = xlon; el_height = xel_height

    geoidC = g.geoidCorrection(lat,lon)
    # calculate height above sea level
    sealevel = el_height - geoidC
    
    if fr not in [1,2,5]:
        print('Illegal frequency chosen: ',fr)
        return
    # default is to use sea level as reflector height.  if RH is set, use that instead
    if RH == None:
        h = sealevel
    else:
        h = float(RH)

    if h > 300:
        h = 2;
        print('This is a very large reflector height value. Reducing to 2.')

    print('Reflector height (m) ', np.round(h,3))
    
    if len(el_list) > 5:
        el_list = el_list[0:5]
        #print('elevation angle is',el_list)
        print('Elevation angle list is very long - reducing to five.')

    obsfile = rf.set_system(system)
    print('The code should use this orbit file: ', obsfile)
    x,y,z=g.llh2xyz(lat,lon,el_height)
    recv=np.array([x,y,z])
    # calculate rising and setting arcs for this site and the requested constellation
    azlisttmp= rf.rising_setting_new(recv,el_list,obsfile)
    azlist = rf.set_final_azlist(azim1,azim2,azlisttmp)

    # figure out where the output will go
    xdir = os.environ['REFL_CODE']
    if output == None: 
        output = xdir + '/Files/' + station 
    else:
        output = xdir + '/Files/' + output 

    # make the KML map file
    fz_maps = rf.make_FZ_kml(output,fr, el_list, h, lat,lon,azlist)

    if fz_maps == True:
        print('File is saved in ' , output + '.kml')
    else:
        print('Something went wrong, and the kml file was not created')



def main():
    args = parse_arguments()
    data = reflzones(**args)


if __name__ == "__main__":
    main()

