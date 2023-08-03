import argparse
import json
import os
import subprocess
import csv
import sys
from pathlib import Path
import requests
import numpy as np
import collections

import gnssrefl.gps as g
from gnssrefl.utils import str2bool
from datetime import datetime

from earthscope_sdk.auth.device_code_flow import DeviceCodeFlowSimple


def parse_arguments():
    # user inputs the observation file information
    parser = argparse.ArgumentParser()
    # required arguments
    parser.add_argument("station", help="station (lowercase)", type=str)
    # optional inputs
    parser.add_argument(
        "-lat",
        help="Latitude (deg), if station not in database",
        type=float,
        default=None,
    )
    parser.add_argument(
        "-lon",
        help="Longitude (deg), if station not in database",
        type=float,
        default=None,
    )
    parser.add_argument(
        "-height",
        help="Ellipsoidal height (m) if station not in database",
        type=float,
        default=None,
    )
    parser.add_argument(
        "-read_offset",
        default=None,
        type=str,
        help="append meta from GAGE offset file",
    )
    parser.add_argument(
        "-man_input", default=None, type=str, help="append meta from manual input"
    )
    parser.add_argument(
        "-overwrite", default=None, type=str, help="create new meta file"
    )

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = [
        "read_offset",
        "man_input",
        "overwrite",
    ]
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def make_meta(
    station: str,
    lat: float = None,
    lon: float = None,
    height: float = None,
    man_input: bool = True,
    read_offset: bool = False,
    overwrite: bool = False,
):
    """
    Make a json file that includes equipment metadata information.
    It saves your inputs to a json file saved in REFL_CODE/input/<station>_meta.json.

    If station is in the UNR database, those lat/lon/ht values are used. You may override those values
    with the optional inputs.

    The default is for the user to enter these values; multiple calls will append entries to the metadata array,
    unless the user sets overwrite to True.
    The user can attempt to extract some of this information from the GAGE offset file.
    GAGE file used is https://data.unavco.org/archive/gnss/products/offset/cwu.kalts_nam14.off (requires ES auth)
    [A caveat: this file is comprehensive for antennas changed by stations included in GAGE processing (n=~3k).
    Receivers are included, but incomplete.]

    Examples
    --------
    make_meta p038
        makes json meta file for p038; uses UNR coords and will request user manually populate meta info.
        If meta json already exists for p038, will append to existing file.

    make_meta test -lat 39.7417583 -lon -105.0706972 -height 1655
        makes json meta file for test; uses manually input coords and will request ueser manually populate meta info

    make_meta p038 -man_input False -read_offset True -overwrite True
        makes json meta file for p038; uses UNR coords, will not request user manually populate meta info but will
        extract available meta info from GAGE offset file.
        Will overwrite any existing meta json file for p038

    Parameters
    ----------
    station : str
        4 character station ID.

    lat : float, optional
        latitude in deg

    lon : float, optional
        longitude in deg

    height : float, optional
        ellipsoidal height in m

    read_offset : bool, optional
        set to True to parse GAGE offset file. default is False.

    man_input : bool, optional
        set to True to manually input equipment metadata. default is True.

    overwrite : bool, optional
        set to True to overwrite existing metadata file. default is False.

    """

    # make sure environment variables exist
    g.check_environ_variables()

    # meta json object path
    xdir = os.environ["REFL_CODE"]
    outputdir = xdir + "/input"
    if not os.path.isdir(outputdir):
        subprocess.call(["mkdir", outputdir])
    outputfile = outputdir + "/" + station + "_meta.json"

    # If no overwrite and a file already exists, read in existing meta json
    if (overwrite is False) and (os.path.isfile(outputfile)):
        with open(outputfile) as json_file:
            comp_dict = json.load(json_file)
            meta_dict = comp_dict["meta"]

    else:  # initialize empty meta_dict
        comp_dict = get_coords(station, lat, lon, height)
        meta_dict = {}

    # read in gage metadata file
    if read_offset:
        meta_dict = check_offsets(station, meta_dict)

    if man_input:
        meta_dict = meta_man_input(meta_dict)

    # sort by date
    meta_dict = collections.OrderedDict(sorted(meta_dict.items()))

    # add metad to complete dictionary
    comp_dict["meta"] = meta_dict
    
    print('writing meta json out to:', outputfile)
    with open(outputfile, "w+") as outfile:
        json.dump(comp_dict, outfile, indent=3)

def get_coords(station, lat, lon, height):
    """
    initializes metadata dictionary with lat lon ht keys, either from UNR database (default) or user entered

    Parameters
    ----------
    station : str
        4 character station ID.

    lat : float, optional, default is None
        latitude in deg

    lon : float, optional, default is None
        longitude in deg

    height : float, optional, default is None
        ellipsoidal height in m

    Returns
    ----------
    comp_dict : dict
        dictionary of metadata; keys 'lat','lon','ht' 'meta'.

    """

    if (lat is None) & (lon is None):
        # check the station coordinates in our database from the station name
        lat, lon, height = g.queryUNR_modern(station)
        if (lat == 0) and (lon == 0):
            print(
                "Manually input coords using -lat -lon -ht args for make_meta. \n Exiting."
            )
            sys.exit()
        else:
            print("Using inputs:", lat, lon, height)
    else:
        print("Using inputs:", lat, lon, height)

    comp_dict = {
        "station": station,
        "lat": "{:.4f}".format(lat),
        "lon": "{:.4f}".format(lon),
        "ht": "{:.4f}".format(height),
        "meta": {},
    }
    return comp_dict


def meta_man_input(meta_dict):
    """
    allows user to manually enter metadata information [Rx, Antenna, Dome, FW] at a given YYYY-mm-dd

    Parameters
    ----------
    meta_dict : dict
        dictionary of metadata; keys 'dates','current','previous'.

    Returns
    ----------
    meta_dict : dict
        dictionary of metadata; keys 'dates','current','previous'.
    """

    date_str = input(
        "You have chosen to manually enter a metadata state. \n Enter the date: (YYYY-mm-dd): "
    )
    # Check if datestring entered is a valid string
    date_valid = False
    while date_valid is False:
        try:
            date_valid = bool(datetime.strptime(date_str, "%Y-%m-%d"))

        except ValueError:
            date_str = input(
                "%s is not in the correct input date format.  Please re-enter the date: (YYYY-mm-dd): "
                % (date_str)
            )

    receiver = input(" Enter the receiver brand and model: ")
    antenna = input("Enter the antenna model: ")
    dome = input("Enter the radome 4 digit type or * if unknown: ")
    fw = input("Enter the receiver firmware or * if unknown: ")

    meta_dict[date_str] = {
        "state": receiver + " " + antenna + " " + dome + " " + fw,
    }
    return meta_dict


def get_es_sdk_headers():
    """
    checks for earthscope-sdk authentication token and refreshes
    repurposed from gnssrefl/kelly.py

    Returns
    ----------
    header : dict
        dictionary of es-sdk token

    """

    token_path = "./"
    device_flow = DeviceCodeFlowSimple(Path(token_path))

    print("Seeking permission from Earthscope to use their archive")
    try:
        # get access token from local path
        device_flow.get_access_token_refresh_if_necessary()
    except:
        # if no token was found locally, do the device code flow
        device_flow.do_flow()

    token = device_flow.access_token

    headers = {}
    headers["authorization"] = "Bearer " + token
    return headers


def check_offsets(station, meta_dict):
    """
    check GAGE processing offset file for sources of possible gnssrefl timeseries offsets
    currently only relevant for ~3k stations processed by GAGE

    Parameters
    ----------
    station : str
        4 character station ID.

    meta_dict : dict
        dictionary of metadata; keys 'dates','current','previous'.

    Returns
    ----------
    meta_dict : dict
        dictionary of metadata; keys 'dates','current','previous'.
    """
    offset_meta_dates = []
    offset_meta_dict_list = []

    url = "https://data.unavco.org/archive/gnss/products/offset/cwu.kalts_nam14.off"
    print("reading GAGE offset file at %s" % url)
    headers = get_es_sdk_headers()
    with requests.Session() as s:
        response = s.get(url, stream=True, headers=headers)
        decode_response = response.content.decode("utf-8")
        cr = list(csv.reader(decode_response.splitlines()))
        for row in cr:
            if (row[0][1:5] == station.upper()) and (len(row[0].split()) > 14):
                # DATE
                year = int(row[0].split()[1])
                month = int(row[0].split()[2])
                day = int(row[0].split()[3])

                offset_meta_dates.append(
                    datetime(year=year, day=day, month=month).strftime("%Y-%m-%d")
                )

                # Description
                ofs = row[0].split()[11]
                evt = row[0].split()[14]
                # todo handle (rare) cases when order in file is swapped
                if evt == "AN":
                    tmp_dict = {}
                    rx_array = np.empty(2, dtype="S15")
                    for i, state in enumerate(["state", "prior"]):
                        receiver = rx_array[i] = (
                            row[0].split()[24 - (i * 3)]
                            + " "
                            + row[0].split()[24 - (i * 3) + 1]
                        )
                        antenna = row[0].split()[19 - (i * 2)]
                        dome = row[0].split()[29 - (i * 2)]
                        tmp_dict[state] = "%s %s %s *" % (
                            receiver,
                            antenna,
                            dome,
                        )
                    swap = "ANT"
                    if rx_array[0] != rx_array[1]:
                        swap = "ANT/RX"
                    tmp_dict["swap"] = swap
                offset_meta_dict_list.append(tmp_dict.copy())

        offset_meta_dict = dict(zip(offset_meta_dates, offset_meta_dict_list))
        meta_dict = meta_dict | offset_meta_dict  # .copy()

    if len(offset_meta_dates) == 0:
        print("%s does not have an entry in GAGE offset file" % station)
    return meta_dict


def main():
    args = parse_arguments()
    make_meta(**args)


if __name__ == "__main__":
    main()
