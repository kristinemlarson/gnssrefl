#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import gzip
import numpy as np
import os

from io import BytesIO
from gnssrefl.utils import FileManagement


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
    snr_type = int(basename.split('.snr')[1].replace('.gz', ''))  # 66
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


def load_snr_time_filtered(obsfile, sec_min=None, sec_max=None):
    """Load an SNR file, parsing only rows within a seconds-of-day window.

    Decompresses the full file (unavoidable for gzip), but only passes the
    matching rows to np.loadtxt, which is where most of the time is spent.

    Parameters
    ----------
    obsfile : str or Path
        Path to SNR file (plain text or .gz)
    sec_min : float or None
        Keep rows with seconds > sec_min. None means no lower bound.
    sec_max : float or None
        Keep rows with seconds < sec_max. None means no upper bound.

    Returns
    -------
    data : numpy array (N x cols) or None if no matching rows
    """
    obsfile = str(obsfile)
    is_gz = obsfile.endswith('.gz')

    if is_gz:
        with gzip.open(obsfile, 'rb') as f:
            raw = f.read()
    else:
        with open(obsfile, 'rb') as f:
            raw = f.read()

    lines = raw.split(b'\n')
    data_lines = [l for l in lines if l and not l.startswith(b'%')]
    if not data_lines:
        return None

    # SNR files are sorted by time (column 3, 0-indexed).
    # Use binary search to find the start/end row indices.
    n = len(data_lines)

    def get_sec(idx):
        return float(data_lines[idx].split(None, 4)[3])

    start = 0
    end = n

    if sec_min is not None:
        lo, hi = 0, n
        while lo < hi:
            mid = (lo + hi) // 2
            if get_sec(mid) <= sec_min:
                lo = mid + 1
            else:
                hi = mid
        start = lo

    if sec_max is not None:
        lo, hi = start, n
        while lo < hi:
            mid = (lo + hi) // 2
            if get_sec(mid) < sec_max:
                lo = mid + 1
            else:
                hi = mid
        end = lo

    if start >= end:
        return None

    subset = b'\n'.join(data_lines[start:end])
    return np.loadtxt(BytesIO(subset))


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

        # Get previous day data (last buffer_hours only)
        prev_year, prev_doy = _get_adjacent_doy(year, doy, -1)
        prev_obsfile, prev_snre = FileManagement(station, 'snr_file', prev_year, prev_doy, snr_type=snr_type).find_snr_file()
        if prev_snre:
            threshold = 86400 - buffer_seconds
            prev_data = load_snr_time_filtered(prev_obsfile, sec_min=threshold)
            if prev_data is not None:
                if prev_data.ndim == 1:
                    prev_data = prev_data.reshape(1, -1)
                if prev_data.shape[1] != main_cols:
                    print(f'Warning: Previous day SNR file has different column count ({prev_data.shape[1]} vs {main_cols}). Skipping.')
                else:
                    # Filter positive elevation, adjust time tags to negative seconds
                    mask = prev_data[:, 1] > 0
                    prev_data = prev_data[mask, :]
                    if prev_data.size > 0:
                        prev_data[:, 3] = prev_data[:, 3] - 86400
                        arrays_to_stack.append(prev_data)
                        prev_loaded = True
        else:
            print(f'Warning: no SNR file for previous day ({prev_year}/{prev_doy:03d}), '
                  f'midnight arcs near 0h may be incomplete')

        # Add main day data
        arrays_to_stack.append(f)

        # Get next day data (first buffer_hours only)
        next_year, next_doy = _get_adjacent_doy(year, doy, +1)
        next_obsfile, next_snre = FileManagement(station, 'snr_file', next_year, next_doy, snr_type=snr_type).find_snr_file()
        if next_snre:
            next_data = load_snr_time_filtered(next_obsfile, sec_max=buffer_seconds)
            if next_data is not None:
                if next_data.ndim == 1:
                    next_data = next_data.reshape(1, -1)
                if next_data.shape[1] != main_cols:
                    print(f'Warning: Next day SNR file has different column count ({next_data.shape[1]} vs {main_cols}). Skipping.')
                else:
                    # Filter positive elevation, adjust time tags past 86400
                    mask = next_data[:, 1] > 0
                    next_data = next_data[mask, :]
                    if next_data.size > 0:
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
