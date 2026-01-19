"""
extract_arcs.py - Standalone module for extracting satellite arcs from SNR data.

This module provides a clean API for detecting and extracting satellite arcs
from Signal-to-Noise Ratio (SNR) data files. It refactors arc detection logic
from gnssir_v2.py into reusable functions.

An "arc" represents a continuous satellite pass (rising or setting) across the sky.
Arcs are split when:
1. Time gap > 600 seconds (10 minutes)
2. Elevation angle direction reverses (rising <-> setting)
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any

import gnssrefl.gps as g

# Constants
GAP_TIME_LIMIT = 600  # seconds (10 minutes)
MIN_ARC_POINTS = 20


def _get_snr_column(freq: int) -> int:
    """
    Map frequency code to SNR column index (1-based, as used in SNR files).

    Parameters
    ----------
    freq : int
        Frequency code (1, 2, 5, 20, 101, 102, 201, 205, 206, 207, 208, etc.)

    Returns
    -------
    int
        Column number (1-based) for the SNR data

    Raises
    ------
    ValueError
        If frequency code is not recognized
    """
    if freq in [1, 101, 201, 301]:
        return 7
    elif freq in [2, 20, 102, 302]:
        return 8
    elif freq in [5, 205, 305]:
        return 9
    elif freq in [206, 306]:
        return 6
    elif freq in [207, 307]:
        return 10
    elif freq in [208, 308]:
        return 11
    else:
        raise ValueError(f"Unrecognized frequency code: {freq}")


def _check_azimuth_compliance(init_azim: float, azlist: List[float]) -> bool:
    """
    Check if azimuth is within allowed regions.

    Parameters
    ----------
    init_azim : float
        Azimuth angle (degrees) at the lowest elevation point of the arc
    azlist : list of float
        Azimuth regions as pairs [az1_start, az1_end, az2_start, az2_end, ...]
        e.g., [0, 90, 180, 270] means 0-90 and 180-270 degrees

    Returns
    -------
    bool
        True if azimuth is within any of the allowed regions
    """
    N = int(len(azlist) / 2)
    for a in range(N):
        azim1 = azlist[2 * a]
        azim2 = azlist[2 * a + 1]
        if (init_azim >= azim1) and (init_azim <= azim2):
            return True
    return False


def _detect_arc_boundaries(
    ele: np.ndarray,
    azm: np.ndarray,
    seconds: np.ndarray,
    e1: float,
    e2: float,
    ediff: float,
    sat: int,
    min_pts: int = MIN_ARC_POINTS,
    gap_time: float = GAP_TIME_LIMIT,
) -> List[Tuple[int, int, int, int]]:
    """
    Detect arc boundaries based on time gaps and elevation direction changes.

    This is refactored from new_rise_set_again() in gnssir_v2.py.

    Parameters
    ----------
    ele : np.ndarray
        Elevation angles (degrees)
    azm : np.ndarray
        Azimuth angles (degrees)
    seconds : np.ndarray
        Seconds of day
    e1 : float
        Minimum elevation angle (degrees) for analysis
    e2 : float
        Maximum elevation angle (degrees) for analysis
    ediff : float
        Elevation difference tolerance for QC (degrees)
    sat : int
        Satellite number
    min_pts : int
        Minimum points required per arc
    gap_time : float
        Time gap threshold for splitting arcs (seconds)

    Returns
    -------
    list of tuples
        Each tuple is (start_idx, end_idx, sat, arc_num) for valid arcs
    """
    if len(ele) < min_pts:
        return []

    # Required minimum elevation span
    min_deg = (e2 - ediff) - (e1 + ediff)

    # Find breakpoints
    ddate = np.ediff1d(seconds)
    delv = np.ediff1d(ele)

    # Initialize with the last index
    bkpt = np.array([len(ddate)])

    # Add time gap breakpoints
    bkpt = np.append(bkpt, np.where(ddate > gap_time)[0])

    # Add elevation direction change breakpoints
    bkpt = np.append(bkpt, np.where(np.diff(np.sign(delv)))[0])

    # Remove duplicates and sort
    bkpt = np.unique(bkpt)
    bkpt = np.sort(bkpt)

    valid_arcs = []
    iarc = 0

    for ii in range(len(bkpt)):
        if ii == 0:
            sind = 0
        else:
            sind = bkpt[ii - 1] + 1
        eind = bkpt[ii] + 1

        # Extract arc data
        arc_ele = ele[sind:eind]

        if len(arc_ele) == 0:
            continue

        minObse = np.min(arc_ele)
        maxObse = np.max(arc_ele)

        # Validation checks
        nogood = False

        # Check min elevation coverage
        if (minObse - e1) > ediff:
            nogood = True

        # Check max elevation coverage
        if (maxObse - e2) < -ediff:
            nogood = True

        # Check minimum point count
        if (eind - sind) < min_pts:
            nogood = True

        # Check elevation span
        if (maxObse - minObse) < min_deg:
            nogood = True

        if not nogood:
            iarc += 1
            valid_arcs.append((sind, eind, sat, iarc))

    return valid_arcs


def _remove_dc_component(
    ele: np.ndarray,
    snr: np.ndarray,
    polyV: int,
    dbhz: bool,
) -> np.ndarray:
    """
    Remove direct signal component via polynomial fit.

    Parameters
    ----------
    ele : np.ndarray
        Elevation angles (degrees)
    snr : np.ndarray
        Raw SNR values
    polyV : int
        Polynomial order for DC removal
    dbhz : bool
        If True, keep SNR in dB-Hz; if False, convert to linear units first

    Returns
    -------
    np.ndarray
        Detrended SNR data
    """
    data = snr.copy()

    # Convert to linear units if needed
    if not dbhz:
        data = np.power(10, (data / 20))

    # Fit and remove polynomial
    model = np.polyfit(ele, data, polyV)
    fit = np.polyval(model, ele)
    data = data - fit

    return data


def _compute_arc_metadata(
    ele: np.ndarray,
    azi: np.ndarray,
    seconds: np.ndarray,
    sat: int,
    freq: int,
    arc_num: int,
) -> Dict[str, Any]:
    """
    Compute metadata for an arc including edot factor.

    Parameters
    ----------
    ele : np.ndarray
        Elevation angles (degrees)
    azi : np.ndarray
        Azimuth angles (degrees)
    seconds : np.ndarray
        Seconds of day
    sat : int
        Satellite number
    freq : int
        Frequency code
    arc_num : int
        Arc index number

    Returns
    -------
    dict
        Metadata dictionary
    """
    # Determine arc type from elevation trend
    if len(ele) >= 2:
        arc_type = 'rising' if ele[-1] > ele[0] else 'setting'
    else:
        arc_type = 'unknown'

    # Get index of minimum elevation angle
    ie = np.argmin(ele)
    init_azim = azi[ie]

    # Compute edot factor (from window_new lines 975-987)
    # edot in radians/sec
    model = np.polyfit(seconds, ele * np.pi / 180, 1)
    avgEdot_fit = model[0]

    # Average tan(elev)
    cunit = np.mean(np.tan(np.pi * ele / 180))

    # edot factor: tan(e)/edot in units of 1/(radians/hour)
    edot_factor = cunit / (avgEdot_fit * 3600) if avgEdot_fit != 0 else 0.0

    # Scale factor (wavelength/2)
    cf = g.arc_scaleF(freq, sat)

    return {
        'sat': sat,
        'freq': freq,
        'arc_num': arc_num,
        'arc_type': arc_type,
        'ele_start': float(np.min(ele)),
        'ele_end': float(np.max(ele)),
        'az_init': float(init_azim),
        'az_avg': float(np.mean(azi)),
        'time_start': float(np.min(seconds)),
        'time_end': float(np.max(seconds)),
        'time_avg': float(np.mean(seconds) / 3600),  # hours UTC
        'num_pts': len(ele),
        'delT': float((np.max(seconds) - np.min(seconds)) / 60),  # minutes
        'edot_factor': float(edot_factor),
        'cf': float(cf),
    }


def extract_arcs(
    snr_array: np.ndarray,
    freq: int,
    e1: float = 5.0,
    e2: float = 25.0,
    azlist: Optional[List[float]] = None,
    sat_list: Optional[List[int]] = None,
    min_pts: int = MIN_ARC_POINTS,
    ediff: float = 2.0,
    polyV: int = 4,
    dbhz: bool = False,
    screenstats: bool = False,
) -> List[Tuple[Dict[str, Any], Dict[str, np.ndarray]]]:
    """
    Extract satellite arcs from SNR data array.

    Parameters
    ----------
    snr_array : np.ndarray
        2D array with columns: [sat, ele, azi, seconds, edot, snr1, snr2, ...]
        This is the output of loading an SNR file with np.loadtxt()
    freq : int
        Frequency code (1, 2, 5, 20, 101, 102, 201, 205, 206, 207, 208, etc.)
    e1 : float
        Minimum elevation angle (degrees) for analysis. Default: 5.0
    e2 : float
        Maximum elevation angle (degrees) for analysis. Default: 25.0
    azlist : list of floats, optional
        Azimuth regions as pairs, e.g., [0, 90, 180, 270] means 0-90 and 180-270.
        Default: [0, 360] (all azimuths)
    sat_list : list of int, optional
        Specific satellites to process. Default: all satellites in data
    min_pts : int
        Minimum points required per arc. Default: 20
    ediff : float
        Elevation difference tolerance for arc validation (degrees). Default: 2.0
    polyV : int
        Polynomial order for DC removal. Default: 4
    dbhz : bool
        If True, keep SNR in dB-Hz; if False, convert to linear units. Default: False
    screenstats : bool
        If True, print debug information. Default: False

    Returns
    -------
    list of (metadata, data) tuples
        Each arc is represented as:
        - metadata: dict with keys: sat, freq, arc_num, arc_type, ele_start, ele_end,
          az_init, az_avg, time_start, time_end, time_avg, num_pts, delT, edot_factor, cf
        - data: dict with keys: ele, azi, snr, seconds, edot (all np.ndarray)
    """
    if azlist is None:
        azlist = [0, 360]

    # Get SNR column for this frequency
    try:
        column = _get_snr_column(freq)
    except ValueError as e:
        if screenstats:
            print(f"Warning: {e}")
        return []

    # Convert to 0-based index
    icol = column - 1
    ncols = snr_array.shape[1]

    # Check if column exists
    if column > ncols:
        if screenstats:
            print(f"Warning: SNR file has {ncols} columns, need column {column} for freq {freq}")
        return []

    # Extract columns
    sats = snr_array[:, 0].astype(int)
    ele_all = snr_array[:, 1]
    azi_all = snr_array[:, 2]
    seconds_all = snr_array[:, 3]
    edot_all = snr_array[:, 4] if ncols > 4 else np.zeros_like(seconds_all)
    snr_all = snr_array[:, icol]

    # Get unique satellites
    if sat_list is None:
        unique_sats = np.unique(sats)
    else:
        unique_sats = np.array(sat_list)

    all_arcs = []

    for sat in unique_sats:
        # Filter for this satellite only (no pele filter - removed as of v3.6.8)
        sat_mask = sats == sat

        if np.sum(sat_mask) < min_pts:
            continue

        sat_ele = ele_all[sat_mask]
        sat_azi = azi_all[sat_mask]
        sat_seconds = seconds_all[sat_mask]
        sat_edot = edot_all[sat_mask]
        sat_snr = snr_all[sat_mask]

        # Detect arc boundaries on full satellite data
        # (arc detection validates against e1/e2 but uses all elevation data)
        arc_boundaries = _detect_arc_boundaries(
            sat_ele, sat_azi, sat_seconds,
            e1, e2, ediff, sat,
            min_pts=min_pts,
        )

        for sind, eind, sat_num, arc_num in arc_boundaries:
            # Extract arc data (full elevation range)
            arc_ele = sat_ele[sind:eind].copy()
            arc_azi = sat_azi[sind:eind].copy()
            arc_seconds = sat_seconds[sind:eind].copy()
            arc_edot = sat_edot[sind:eind].copy()
            arc_snr = sat_snr[sind:eind].copy()

            # Remove zero SNR values from the arc
            nonzero_mask = arc_snr > 0
            if np.sum(nonzero_mask) < min_pts:
                if screenstats:
                    print(f"No useful data on frequency {freq} / sat {sat}: all zeros")
                continue

            arc_ele = arc_ele[nonzero_mask]
            arc_azi = arc_azi[nonzero_mask]
            arc_seconds = arc_seconds[nonzero_mask]
            arc_edot = arc_edot[nonzero_mask]
            arc_snr = arc_snr[nonzero_mask]

            # Check minimum points for polynomial fit
            reqN = 20
            if len(arc_ele) <= reqN:
                continue

            # Remove DC component on FULL arc (before e1/e2 filter)
            arc_snr_detrended = _remove_dc_component(arc_ele, arc_snr, polyV, dbhz)

            # NOW apply e1/e2 filter (after DC removal)
            e_mask = (arc_ele > e1) & (arc_ele <= e2)
            Nvv = np.sum(e_mask)

            if Nvv < 15:
                continue

            # Get index of min elevation in filtered data for azimuth check
            filtered_ele = arc_ele[e_mask]
            filtered_azi = arc_azi[e_mask]
            ie = np.argmin(filtered_ele)
            init_azim = filtered_azi[ie]

            # Check azimuth compliance
            if not _check_azimuth_compliance(init_azim, azlist):
                if screenstats:
                    print(f"Azimuth {init_azim:.2f} not in requested region")
                continue

            # Apply e1/e2 filter to all arrays
            final_ele = arc_ele[e_mask]
            final_azi = arc_azi[e_mask]
            final_seconds = arc_seconds[e_mask]
            final_edot = arc_edot[e_mask]
            final_snr = arc_snr_detrended[e_mask]

            # Compute metadata using filtered data
            metadata = _compute_arc_metadata(
                final_ele, final_azi, final_seconds,
                sat, freq, arc_num,
            )

            # Create data dictionary
            data = {
                'ele': final_ele,
                'azi': final_azi,
                'snr': final_snr,
                'seconds': final_seconds,
                'edot': final_edot,
            }

            all_arcs.append((metadata, data))

    return all_arcs
