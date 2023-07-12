import argparse
import json
import os
import subprocess
import datetime
import csv
import sys
import urllib.request
import numpy as np
import collections

import gnssrefl.gps as g
from gnssrefl.utils import str2bool


def parse_arguments():
    # user inputs the observation file information
    parser = argparse.ArgumentParser()
    # required arguments
    parser.add_argument("station", help="station (lowercase)", type=str)
    # optional inputs
    parser.add_argument(
        "-man_input_loc",
        default=False,
        type=str,
        help="manually input station location (bool)",
    )
    parser.add_argument(
        "-read_offset",
        default=False,
        type=str,
        help="append meta from GAGE offset file",
    )
    parser.add_argument(
        "-man_input", default=False, type=str, help="append meta from manual input"
    )
    parser.add_argument(
        "-overwrite", default=False, type=str, help="create new meta file"
    )

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = [
        "man_input_loc",
        "read_offset",
        "man_input",
        "overwrite",
    ]
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def make_meta(
    station: str,
    man_input_loc: bool = False,
    read_offset: bool = False,
    man_input: bool = True,
    overwrite: bool = False,
):
    """
    Make a json file that includes equipment metadata information.
    It saves your inputs to a json file which by default is saved in REFL_CODE/input/<station>_meta.json.

    The default is for the user to enter these values; multiple calls will append entries to the metadata array, unless the user sets overwrite to False.
    The user can attempt to pull some of this information from the GAGE offset file.
    [A caveat: this file is comprehensive for antenna's changed by stations included in GAGE processing (n=~3k).  Receivers are included, but incomplete.]

    Parameters
    ----------
    station : str
        4 character station ID.
    man_input_loc : bool
        set to true to manually input station coords (LLH or ECEF).
        default is false, in which case they are pulled from unr db
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
        comp_dict = get_coords(station, man_input_loc)
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
    with open(outputfile, "w+") as outfile:
        json.dump(comp_dict, outfile, indent=3)


def get_coords(station, man_input_loc):
    """
    initializes metadata dictionary with lat lon ht keys, either from UNR database (default) or user entered
    Parameters
    ----------
    station : str
        4 character station ID.
    man_input_loc : bool
        set to true to manually input station coords (LLH or ECEF).
        default is false, in which case they are pulled from unr db
    Returns
    ----------
    comp_dict : dict
        dictionary of metadata; keys 'lat','long','height' 'meta'.
    """
    if man_input_loc:
        geod = input(
            "You have chosen to manually enter the station location. \n Do you have geodetic coordinates? :"
        )
        geod = str2bool({"g": geod}, "g")["g"]

        if geod:
            lat = float(input("Enter the latitude:"))
            long = float(input("Enter the longitude of the station: "))
            height = float(input("Enter the height of the station: "))

        else:
            x = float(input("Enter the ECEF X coordinate:"))
            y = float(input("Enter the Y coordinate: "))
            z = float(input("Enter the Z coordinate: "))
            lat, long, height = g.xyz2llhd([x, y, z])
    else:
        lat, long, height = g.queryUNR_modern(station)
        if lat == 0:
            print(
                "Tried to find coordinates in our UNR database. gnssrefl wont work without knowing this"
            )
            sys.exit()

    comp_dict = {
        "station": station,
        "lat": "{:.4f}".format(lat),
        "long": "{:.4f}".format(long),
        "height": "{:.4f}".format(height),
        "meta": {},
    }
    return comp_dict


def meta_man_input(meta_dict):
    """
    allows user to manually enter metadata information [Rx, Antenna, Dome, FW] at a given YMD
    Parameters
    ----------
    meta_dict : dict
        dictionary of metadata; keys 'dates','current','previous'.
    Returns
    ----------
    meta_dict : dict
        dictionary of metadata; keys 'dates','current','previous'.
    """

    year = input(
        "You have chosen to manually enter a metadata state. \n Enter the 4 digit year: "
    )
    month = input("Enter the month number: ")
    day = input("Enter the day of month number: ")
    date_str = datetime.datetime(
        year=int(year), day=int(day), month=int(month)
    ).strftime("%Y-%m-%d")
    receiver = input(" Enter the receiver brand and model: ")
    antenna = input("Enter the antenna model: ")
    dome = input("Enter the radome 4 digit type or * if unknown: ")
    fw = input("Enter the receiver firmware or * if unknown: ")

    meta_dict[date_str] = {
        "state": receiver + " " + antenna + " " + dome + " " + fw,
    }
    return meta_dict


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
    response = urllib.request.urlopen(url)
    lines = [l.decode("utf-8") for l in response.readlines()]
    cr = csv.reader(lines)
    for row in cr:
        if row[0][1:5] == station.upper():
            # DATE
            year = int(row[0].split()[1])
            month = int(row[0].split()[2])
            day = int(row[0].split()[3])

            offset_meta_dates.append(
                datetime.datetime(year=year, day=day, month=month).strftime("%Y-%m-%d")
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
