#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import numpy as np
import os
import subprocess

import gnssrefl.gps as g


def _parse_snr_filename(obsfile):
    """
    Parse station, year, doy, snr_type from SNR file path.

    Path format: {REFL_CODE}/{yyyy}/snr/{station}/{station}{doy}0.{yy}.snr{type}
    Example: /home/user/.../2024/snr/alby/alby1000.24.snr66

    Parameters
    ----------
    obsfile : str
        path to SNR file

    Returns
    -------
    station : str
        4-character station name
    year : int
        full year (e.g. 2024)
    doy : int
        day of year
    snr_type : int
        SNR file type (e.g. 66)
    """
    basename = os.path.basename(obsfile)  # alby1000.24.snr66
    station = basename[:4]                 # alby
    doy = int(basename[4:7])               # 100
    yy = int(basename[9:11])               # 24
    year = 2000 + yy if yy < 80 else 1900 + yy
    snr_type = int(basename.split('.snr')[1])  # 66
    return station, year, doy, snr_type


def _get_adjacent_doy(year, doy, offset):
    """
    Get year/doy for adjacent day.

    Parameters
    ----------
    year : int
        full year
    doy : int
        day of year
    offset : int
        -1 for previous day, +1 for next day

    Returns
    -------
    new_year : int
        year of adjacent day
    new_doy : int
        doy of adjacent day
    """
    # Convert to datetime, apply offset, convert back
    date = datetime.datetime(year, 1, 1) + datetime.timedelta(days=doy - 1 + offset)
    new_year = date.year
    new_doy = date.timetuple().tm_yday
    return new_year, new_doy


def read_snr(obsfile, buffer_hours=0, screenstats=False):
    """
    Load the contents of a SNR file into a numpy array, optionally including
    data from adjacent days.

    Parameters
    ----------
    obsfile : str
        name of the snrfile
    buffer_hours : float, optional
        hours of data to include from adjacent days. If > 0, reads last
        buffer_hours from previous day and first buffer_hours from next day.
        Time tags are adjusted: prev day uses negative seconds, next day
        uses seconds > 86400. Default is 0 (single day only).
    screenstats : bool, optional
        print verbose information about buffer data loading. Default is False.

    Returns
    -------
    allGood : int
        1, file was successfully loaded, 0 if not.
        apparently this variable was defined when I did not know about booleans....
    f : numpy array
        contents of the SNR file
    r : int
        number of rows in SNR file
    c : int
        number of columns in SNR file

    """
    allGood = 1
    if os.path.isfile(obsfile):
        f = np.loadtxt(obsfile,comments='%')
    else:
        print('No SNR file found')
        allGood = 0
        return allGood, 0, 0, 0
    r,c = f.shape
    if (r > 0) & (c > 0):
        i= f[:,1] > 0
        f=f[i,:]
    if r == 0:
        print('No rows in this file!')
        allGood = 0
    if c == 0:
        print('No columns in this file!')
        allGood = 0

    # Handle buffer_hours for adjacent day data
    if allGood and buffer_hours > 0:
        station, year, doy, snr_type = _parse_snr_filename(obsfile)
        buffer_seconds = buffer_hours * 3600
        arrays_to_stack = []
        main_cols = c
        prev_loaded, next_loaded = False, False

        # Get previous day data
        prev_year, prev_doy = _get_adjacent_doy(year, doy, -1)
        prev_obsfile, prev_obsfileCmp, prev_snre = g.define_and_xz_snr(station, prev_year, prev_doy, snr_type)
        if prev_snre and os.path.isfile(prev_obsfile):
            prev_data = np.loadtxt(prev_obsfile, comments='%')
            if prev_data.size > 0:
                # Ensure 2D array
                if prev_data.ndim == 1:
                    prev_data = prev_data.reshape(1, -1)
                # Check column count matches main file
                if prev_data.shape[1] != main_cols:
                    print(f'Warning: Previous day SNR file has different column count ({prev_data.shape[1]} vs {main_cols}). Skipping.')
                else:
                    # Filter: positive elevation and last buffer_hours of previous day
                    threshold = 86400 - buffer_seconds
                    mask = (prev_data[:, 1] > 0) & (prev_data[:, 3] > threshold)
                    prev_data = prev_data[mask, :]
                    if prev_data.size > 0:
                        # Adjust time tags: subtract 86400 to get negative seconds
                        prev_data[:, 3] = prev_data[:, 3] - 86400
                        arrays_to_stack.append(prev_data)
                        prev_loaded = True
        else:
            print(f'Warning: no SNR file for previous day ({prev_year}/{prev_doy:03d}), '
                  f'midnight arcs near 0h may be incomplete')

        # Add main day data
        arrays_to_stack.append(f)

        # Get next day data
        next_year, next_doy = _get_adjacent_doy(year, doy, +1)
        next_obsfile, next_obsfileCmp, next_snre = g.define_and_xz_snr(station, next_year, next_doy, snr_type)
        if next_snre and os.path.isfile(next_obsfile):
            next_data = np.loadtxt(next_obsfile, comments='%')
            if next_data.size > 0:
                # Ensure 2D array
                if next_data.ndim == 1:
                    next_data = next_data.reshape(1, -1)
                # Check column count matches main file
                if next_data.shape[1] != main_cols:
                    print(f'Warning: Next day SNR file has different column count ({next_data.shape[1]} vs {main_cols}). Skipping.')
                else:
                    # Filter: positive elevation and first buffer_hours of next day
                    mask = (next_data[:, 1] > 0) & (next_data[:, 3] < buffer_seconds)
                    next_data = next_data[mask, :]
                    if next_data.size > 0:
                        # Adjust time tags: add 86400 to get seconds > 86400
                        next_data[:, 3] = next_data[:, 3] + 86400
                        arrays_to_stack.append(next_data)
                        next_loaded = True
        else:
            print(f'Warning: no SNR file for next day ({next_year}/{next_doy:03d}), '
                  f'midnight arcs near 24h may be incomplete')

        # Log buffer loading status
        if screenstats:
            status = []
            if prev_loaded:
                status.append(f'prev ({prev_year}/{prev_doy})')
            if next_loaded:
                status.append(f'next ({next_year}/{next_doy})')
            if status:
                print(f'  Buffer data loaded: {", ".join(status)}')
            else:
                print(f'  Buffer data: no adjacent day SNR files available')

        # Stack all arrays
        if len(arrays_to_stack) > 1:
            f = np.vstack(arrays_to_stack)

        # Update row/col counts
        r, c = f.shape

    return allGood, f, r, c


def compress_snr_files(wantCompression, obsfile, obsfile2,TwoDays,gzip):
    """
    compresses SNR files

    Parameters
    ----------
    wantCompression : bool
        whether the file should be compressed again
    obsfile : str
        name of first SNR file
    obsfile2 : str
        name of second SNR file
    TwoDays : bool
        whether second file is being input
    gzip : bool
        whether you want to gzip/gunzip the file

    """

    # apparently written before I knew how to use booleans in python
    if gzip:
        if (os.path.isfile(obsfile) == True):
            subprocess.call(['gzip', '-f', obsfile])
        if (os.path.isfile(obsfile2) == True and twoDays == True):
            subprocess.call(['gzip', '-f', obsfile2])
    else:
        # this is only for xz compression - which I should get rid of
        if wantCompression:
            if (os.path.isfile(obsfile) == True):
                subprocess.call(['xz', '-f', obsfile])
            if (os.path.isfile(obsfile2) == True and twoDays == True):
                subprocess.call(['xz', '-f', obsfile2])
