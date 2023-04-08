#reflection zones command line function

import argparse
import numpy as np
import os
import subprocess
import sys

import gnssrefl.gps as g
import gnssrefl.refl_zones as rf


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('station', help='station', type=str)
    parser.add_argument('-lat', help='Latitude (deg), if station not in database', type=float, default=None)
    parser.add_argument('-lon', help='Longitude (deg), if station not in database', type=float, default=None)
    parser.add_argument('-el_height', help='Ellipsoidal height (m) if station not in database', type=float,default=None)
    parser.add_argument('-fr', help='1, 2, or 5 ', type=int)
    parser.add_argument('-RH', help='Reflector height (meters). Default is sea level', type=str, default=None)
    parser.add_argument('-azim1', help='start azimuth (default is 0, negative values allowed) ', type=int,default=None)
    parser.add_argument('-azim2', help='end azimuth (default is 360) ', type=int,default=None)
    parser.add_argument('-el_list', nargs="*",type=float,  help='elevation angle list, e.g. 5 10 15  (default)')
    parser.add_argument('-azlist', nargs="*",type=float,  help='flexible azimuth angle list, e.g. 0 90 270 360, but must be positive ')
    parser.add_argument('-system', help='default=gps, options are galileo, glonass, beidou', type=str)
    parser.add_argument('-output', help='output filename. default is the station name with kml extension', type=str,default=None)


    args = parser.parse_args().__dict__

    return {key: value for key, value in args.items() if value is not None}

def reflzones(station: str, azim1: int=0, azim2: int=360, lat: float=None, lon: float=None, el_height: float=None, 
        RH: str=None, fr: int = 1, el_list: float= [], azlist : float=[], system: str = 'gps', output: str = None):
    """
    Creates a KML file for reflection zones to be used in Google Earth

    If station is in the UNR database, those lat/lon/el_height values are used. You may override those values 
    with the optional inputs.

    The output file will be stored in REFL_CODE/Files/kml unless you specify an output name. In that case
    it will go into your working directory

    Examples
    --------

    refl_zones p041 -RH 2

    refl_zones sc02 -fr 2 -azlist 40 240

    refl_zones p041 -RH 2 -system galileo

    Parameters
    ----------
    station : str
        station name
    azim1 : int, optional
        min azimuth angle in deg
    azim2 : int, optional
        max azimuth angle in deg
    lat : float, optional
        latitude in deg
    lon : float, optional
        longitude in deg
    el_height : float, optional
        ellipsoidal height in m
    RH : str, optional
        user-defined reflector height (m)
        default is to use sea level as the RH
    fr : int, optional
        frequency (1,2, or 5 allowed)
    el_list : list of floats
        elevation angles desired (deg)
        default is 5, 10, 15
    azlist : list of floats, optional
        azimuth angle regions (deg) Must be in pairs, i.e. 0 90 180 270
    system : str, optional
        name of constellation (gps,glonass,galileo, beidou allowed)
        default is gps
    output : str, optional
        name for kml file 

    Returns
    -------
    Creates a KML file

    """
    # changed name to be consistent with other codes
    az_sectors = azlist
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

    #print(lat,lon,el_height)
    if (lat is None) & (lon is None):
    # check the station coordinates in our database from the station name
        lat, lon, el_height = g.queryUNR_modern(station)
        if (lat == 0) and (lon == 0):
            print('Exiting.')
            sys.exit()
        else:
            print('using inputs:', lat, lon, el_height)
    else:
        print('using inputs:', lat, lon, el_height)

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

    if h < 0:
        print('This is an illegal RH: ',h, ' Exiting.')
        sys.exit()

    if h > 300:
        print('This is a very large reflector height value:', round(h,2), '(m). Try setting RH. Exiting.')
        sys.exit()

    print('Reflector height (m) ', np.round(h,3))

    # set the default
    if len(el_list) == 0:
        el_list = [5, 10, 15]
    
    if len(el_list) > 5:
        el_list = el_list[0:5]
        print('Elevation angle list is very long - reducing to five.')

    emax = 31 # degrees for now

    print(all(x < 50 for x in el_list))

    if not (all(x < emax for x in el_list)):
        print('Right now we have an emax of 30 degrees. Resubmit your request.')
        sys.exit()


    obsfile = rf.set_system(system)
    print('The code should use this orbit file: ', obsfile)
    x,y,z=g.llh2xyz(lat,lon,el_height)
    recv=np.array([x,y,z])
    # calculate rising and setting arcs for this site and the requested constellation
    azlisttmp= rf.rising_setting_new(recv,el_list,obsfile)
    if len(az_sectors) == 0:
        print('Using one set of azimuths') 
        azlist = rf.set_final_azlist(azim1,azim2,azlisttmp)
    else:
        NL = len(az_sectors)
        if (np.mod(NL,2) != 0):
            print('Your azimuth sector list does not have pairs of azimuths. Exiting')
            sys.exit()
        for ii in range(0,NL):
            if (az_sectors[ii] < 0):
                print('Negative azimuths not allowed. Exiting')
                sys.exit()
            if (az_sectors[ii] > 360):
                print('Azimuths greater than 360 not allowed. Exiting')
                sys.exit()

        for ii in range(0,int(NL/2)):
            if (az_sectors[ii*2] > az_sectors[ii*2+1]):
                print('Sectors must have increasing azimuth values. Exiting')
                sys.exit()

        print('Using sectors')
        azlist = rf.set_azlist_multi_regions(az_sectors,azlisttmp)

    # figure out where the output will go
    # changed it so it  goes to a subdirectory called "kml" by default 


    # if you set a filename, the output will be written there in the user directory
    # you need to set the kml to the ending.
    # if you use defaults, it is written in 

    if output == None: 
    # first check that the Files output directory exists
        xdir = os.environ['REFL_CODE']
        outputdir = xdir + '/Files' 
        if not os.path.isdir(outputdir):
            subprocess.call(['mkdir',outputdir])
        outputdir = xdir + '/Files/kml'  
        if not os.path.isdir(outputdir):
            subprocess.call(['mkdir',outputdir])
        output = outputdir  + '/' + station  + '.kml'

    # make the KML map file
    # 2023jan19 add station location
    fz_maps = rf.make_FZ_kml(station,output,fr, el_list, h, lat,lon,azlist)

    if fz_maps == True:
        print('File is saved in ' , output)
    else:
        print('Something went wrong, and the kml file was not created')



def main():
    args = parse_arguments()
    data = reflzones(**args)


if __name__ == "__main__":
    main()

