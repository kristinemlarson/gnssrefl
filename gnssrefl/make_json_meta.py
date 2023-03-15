import argparse
import json
import os
import subprocess
import datetime
import csv
import urllib.request
import numpy as np

import gnssrefl.gps as g
from gnssrefl.utils import str2bool


def parse_arguments():
    # user inputs the observation file information
    parser = argparse.ArgumentParser()
    # required arguments
    parser.add_argument("station", help="station (lowercase)", type=str)
    # optional inputs
    parser.add_argument("-read_offset", default=False, type=str, help="append meta from GAGE offset file")
    parser.add_argument("-read_rnx", default=False, type=str, help="append meta from a designated rinex file")
    parser.add_argument("-man_input", default=False, type=str, help="append meta from manual input")
    parser.add_argument("-overwrite", default=False, type=str, help="create new meta file")

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['read_offset', 'read_rnx', 'man_input', 'overwrite']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def make_json(station: str, read_offset: bool = False, read_rnx: bool = False, man_input: bool = False,
              overwrite: bool = False):
    """
    Make a json file that includes equipment metadata information.

    Parameters
    ----------
    station : str
        4 character station ID.
    read_offset : bool, optional
        set to True to parse GAGE offset file. default is False.
    read_rnx : bool, optional
        set to True to read in user defined rinex header. default is False.
    man_input : bool, optional
        set to True to manually input equipment metadata. default is False.
    overwrite : bool, optional
        set to True to overwrite existing metadata file. default is False.
     """

    # make sure environment variables exist
    g.check_environ_variables()

    # meta json object path
    xdir = os.environ['REFL_CODE']
    outputdir = xdir + '/input'
    if not os.path.isdir(outputdir):
        subprocess.call(['mkdir', outputdir])
    outputfile = outputdir + '/' + station + '_meta.json'

    # If no overwrite and a file already exists, read in existing meta information
    if ((overwrite is False) and (os.path.isfile(outputfile))):
        with open(outputfile) as json_file:
            meta_dict = json.load(json_file)

    else:  # initialize empty meta_dict
        meta_dict = {
            'dates': [],
            'current': [],
            'previous': []
        }

    # read in gage metadata file
    if read_offset:
        meta_dict = check_offsets(station, meta_dict)

    # if read_rnx:
    #    # read in rinex metadata
    #    meta_dict = check_rnx_header(station, meta_dict)
    # if check_earthscope_api:
    #   query es metadata db api

    if man_input:
        meta_dict = meta_man_input(meta_dict)

    meta_dict = sort_meta_dict(meta_dict)

    with open(outputfile, 'w+') as outfile:
        json.dump(meta_dict, outfile, indent=3)


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
    offset_meta_current = []
    offset_meta_past = []
    url = 'https://data.unavco.org/archive/gnss/products/offset/cwu.kalts_nam14.off'
    response = urllib.request.urlopen(url)
    lines = [l.decode('utf-8') for l in response.readlines()]
    cr = csv.reader(lines)
    for row in cr:
        if row[0][1:5] == station.upper():
            # DATE
            year = int(row[0].split()[1])
            month = int(row[0].split()[2])
            day = int(row[0].split()[3])
            hour = int(row[0].split()[4])
            minute = int(row[0].split()[5])
            offset_meta_dates.append(
                datetime.datetime(year=year, day=day, month=month, hour=hour, minute=minute).strftime(
                    "%Y-%m-%d %H:%M:%S"))
            # Description
            ofs = row[0].split()[11]
            evt = row[0].split()[14]
            if evt == 'AN':
                for i, list_ in enumerate([offset_meta_current, offset_meta_past]):
                    receiver = row[0].split()[24 - (i * 3)] + ' ' + row[0].split()[24 - (i * 3) + 1]
                    antenna = row[0].split()[19 - (i * 2)]
                    dome = row[0].split()[27]
                    list_ += ['%s %s %s *' % (receiver, antenna, dome)]  # * for fw]

    meta_dict['dates'] += offset_meta_dates
    meta_dict['current'] += offset_meta_current
    meta_dict['previous'] += offset_meta_past
    if len(offset_meta_dates) == 0:
        print('%s does not have an entry in GAGE offset file' % station)
    return meta_dict


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

    year = input("Enter the 4 digit year: ")
    month = input("Enter the month number: ")
    day = input("Enter the day of month number: ")

    meta_dict['dates'] += [datetime.datetime(year=int(year), day=int(day), month=int(month), hour=0, minute=0).strftime(
        "%Y-%m-%d %H:%M:%S")]

    receiver = input("Enter the receiver brand and model: ")
    antenna = input("Enter the antenna model: ")
    dome = input("Enter the radome 4 digit type or * if unknown: ")
    fw = input("Enter the receiver firmware or * if unknown: ")
    meta_dict['current'] += [receiver + ' ' + antenna + ' ' + dome + ' ' + fw]
    meta_dict['previous'] += ['* * * *']
    return meta_dict


def sort_meta_dict(meta_dict):
    """
    Removes duplicate entries and orders dictionary by dates
    Parameters
    ----------
    meta_dict : dict
        dictionary of metadata; keys 'dates','current','previous'.
    Returns
    ----------
    meta_dict : dict
        dictionary of metadata; keys 'dates','current','previous'.
    """
    # sort
    date_array = np.array(meta_dict['dates'], dtype='datetime64[s]')
    current_array = np.array(meta_dict['current'])
    previous_array = np.array(meta_dict['previous'])

    array_inds = date_array.argsort()
    date_array, current_array, previous_array = date_array[array_inds], current_array[array_inds], previous_array[
        array_inds]
    # remove duplicate
    unq = np.unique(date_array, return_index=True)
    date_array, current_array, previous_array = date_array[unq[1]], current_array[unq[1]], previous_array[unq[1]]

    # return to dict
    meta_dict['dates'], meta_dict['current'], meta_dict[
        'previous'] = np.datetime_as_string(date_array, unit='D').astype('str').tolist(), current_array.astype(
        'str').tolist(), previous_array.astype('str').tolist()

    return meta_dict


def main():
    args = parse_arguments()
    make_json(**args)


if __name__ == "__main__":
    main()
