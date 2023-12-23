import argparse
import json
import numpy as np
import os
import sys

from pathlib import Path

from gnssrefl.gps import l2c_l5_list
from gnssrefl.utils import read_files_in_dir, FileTypes, FileManagement
import gnssrefl.gnssir_v2 as guts2


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("-min_tracks", default=None, help="min number of tracks to keep mean RH (default is 100)", type=int)
    parser.add_argument("-fr", default=None, help="frequency (default is L2C)", type=int)
    parser.add_argument("-extension", default='', help="analysis extension parameter", type=str)
    parser.add_argument("-tmin", default=0.05, help="min soil texture", type=float)
    parser.add_argument("-tmax", default=0.45, help="max soil texture", type=float)
    parser.add_argument("-warning_value", default=5.5, help="warning value, phaseRMS", type=float)

    args = parser.parse_args().__dict__

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def vwc_input(station: str, year: int, fr: int = 20, min_tracks: int = 100, 
              extension : str='', tmin : float=0.05, tmax : float=0.45, minvalperday : int = 5, warning_value :float=5.5 ):
    """
    Starts the analysis for volumetric water content.  Picks up reflector height (RH) results for a 
    given station and year-year end range and computes the RH mean values and writes them 
    to a file. These will be used to compute a consistent set of phase estimates.

    Secondarily, it will add vwc input parameters into the json previously created for RH estimates.
    If nothing is requested here, it will put the defaults in the file.  

    Examples
    --------
    vwc_input p038 2018
        standard usage, station and year inputs
         
    vwc_input p038 2018 -min_tracks 50
        allow fewer values to accept a satellite track
        default is 100

    Parameters
    ----------
    station : str
        4 character ID of the station
    year : int
        full year
    fr : int, optional
        GPS frequency. Currently only supports l2c, which is frequency 20.
    min_tracks : int, optional
        number of minimum tracks needed in order to keep the average RH
    extension : str, optional
        strategy extension value (same as used in gnssir, subdaily etc)
    tmin : float, optional
        minimum soil moisture value
    tmax : float, optional
        maximum soil moisture value
    minvalperday : int, optional
        how many unique tracks are needed to compute a valid VWC measurement for that day
    warning_value : float, optional
        for removing low quality satellite tracks when running vwc

    Returns
    -------
    File with columns
    index, mean reflector_heights, satellite, average_azimuth, number of reflector heights in average, min azimuth, max azimuth

    Saves to $REFL_CODE/input/<station>_phaseRH.txt


    Saves four vwc specific parameters to existing $REFL_CODE/input/<station>.json file

    vwc_minvalperday, vwc_min_soil_texture, vwc_max_soil_texture, vwc_min_req_pts_track, vwc_warning_value

    """
    # default l2c, but can ask for L1 and L2
    xdir = Path(os.environ["REFL_CODE"]) # for kelly enloe
    myxdir = os.environ['REFL_CODE'] # for kristine 


    if (len(station) != 4):
        print('station name must be four characters. Exiting.')
        sys.exit()
    if (len(str(year)) != 4):
        print('Year must be four characters. Exiting.')
        sys.exit()

    # not sure this is needed?
    if not min_tracks:
        min_tracks = 100

    print('Minimum number of tracks required ', min_tracks)
    gnssir_results = []
    # removed the ability to look at multiple years
    # it failed and there is no need for it at this time
    y = year
    data_dir = xdir / str(y) / 'results' / station
    result_files = read_files_in_dir(data_dir)
    if result_files == None:
        print('Exiting.')
        sys.exit()

    gnssir_results = np.asarray(result_files)

    # change it to a numpy array
    #gi = np.asarray(gnssir_results)
    # I transpose this because the original code did that.
    gnssir_results = np.transpose(gnssir_results) 


    # four quadrants
    azimuth_list = [0, 90, 180, 270]

    # get the satellites for the requested frequency (20 for now) and most recent year
    if (fr == 1):
        l1_satellite_list = np.arange(1,33)
        satellite_list = l1_satellite_list
        apriori_path_f = myxdir + '/input/' + station + '_phaseRH_L1.txt'
    else:
        print('Using L2C satellite list for December 31 on ', year)
        l2c_sat, l5_sat = l2c_l5_list(year, 365)
        satellite_list = l2c_sat
        apriori_path_f = myxdir + '/input/' + station + '_phaseRH.txt'


    # window out frequency 20
    # the following function returns the index values where the statement is True
    frequency_indices = np.where(gnssir_results[10] == fr)

    reflector_height_gnssir_results = gnssir_results[2][frequency_indices]
    satellite_gnssir_results = gnssir_results[3][frequency_indices]
    azimuth_gnssir_results = gnssir_results[5][frequency_indices]

    b=0

    apriori_array = []
    for azimuth in azimuth_list:
        azimuth_min = azimuth
        azimuth_max = azimuth + 90
        for satellite in satellite_list:
            reflector_heights = reflector_height_gnssir_results[(azimuth_gnssir_results > azimuth_min)
                                                                & (azimuth_gnssir_results < azimuth_max)
                                                                & (satellite_gnssir_results == satellite)]
            azimuths = azimuth_gnssir_results[(azimuth_gnssir_results > azimuth_min)
                                              & (azimuth_gnssir_results < azimuth_max)
                                              & (satellite_gnssir_results == satellite)]
            if (len(reflector_heights) > min_tracks):
                b = b+1
                average_azimuth = np.mean(azimuths)
                #print("{0:3.0f} {1:5.2f} {2:2.0f} {3:7.2f} {4:3.0f} {5:3.0f} {6:3.0f} ".format(b, np.mean(reflector_heights), satellite, average_azimuth, len(reflector_heights),azimuth_min,azimuth_max))
                apriori_array.append([b, np.mean(reflector_heights), satellite, average_azimuth, len(reflector_heights), azimuth_min, azimuth_max])

    apriori_path = FileManagement(station, FileTypes("apriori_rh_file")).get_file_path()

    # save file

    if (len(apriori_array) == 0):
        print('Found no results - perhaps wrong year? or ')
    else:
        print('>>>> Apriori RH file written to ', apriori_path_f)
        fout = open(apriori_path_f, 'w+')
        fout.write("{0:s}  \n".format('% apriori RH values used for phase estimation'))
        l = '% year/station ' + str(year) + ' ' + station 
        fout.write("{0:s}  \n".format(l))
        fout.write("{0:s}  \n".format('% tmin 0.05 (default)'))
        fout.write("{0:s}  \n".format('% tmax 0.50 (default)'))
        fout.write("{0:s}  \n".format('% Track  RefH SatNu MeanAz  Nval   Azimuths '))
        fout.write("{0:s}  \n".format('%         m   ' ))

    #with open(apriori_path, 'w') as my_file:
        np.savetxt(fout, apriori_array, fmt="%3.0f %6.3f %4.0f %7.2f   %4.0f  %3.0f  %3.0f")
        fout.close()


    # read in existing information
    lsp = guts2.read_json_file(station, extension)

    # new one for minimum normalized amplitude
    lsp['vwc_min_norm_amp'] = 0.5;

    # save the vwc specific values that might be useful
    lsp['vwc_warning_value'] = warning_value
    lsp['vwc_min_soil_texture'] = tmin
    lsp['vwc_max_soil_texture'] = tmax
    lsp['vwc_minvalperday'] = minvalperday # this is how many unique tracks you need on each day 
    lsp['vwc_min_req_pts_track'] = min_tracks # this is total number of days needed to keep a satellite

    if len(extension)==0:
        instructions = str(os.environ['REFL_CODE']) + '/input/' + station + '.json'
    else:
        instructions = str(os.environ['REFL_CODE']) + '/input/' + station + '.' + extension + '.json'

    with open(instructions, 'w+') as outfile:
        json.dump(lsp, outfile, indent=4)


def main():
    args = parse_arguments()
    vwc_input(**args)


if __name__ == "__main__":
    main()
