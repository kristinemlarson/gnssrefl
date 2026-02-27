import argparse
import json
import numpy as np
import os
import sys
from scipy.stats import skew, kurtosis as scipy_kurtosis

from pathlib import Path

from gnssrefl.gps import l2c_l5_list, l1c_list
from gnssrefl.utils import read_files_in_dir, FileTypes, FileManagement, circular_mean_deg, circular_distance_deg
import gnssrefl.gnssir_v2 as guts2
import gnssrefl.phase_functions as qp
from gnssrefl.phase_functions import get_vwc_frequency

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("-min_tracks", default=None, help="min number of daily tracks to keep the series (default is 100)", type=int)
    parser.add_argument("-minvalperday", default=None, help="min number of tracks needed on one day to compute VWC (default is 10)", type=int)
    parser.add_argument("-bin_hours", default=None, type=int, help="time bin size in hours (1,2,3,4,6,8,12,24). Default is 24 (daily)")
    parser.add_argument("-minvalperbin", default=None, type=int, help="min number of satellite tracks needed per time bin. Default is 5")
    parser.add_argument("-bin_offset", default=None, type=int, help="bin timing offset in hours (0 <= offset < bin_hours). Default is 0")
    parser.add_argument("-fr", default=None, help="frequency: 1 (L1), 20 (L2C), 5 (L5). Only L2C officially supported.", type=int)
    parser.add_argument("-extension", default='', help="analysis extension parameter", type=str)
    parser.add_argument("-tmin", default=0.05, help="min soil texture", type=float)
    parser.add_argument("-tmax", default=0.5, help="max soil texture", type=float)
    parser.add_argument("-warning_value", default=5.5, help="warning value, degrees, phaseRMS", type=float)

    args = parser.parse_args().__dict__

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def vwc_input(station: str, year: int, fr: str = None, min_tracks: int = 100, minvalperday : int = 10,
              bin_hours: int = None, minvalperbin: int = 5, bin_offset: int = None,
              extension : str='', tmin : float=0.05, tmax : float=0.5, warning_value :float=5.5 ):
    """
    Sets inputs for the estimation of vwc (volumetric water content).  Picks up reflector height (RH) results for a 
    given station and year-year end range and computes the RH mean values and writes them 
    to a file. These will be used to compute a consistent set of phase estimates.

    Secondarily, it will add vwc input parameters into the json previously created for RH estimates.
    If nothing is requested here, it will put the defaults in the file.  That json file is then used when 
    you run vwc.

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
        GPS frequency: 1 (L1), 20 (L2C), 5 (L5). Only L2C is officially supported.
    min_tracks : int, optional
        number of minimum daily tracks needed in order to keep that satellite track
    minvalperday : int, optional
        how many unique tracks are needed to compute a valid VWC measurement for a given day
    extension : str, optional
        strategy extension value (same as used in gnssir, subdaily etc)
    tmin : float, optional
        minimum soil moisture value
    tmax : float, optional
        maximum soil moisture value
    warning_value : float, optional
        for removing low quality satellite tracks when running vwc
        phase units, degrees

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

    # check that it is a nominally valid year and station name

    if (len(station) != 4):
        print('station name must be four characters. Exiting.')
        sys.exit()
    if (len(str(year)) != 4):
        print('Year must be four characters. Exiting.')
        sys.exit()

    # Use the new helper function to determine the frequency.
    fr_list = get_vwc_frequency(station, extension, fr)
    if len(fr_list) > 1:
        print("Error: vwc_input can only process one frequency at a time.")
        print("Please specify a single frequency with -fr or in the json file.")
        sys.exit()
    # Get the single frequency from the list (vwc command only supports 1 frequency)
    fr = fr_list[0]

    lsp = guts2.read_json_file(station, extension)
    ellist = lsp.get('ellist', [])
    if len(ellist) > 0:
        print('vwc_input does not support ellist. Please remove ellist from your json')
        print('and rerun gnssir_input with a single e1/e2 range before using vwc_input.')
        sys.exit()

    print('Minimum number of tracks required to save a series ', min_tracks)
    gnssir_results = []
    # removed the ability to look at multiple years
    # it failed and there is no need for it at this time
    y = year
    data_dir = xdir / str(y) / 'results' / station
    if extension:
        data_dir = data_dir / extension  # add extension subdirectory if specified
    result_files = read_files_in_dir(data_dir)
    if result_files == None:
        print('Exiting.')
        sys.exit()

    gnssir_results = np.asarray(result_files)

    # change it to a numpy array
    #gi = np.asarray(gnssir_results)
    # I transpose this because the original code did that.
    gnssir_results = np.transpose(gnssir_results) 


    # get the satellites for the requested frequency and most recent year
    if (fr == 1):
        l1_satellite_list = np.arange(1,33)
        satellite_list = l1_satellite_list

        # Uncomment to use experimental L1C_list function, for filtering to GPS BLock III
        #satellite_list = l1c_list(year, 365)
    elif (fr == 5):
        print('Using L5 satellite list for December 31 on ', year)
        l2c_sat, l5_sat = l2c_l5_list(year, 365)
        satellite_list = l5_sat
    else:  # fr == 20 (L2C)
        print('Using L2C satellite list for December 31 on ', year)
        l2c_sat, l5_sat = l2c_l5_list(year, 365)
        satellite_list = l2c_sat

    if len(gnssir_results) == 0:
        print('Found no results - perhaps wrong year? Please run gnssir first.')
        sys.exit()

    # window out frequency 20
    # the following function returns the index values where the statement is True
    frequency_indices = np.where(gnssir_results[10] == fr)

    reflector_height_gnssir_results = gnssir_results[2][frequency_indices]
    satellite_gnssir_results = gnssir_results[3][frequency_indices]
    azimuth_gnssir_results = gnssir_results[5][frequency_indices]

    b = 0

    apriori_array = []
    for satellite in satellite_list:
        sat_mask = satellite_gnssir_results == satellite
        sat_azimuths = azimuth_gnssir_results[sat_mask]
        if len(sat_azimuths) == 0:
            continue
        clusters = define_track_clusters(sat_azimuths)
        for cluster in clusters:
            track_avg_az = circular_mean_deg(cluster)
            mask = sat_mask & (circular_distance_deg(azimuth_gnssir_results, track_avg_az) <= 3)
            reflector_heights = reflector_height_gnssir_results[mask]
            azimuths = azimuth_gnssir_results[mask]
            if len(reflector_heights) > min_tracks:
                # Exclude bimodal RH distributions (high BC + low kurtosis)
                kurt = scipy_kurtosis(reflector_heights, fisher=False)
                bc = (skew(reflector_heights)**2 + 1) / kurt if kurt > 0 else 0
                if bc > 0.9 and kurt < 3:
                    print(f'  Excluding bimodal track: sat {satellite:2.0f} avgAz {track_avg_az:5.1f} (BC={bc:.3f}, n={len(reflector_heights)})')
                    continue

                b = b + 1
                average_azimuth = circular_mean_deg(azimuths)
                az_min = (average_azimuth - 3) % 360
                az_max = (average_azimuth + 3) % 360
                apriori_array.append([b, np.mean(reflector_heights), satellite, average_azimuth, len(reflector_heights), az_min, az_max])

    # Use FileManagement with frequency and extension support
    file_manager = FileManagement(station, 'apriori_rh_file', frequency=fr, extension=extension)
    apriori_path_f = file_manager.get_file_path()

    # save file

    if (len(apriori_array) == 0):
        print('Found no results - perhaps wrong year?')
        sys.exit()
    else:
        qp.write_apriori_rh(apriori_path_f, apriori_array, station, year, tmin, tmax)
        print('>>>> Apriori RH file written to ', apriori_path_f)

    lsp = guts2.read_json_file(station, extension)

    # new one for minimum normalized amplitude
    lsp['vwc_min_norm_amp'] = 0.5;

    # save the vwc specific values that might be useful
    lsp['vwc_warning_value'] = warning_value
    lsp['vwc_min_soil_texture'] = tmin
    lsp['vwc_max_soil_texture'] = tmax
    lsp['vwc_minvalperday'] = minvalperday # this is how many unique tracks you need on each day (legacy)
    lsp['vwc_minvalperbin'] = minvalperbin # preferred parameter for subdaily analysis
    lsp['vwc_min_req_pts_track'] = min_tracks # this is total number of days needed to keep a satellite
    
    # Add subdaily binning parameters if provided
    if bin_hours is not None:
        lsp['vwc_bin_hours'] = bin_hours
    if bin_offset is not None:
        lsp['vwc_bin_offset'] = bin_offset

    # Use FileManagement to get JSON file path with new directory structure
    json_manager = FileManagement(station, 'make_json', extension=extension)
    json_path = json_manager.get_file_path()

    with open(json_path, 'w+') as outfile:
        json.dump(lsp, outfile, indent=4)


def define_track_clusters(azimuths, gap_threshold=10):
    """Define satellite track clusters from observed azimuths.

    Groups azimuths into distinct tracks by sorting them on the circle,
    finding the largest gap (natural break), then splitting at any gap
    exceeding the threshold. Handles 0/360 wrap.

    Parameters
    ----------
    azimuths : array-like
        Observed azimuth values in degrees for a single satellite
    gap_threshold : float
        Minimum azimuth gap in degrees to split into separate tracks. Default 10.

    Returns
    -------
    list of numpy arrays
        Each array contains the azimuths belonging to one track.
    """
    az = np.sort(np.asarray(azimuths, dtype=float) % 360)
    n = len(az)
    if n == 0:
        return []
    if n == 1:
        return [az]

    # Compute gaps between consecutive sorted values (including wrap-around)
    gaps = np.empty(n)
    gaps[:-1] = np.diff(az)
    gaps[-1] = (az[0] + 360) - az[-1]

    # Reorder starting after the largest gap (natural circle break)
    start = (np.argmax(gaps) + 1) % n
    ordered_az = np.roll(az, -start)

    # Compute gaps in the reordered sequence, handling wrap
    ordered_gaps = np.diff(ordered_az)
    ordered_gaps[ordered_gaps < 0] += 360

    # Split at gaps exceeding threshold
    clusters = []
    current = [ordered_az[0]]
    for i in range(1, n):
        if ordered_gaps[i - 1] > gap_threshold:
            clusters.append(np.array(current))
            current = []
        current.append(ordered_az[i])
    clusters.append(np.array(current))

    return clusters


def main():
    args = parse_arguments()
    vwc_input(**args)


if __name__ == "__main__":
    main()
