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

import contextlib
import glob
import io
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, Union

import numpy as np
from numpy.polynomial import Polynomial
import pandas as pd
from tqdm import tqdm

import gnssrefl.gps as g
from gnssrefl.read_snr_files import read_snr
from gnssrefl.utils import circular_mean_deg, circular_distance_deg, FileManagement
from gnssrefl.gnss_frequencies import all_frequencies, get_snr_column, get_scale_factor, get_file_suffix, get_glonass_channel
from gnssrefl.tracks import active_epoch_days, attach_legacy_apriori, attach_track_id, build_lookup_index, lookup_arc

# Constants
GAP_TIME_LIMIT = 600  # seconds (10 minutes)
MIN_ARC_POINTS = 20
RESULT_COLUMNS = [
    'year', 'doy', 'RH', 'sat', 'UTCtime', 'Azim', 'Amp',
    'eminO', 'emaxO', 'NumbOf', 'freq', 'rise', 'EdotF',
    'PkNoise', 'DelT', 'MJD', 'refr',
]
PHASE_COLUMNS = [
    'year', 'doy', 'Hour', 'Phase', 'Nv', 'Azimuth', 'Sat', 'Ampl',
    'emin', 'emax', 'DelT', 'aprioriRH', 'freq', 'estRH', 'pk2noise', 'LSPAmp',
]
VWC_TRACK_COLUMNS = [
    'Year', 'DOY', 'Hour', 'MJD', 'AzMinEle',
    'PhaseOrig', 'AmpLSPOrig', 'AmpLSOrig', 'DeltaRHOrig',
    'AmpLSPSmooth', 'AmpLSSmooth', 'DeltaRHSmooth',
    'PhaseVegCorr', 'SlopeCorr', 'SlopeFinal',
    'PhaseCorrected', 'VWC',
]

# (snr file column, constellation offset) -> user-facing freq code
# Constellation offset derived from sat number: GPS=0, GLONASS=100, Galileo=200, Beidou=300
COL_CONST_TO_FREQ = {
    (6, 200): 206, (6, 300): 306,
    (7, 0): 1, (7, 100): 101, (7, 200): 201, (7, 300): 301,
    (8, 0): 20, (8, 100): 102, (8, 300): 302,
    (9, 0): 5, (9, 200): 205, (9, 300): 305,
    (10, 200): 207, (10, 300): 307,
    (11, 200): 208, (11, 300): 308,
}
SNR_COLUMNS = [6, 7, 8, 9, 10, 11]


def _freq_for_column_and_sat(column, sat, l2c_sats=None, l5_sats=None):
    """Map (SNR column, sat number) to user-facing freq code. Returns None if invalid."""
    offset = (sat // 100) * 100
    # GPS special cases: L2C vs legacy L2, and L5 transmit check
    if offset == 0:
        if column == 8:
            return 20 if (l2c_sats is None or sat in l2c_sats) else 2
        if column == 9 and l5_sats is not None and sat not in l5_sats:
            return None
    return COL_CONST_TO_FREQ.get((column, offset))


def _load_result_file(path):
    """Load a gnssir/phase result file into a 2-D numpy array."""
    data = np.loadtxt(path, comments='%')
    if data.size == 0:
        return None
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return data


def attach_gnssir_processing_results(arcs, results, time_tolerance=0.17):
    """Attach gnssir processing results to extracted arcs.

    For each arc, finds the matching row in the gnssir result file based on
    satellite number, frequency, rise/set direction, and UTC time proximity.
    Sets ``metadata['gnssir_processing_results']`` to a dict or ``None``.
    """
    if isinstance(results, str):
        results = _load_result_file(results)

    if results is None:
        for metadata, _data in arcs:
            metadata['gnssir_processing_results'] = None
        return arcs

    COL_SAT = RESULT_COLUMNS.index('sat')
    COL_UTC = RESULT_COLUMNS.index('UTCtime')
    COL_FREQ = RESULT_COLUMNS.index('freq')
    COL_RISE = RESULT_COLUMNS.index('rise')

    lookup = {}
    for i in range(results.shape[0]):
        key = (int(results[i, COL_SAT]), int(results[i, COL_FREQ]), int(results[i, COL_RISE]))
        lookup.setdefault(key, []).append((i, results[i, COL_UTC]))

    result_fields = {
        'RH': (RESULT_COLUMNS.index('RH'), float),
        'Amp': (RESULT_COLUMNS.index('Amp'), float),
        'PkNoise': (RESULT_COLUMNS.index('PkNoise'), float),
        'MJD': (RESULT_COLUMNS.index('MJD'), float),
        'UTCtime': (COL_UTC, float),
        'Azim': (RESULT_COLUMNS.index('Azim'), float),
        'eminO': (RESULT_COLUMNS.index('eminO'), float),
        'emaxO': (RESULT_COLUMNS.index('emaxO'), float),
        'NumbOf': (RESULT_COLUMNS.index('NumbOf'), int),
        'DelT': (RESULT_COLUMNS.index('DelT'), float),
        'EdotF': (RESULT_COLUMNS.index('EdotF'), float),
        'refr': (RESULT_COLUMNS.index('refr'), int),
        'rise': (COL_RISE, int),
    }

    for metadata, data in arcs:
        arc_rise = 1 if metadata['arc_type'] == 'rising' else -1
        key = (metadata['sat'], metadata['freq'], arc_rise)
        candidates = lookup.get(key, [])
        arc_utc = metadata['arc_timestamp']
        best_idx = None
        best_dt = time_tolerance
        for row_idx, utctime in candidates:
            dt = abs(utctime - arc_utc)
            if dt < best_dt:
                best_dt = dt
                best_idx = row_idx
        if best_idx is not None:
            row = results[best_idx]
            metadata['gnssir_processing_results'] = {
                name: typ(row[col]) for name, (col, typ) in result_fields.items()
            }
        else:
            metadata['gnssir_processing_results'] = None

    return arcs


def attach_phase_processing_results(arcs, results, time_tolerance=0.17):
    """Attach phase processing results to extracted arcs.

    For each arc, finds the matching row in the phase result file based on
    satellite number, frequency, and UTC time proximity.
    Sets ``metadata['phase_processing_results']`` to a dict or ``None``.
    """
    if isinstance(results, str):
        results = _load_result_file(results)

    if results is None:
        for metadata, _data in arcs:
            metadata['phase_processing_results'] = None
        return arcs

    COL_SAT = PHASE_COLUMNS.index('Sat')
    COL_HOUR = PHASE_COLUMNS.index('Hour')
    COL_FREQ = PHASE_COLUMNS.index('freq')

    lookup = {}
    for i in range(results.shape[0]):
        key = (int(results[i, COL_SAT]), int(results[i, COL_FREQ]))
        lookup.setdefault(key, []).append((i, results[i, COL_HOUR]))

    phase_fields = {
        'Phase': (PHASE_COLUMNS.index('Phase'), float),
        'Nv': (PHASE_COLUMNS.index('Nv'), int),
        'Azimuth': (PHASE_COLUMNS.index('Azimuth'), float),
        'Ampl': (PHASE_COLUMNS.index('Ampl'), float),
        'emin': (PHASE_COLUMNS.index('emin'), float),
        'emax': (PHASE_COLUMNS.index('emax'), float),
        'DelT': (PHASE_COLUMNS.index('DelT'), float),
        'aprioriRH': (PHASE_COLUMNS.index('aprioriRH'), float),
        'estRH': (PHASE_COLUMNS.index('estRH'), float),
        'pk2noise': (PHASE_COLUMNS.index('pk2noise'), float),
        'LSPAmp': (PHASE_COLUMNS.index('LSPAmp'), float),
    }

    for metadata, data in arcs:
        key = (metadata['sat'], metadata['freq'])
        candidates = lookup.get(key, [])
        arc_utc = metadata['arc_timestamp']
        best_idx = None
        best_dt = time_tolerance
        for row_idx, hour in candidates:
            dt = abs(hour - arc_utc)
            if dt < best_dt:
                best_dt = dt
                best_idx = row_idx
        if best_idx is not None:
            row = results[best_idx]
            metadata['phase_processing_results'] = {
                name: typ(row[col]) for name, (col, typ) in phase_fields.items()
            }
        else:
            metadata['phase_processing_results'] = None

    return arcs


def attach_vwc_track_results(arcs, station, year, doy, extension='',
                             az_tolerance=5.0, time_tolerance=0.25):
    """Attach VWC track results to extracted arcs.

    Matches track file rows to arcs by sat, freq suffix, azimuth, and hour.
    Sets ``metadata['vwc_track_results']`` to a dict or ``None``.
    """
    import re
    from gnssrefl.phase_functions import get_temporal_suffix

    def _set_all_none():
        for metadata, _data in arcs:
            metadata['vwc_track_results'] = None
        return arcs

    refl_code = os.environ.get('REFL_CODE', '')
    if not refl_code:
        return _set_all_none()

    fm = FileManagement(station, "individual_tracks", extension=extension)
    track_dir = str(fm.get_directory_path(ensure_directory=False))
    if not os.path.isdir(track_dir):
        return _set_all_none()

    # {station}_track_sat{NN}_az{NNN}_{year}{freq}.txt
    filename_re = re.compile(r'.*_track_sat(\d{2})_az(\d{3})_')
    sat_lookup = {}
    for fpath in glob.glob(os.path.join(track_dir, '*.txt')):
        m = filename_re.match(os.path.basename(fpath))
        if m:
            sat_lookup.setdefault(int(m.group(1)), []).append((int(m.group(2)), fpath))
    if not sat_lookup:
        return _set_all_none()

    vwc_fields = {name: (i, float) for i, name in enumerate(VWC_TRACK_COLUMNS)}
    for col in ('Year', 'DOY', 'MJD'):
        vwc_fields[col] = (VWC_TRACK_COLUMNS.index(col), int)

    for metadata, _data in arcs:
        metadata['vwc_track_results'] = None
        candidates = sat_lookup.get(metadata['sat'])
        if not candidates:
            continue
        try:
            freq_suffix = get_temporal_suffix(metadata['freq'], include_time=False)
        except Exception:
            continue
        candidates = [(az, fp) for az, fp in candidates if freq_suffix in os.path.basename(fp)]
        if not candidates:
            continue
        az_dists = np.array([circular_distance_deg(metadata['az_min_ele'], az) for az, _ in candidates])
        best_i = int(np.argmin(az_dists))
        if az_dists[best_i] > az_tolerance:
            continue
        track_data = _load_result_file(candidates[best_i][1])
        if track_data is None:
            continue
        day_mask = (track_data[:, 0].astype(int) == year) & (track_data[:, 1].astype(int) == doy)
        day_rows = track_data[day_mask]
        if len(day_rows) == 0:
            continue
        raw_diffs = np.abs(day_rows[:, 2] - metadata['arc_timestamp'])
        hour_diffs = np.minimum(raw_diffs, 24 - raw_diffs)
        best_row_i = int(np.argmin(hour_diffs))
        if hour_diffs[best_row_i] > time_tolerance:
            continue
        row = day_rows[best_row_i]
        metadata['vwc_track_results'] = {
            name: typ(row[col]) for name, (col, typ) in vwc_fields.items()
        }

    return arcs


def _get_arc_filename(sdir, sat, freq, az_min_ele, arc_timestamp):
    """Build deterministic arc filename from metadata.

    Suffix follows the registry convention _<C>_<label> shared with
    phaseRH/VWC/track files (e.g. _G_L1, _G_L2C, _E_L7).
    """
    csat = f'{sat:03d}'
    hh = int(arc_timestamp) % 24
    mm = int((arc_timestamp % 1) * 60)
    ctime = f'{hh:02d}{mm:02d}z'
    return f'{sdir}sat{csat}{get_file_suffix(freq)}_az{round(az_min_ele):03d}_{ctime}.txt'


def _write_arc_file(fname, data, meta, station, year, doy, savearcs_format='txt'):
    """Write a single arc to disk."""
    eangles = data['ele']
    dsnr = data['snr']
    sec = data['seconds']
    if savearcs_format == 'txt':
        headerline = ' elev-angle (deg), dSNR (volts/volts), sec of day'
        xyz = np.vstack((eangles, dsnr, sec)).T
        fmt = '%12.7f  %12.7f  %10.0f'
        np.savetxt(fname, xyz, fmt=fmt, delimiter=' ', newline='\n',
                   comments='%', header=headerline)
    else:
        import pickle
        d = g.doy2ymd(int(year), int(doy))
        MJD = g.getMJD(year, d.month, d.day, meta['arc_timestamp'])
        docstring = ('arrays are eangles (degrees), dsnrData is SNR '
                     'with/DC removed, and sec (seconds of the day),\n')
        pname = fname[:-4] + '.pickle'
        with open(pname, 'wb') as f:
            pickle.dump([station, eangles, dsnr, sec, meta['sat'],
                         meta['freq'], meta['az_min_ele'], year, doy,
                         meta['arc_timestamp'], MJD, docstring], f)


def setup_arcs_directory(station, year, doy, extension='', nooverwrite=False):
    """Create arcs directory, optionally clearing old contents."""
    fm = FileManagement(station, "arcs_directory", year=year, doy=doy,
                        extension=extension)
    sdir = str(fm.get_directory_path(ensure_directory=True)) + '/'
    if not nooverwrite:
        for f in glob.glob(sdir + '*.txt') + glob.glob(sdir + '*.pickle'):
            os.remove(f)
        failqc = sdir + 'failQC/'
        if os.path.isdir(failqc):
            for f in glob.glob(failqc + '*.txt') + glob.glob(failqc + '*.pickle'):
                os.remove(f)
    os.makedirs(sdir + 'failQC/', exist_ok=True)
    return sdir


def save_arc(meta, data, sdir, station, year, doy, savearcs_format='txt'):
    """Save a single arc file to sdir."""
    if meta['num_pts'] <= 0 or meta['delT'] == 0:
        return
    fname = _get_arc_filename(sdir, meta['sat'], meta['freq'],
                              meta['az_min_ele'], meta['arc_timestamp'])
    if not fname:
        return
    _write_arc_file(fname, data, meta, station, year, doy, savearcs_format)


def move_arc_to_failqc(meta, station, year, doy, extension=''):
    """Move a saved arc file from arcs/ to arcs/failQC/."""
    fm = FileManagement(station, "arcs_directory", year=year, doy=doy,
                        extension=extension)
    sdir = str(fm.get_directory_path()) + '/'
    base = _get_arc_filename(sdir, meta['sat'], meta['freq'],
                             meta['az_min_ele'], meta['arc_timestamp'])
    if not base:
        return
    # arc may have been saved as .txt or .pickle
    for ext in ('.txt', '.pickle'):
        src = base[:-4] + ext
        if os.path.isfile(src):
            dest = _get_arc_filename(sdir + 'failQC/', meta['sat'], meta['freq'],
                                     meta['az_min_ele'], meta['arc_timestamp'])
            dest = dest[:-4] + ext
            shutil.move(src, dest)
            return


def apply_refraction(snr_array, station_config, year, doy, verbose=True):
    """Apply refraction correction to SNR elevation angles.

    Returns a copy of *snr_array* with corrected elevations; rows where
    the correction is invalid (e.g. ele < 1.5 for NITE/MPF) are removed.
    """
    from gnssrefl.refraction import correct_elevations
    corrected, valid_mask = correct_elevations(snr_array[:, 1], station_config, year, doy, verbose=verbose)
    snr_array = snr_array.copy()
    snr_array[:, 1] = corrected
    return snr_array[valid_mask]


def extract_arcs_from_station(
    station: str,
    year: int,
    doy: int,
    freq: Optional[Union[int, List[int]]] = None,
    snr_type: int = 66,
    buffer_hours: float = 2,
    attach_results: Union[bool, List[str]] = False,
    extension: str = '',
    station_config: Optional[Dict[str, Any]] = None,
    gzip: bool = True,
    track_file: Optional[Union[str, Path]] = None,
    track_cache: Optional[Dict[str, Any]] = None,
    tag_with_legacy_apriori: bool = False,
    refraction_verbose: bool = True,
    **kwargs,
) -> List[Tuple[Dict[str, Any], Dict[str, np.ndarray]]]:
    """
    Extract satellite arcs for a station/year/day.

    Resolves the SNR file path, loads SNR data, optionally applies refraction
    correction and decimation, extracts arcs, and optionally saves arc files
    and attaches processing results.

    Parameters
    ----------
    station : str
        Station name (4 characters, e.g. 'mchl')
    year : int
        Full year (e.g. 2025)
    doy : int
        Day of year (1-366)
    freq : int, list of int, or None
        Frequency code(s). Default: None (auto-detect)
    snr_type : int
        SNR file type (66, 77, 88, etc.). Default: 66
    buffer_hours : float
        Hours of data from adjacent days for midnight-crossing arcs. Default: 2
    attach_results : bool
        If True, attach gnssir/phase/vwc results to arc metadata. Default: False
    extension : str
        Strategy extension for result file paths. Default: ''
    station_config : dict, optional
        Station analysis parameters. When provided, enables refraction
        correction (if ``station_config['refraction']``) and savearcs (if ``station_config['savearcs']``).
    gzip : bool
        If True, gzip the SNR file after reading. Default: True
    track_file : path-like, optional
        Path to a tracks-shaped JSON file (tracks.json from build_tracks, or
        vwc_tracks.json from vwc_input). When supplied, each arc's metadata
        is tagged via tracks.attach_track_id with track_id, track_epoch,
        track_azim, and (if present in the epoch dict) apriori_RH. Arcs that
        don't match any track get -1/None.
    track_cache : dict, optional
        Shared dict for reusing the same tracks JSON across many calls. Pass
        the same dict on each call; the JSON is loaded and indexed on the
        first call and reused thereafter.
    tag_with_legacy_apriori : bool
        When True, tag arcs from the legacy GPS apriori_rh_{fr}.txt file via
        tracks.attach_legacy_apriori (sets apriori_RH / track_azim on each arc
        by (sat, azimuth-within-3 deg) matching). Mutually exclusive with
        track_file. Default: False.

        When neither track_file nor tag_with_legacy_apriori is provided, arcs
        are returned without track_id / track_epoch / track_azim / apriori_RH
        tagging.
    refraction_verbose : bool
        Forwarded as ``verbose`` to apply_refraction so batch callers can
        silence the per-day refraction prints. Default: True.
    **kwargs
        Additional keyword arguments passed to ``extract_arcs()``

    Returns
    -------
    list of (metadata, data) tuples
        See ``extract_arcs()`` for format details.

    Raises
    ------
    FileNotFoundError
        If the SNR file does not exist and cannot be decompressed, or if
        ``track_file`` is supplied but does not exist.
    ValueError
        If both ``track_file`` and ``tag_with_legacy_apriori=True`` are set.
    """
    if tag_with_legacy_apriori and track_file is not None:
        raise ValueError(
            "extract_arcs_from_station: 'track_file' and 'tag_with_legacy_apriori=True' "
            "are mutually exclusive. Pass one or the other."
        )

    if track_file is not None and not Path(track_file).exists():
        raise FileNotFoundError(
            f"track_file not found: {track_file}. "
            f"Run vwc_input (default path) or build_tracks before tagging arcs."
        )

    obsfile, snr_exists = FileManagement(station, 'snr_file', year, doy, snr_type=snr_type).find_snr_file(gzip=gzip)
    if not snr_exists:
        raise FileNotFoundError(
            f"SNR file not found for station={station}, year={year}, "
            f"doy={doy}, snr_type={snr_type}: {obsfile}"
        )

    screenstats = kwargs.get('screenstats', False)
    allGood, snr_array, _, _ = read_snr(
        obsfile, buffer_hours=buffer_hours, screenstats=screenstats,
    )
    if not allGood:
        raise RuntimeError(f"read_snr failed for: {obsfile}")

    # Apply refraction correction
    if station_config is not None and station_config.get('refraction', False):
        snr_array = apply_refraction(snr_array, station_config, year, doy, verbose=refraction_verbose)

    arcs = extract_arcs(snr_array, freq=freq, year=year, doy=doy, **kwargs)

    if track_file is not None:
        attach_track_id(arcs, track_file, year, doy, track_cache=track_cache)
    elif tag_with_legacy_apriori:
        attach_legacy_apriori(arcs, station, extension=extension)

    # Save individual arc files to disk
    if station_config is not None and station_config.get('savearcs', False):
        nooverwrite = station_config.get('nooverwrite', False)
        savearcs_format = station_config.get('savearcs_format', 'txt')
        sdir = setup_arcs_directory(station, year, doy, extension, nooverwrite)
        print('Writing individual arcs to', sdir)
        for meta, data in arcs:
            save_arc(meta, data, sdir, station, year, doy, savearcs_format)

    if attach_results:
        # Normalize: True means all, list means specific types
        if attach_results is True:
            attach_results = ['gnssir', 'phase', 'vwc']

        if 'gnssir' in attach_results:
            try:
                results = load_results_with_failqc(station, year, doy, extension, require_failqc=False)
                if results is not None:
                    attach_gnssir_processing_results(arcs, results)
                else:
                    for metadata, _data in arcs:
                        metadata['gnssir_processing_results'] = None
            except Exception:
                for metadata, _data in arcs:
                    metadata['gnssir_processing_results'] = None

        if 'phase' in attach_results:
            phase_path = FileManagement(station, 'phase_file', year, doy,
                                        extension=extension).get_file_path(ensure_directory=False)
            if phase_path.is_file():
                attach_phase_processing_results(arcs, str(phase_path))
            else:
                for metadata, _data in arcs:
                    metadata['phase_processing_results'] = None

        if 'vwc' in attach_results:
            attach_vwc_track_results(arcs, station, year, doy, extension)

    return arcs


def extract_arcs_from_file(
    obsfile: str,
    freq: Optional[Union[int, List[int]]] = None,
    buffer_hours: float = 2,
    **kwargs,
) -> List[Tuple[Dict[str, Any], Dict[str, np.ndarray]]]:
    """
    Extract satellite arcs from an SNR file.

    Loads the file with ``read_snr()`` and extracts arcs in one call.

    Parameters
    ----------
    obsfile : str
        Path to the SNR observation file.
    freq : int, list of int, or None
        Frequency code(s). Default: None (auto-detect)
    buffer_hours : float
        Hours of data from adjacent days. Default: 2
    **kwargs
        Additional keyword arguments passed to ``extract_arcs()``

    Returns
    -------
    list of (metadata, data) tuples
        See ``extract_arcs()`` for format details.

    Raises
    ------
    FileNotFoundError
        If *obsfile* does not exist.
    RuntimeError
        If ``read_snr()`` fails to load the file.
    """
    screenstats = kwargs.get('screenstats', False)
    allGood, snr_array, _, _ = read_snr(
        obsfile, buffer_hours=buffer_hours, screenstats=screenstats,
    )
    if not allGood:
        raise RuntimeError(f"read_snr failed for: {obsfile}")

    return extract_arcs(snr_array, freq=freq, **kwargs)


def extract_arcs(
    snr_array: np.ndarray,
    freq: Optional[Union[int, List[int]]] = None,
    e1: float = 5.0,
    e2: float = 25.0,
    ellist: Optional[List[float]] = None,
    azlist: Optional[List[float]] = None,
    sat_list: Optional[List[int]] = None,
    min_pts: int = MIN_ARC_POINTS,
    polyV: int = 4,
    pele: Optional[List[float]] = None,
    dbhz: bool = False,
    screenstats: bool = False,
    detrend: bool = True,
    split_arcs: bool = True,
    filter_to_day: bool = True,
    year: Optional[int] = None,
    doy: Optional[int] = None,
    dec: int = 1,
) -> List[Tuple[Dict[str, Any], Dict[str, np.ndarray]]]:
    """
    Extract satellite arcs from SNR data array.

    Parameters
    ----------
    snr_array : np.ndarray
        2D array with columns: [sat, ele, azi, seconds, edot, snr1, snr2, ...]
    freq : int, list of int, or None
        Frequency code(s). Default: None (auto-detect)
    e1 : float
        Minimum elevation angle (degrees). Default: 5.0
    e2 : float
        Maximum elevation angle (degrees). Default: 25.0
    ellist : list of floats, optional
        Multiple elevation angle ranges as pairs. Overrides e1/e2.
    azlist : list of floats, optional
        Azimuth regions as pairs. Default: [0, 360]
    sat_list : list of int, optional
        Specific satellites to process. Default: all satellites in data
    min_pts : int
        Minimum points required per arc. Default: 20
    polyV : int
        Polynomial order for DC removal. Default: 4
    pele : list of float, optional
        Elevation angle range [min, max] for polynomial fit. Default: [e1, e2]
    dbhz : bool
        If True, keep SNR in dB-Hz. Default: False
    screenstats : bool
        If True, print debug information. Default: False
    detrend : bool
        If True (default), remove DC component via polynomial fit.
    split_arcs : bool
        If True (default), split data into separate arcs.
    filter_to_day : bool
        If True (default), only return arcs within the principal day (0-24h).
    year : int, optional
        Year, used for L2C/L5 satellite list lookup.
    doy : int, optional
        Day of year, used with *year*.
    dec : int
        Decimation factor. Default: 1 (no decimation).

    Returns
    -------
    list of (metadata, data) tuples
        Each arc is represented as:
        - metadata: dict with keys: sat, freq, arc_num, arc_type, ele_start, ele_end,
          az_min_ele, az_avg, time_start, time_end, arc_timestamp, num_pts, delT, edot_factor, cf
        - data: dict with keys: ele, azi, snr, seconds, edot (all np.ndarray)
    """
    if azlist is None:
        azlist = [0, 360]
    if pele is None:
        pele = [e1, e2]

    # Apply decimation before any other filtering
    if dec != 1:
        keep = np.remainder(snr_array[:, 3], dec) == 0
        snr_array = snr_array[keep]

    # Pre-filter SNR data to pele range (replicates gnssir's elevation mask)
    pele_mask = (snr_array[:, 1] >= pele[0]) & (snr_array[:, 1] <= pele[1])
    snr_array = snr_array[pele_mask]

    ncols = snr_array.shape[1]

    # Build column list and optional freq filter
    freq_list = [freq] if isinstance(freq, int) else (list(freq) if freq is not None else None)
    freq_set = set(freq_list) if freq_list is not None else None
    if freq_list is not None:
        # Deduplicate columns while preserving order (multiple freqs can share a column)
        seen = set()
        column_list = []
        for f in freq_list:
            c = get_snr_column(f)
            if c not in seen:
                seen.add(c)
                column_list.append(c)
    else:
        column_list = [c for c in SNR_COLUMNS if c <= ncols]

    # L2C/L5 satellite sets for GPS freq assignment
    l2c_sats = l5_sats = None
    if year is not None and doy is not None:
        from gnssrefl.gps import l2c_l5_list
        l2c_arr, l5_arr = l2c_l5_list(year, doy)
        l2c_sats = set(int(s) for s in l2c_arr)
        l5_sats = set(int(s) for s in l5_arr)

    all_arcs = []

    # Pre-extract column-independent arrays once (not per-column)
    sats = snr_array[:, 0].astype(int)
    ele_all = snr_array[:, 1]
    azi_all = snr_array[:, 2]
    seconds_all = snr_array[:, 3]
    edot_all = snr_array[:, 4] if ncols > 4 else np.zeros_like(seconds_all)

    if sat_list is None:
        unique_sats = np.unique(sats)
    else:
        unique_sats = np.array(sat_list)

    # Drop GLONASS sats whose slot has no known FDMA channel (e.g. newly launched
    # GLONASS-K not yet in the slot table). Without this they would crash the
    # per-arc wavelength lookup. Log once so the user sees which PRNs were skipped.
    glonass_mask = (unique_sats >= 101) & (unique_sats <= 199)
    if glonass_mask.any():
        unknown = [int(s) for s in unique_sats[glonass_mask] if get_glonass_channel(int(s)) is None]
        if unknown:
            print(f'Skipping GLONASS sats with no known channel assignment: {unknown}')
            unique_sats = np.array([s for s in unique_sats if int(s) not in unknown])

    elev_pairs = _parse_elevation_list(e1, e2, ellist)
    if screenstats and len(elev_pairs) > 1:
        print(f'Using {len(elev_pairs)} elevation angle ranges: {elev_pairs}')

    # Pre-compute arc scale factors (wavelength/2) to avoid repeated lookup
    cf_cache = {}

    # Pre-compute per-satellite masks and index ranges for fast lookup
    sort_idx = np.argsort(sats, kind='stable')
    sorted_sats = sats[sort_idx]
    sat_boundaries = np.searchsorted(sorted_sats, unique_sats, side='left')
    sat_boundaries_r = np.searchsorted(sorted_sats, unique_sats, side='right')
    sat_counts = sat_boundaries_r - sat_boundaries

    for column in column_list:
        icol = column - 1

        if column > ncols:
            if screenstats:
                print(f"Warning: SNR file has {ncols} columns, need column {column}")
            continue

        snr_all = snr_array[:, icol]

        for sat_idx, sat in enumerate(unique_sats):
            # Determine freq code for this column + satellite
            sat_freq = _freq_for_column_and_sat(column, sat, l2c_sats, l5_sats)
            if sat_freq is None:
                continue
            if freq_set is not None and sat_freq not in freq_set:
                continue  # user didn't request this freq

            if sat_counts[sat_idx] < min_pts:
                continue

            # Use pre-sorted index for fast satellite data extraction
            sat_indices = sort_idx[sat_boundaries[sat_idx]:sat_boundaries_r[sat_idx]]
            sat_ele = ele_all[sat_indices]
            sat_azi = azi_all[sat_indices]
            sat_seconds = seconds_all[sat_indices]
            sat_edot = edot_all[sat_indices]
            sat_snr = snr_all[sat_indices]

            for pair_e1, pair_e2 in elev_pairs:
                if split_arcs:
                    arc_boundaries = _detect_arc_boundaries(
                        sat_ele, sat_azi, sat_seconds,
                        pair_e1, pair_e2, sat,
                        min_pts=min_pts,
                    )
                else:
                    arc_boundaries = [(0, len(sat_ele), sat, 1)]

                for sind, eind, sat_num, arc_num in arc_boundaries:
                    # Use views (not copies) — nonzero_mask indexing below creates new arrays
                    arc_ele = sat_ele[sind:eind]
                    arc_azi = sat_azi[sind:eind]
                    arc_seconds = sat_seconds[sind:eind]
                    arc_edot = sat_edot[sind:eind]
                    arc_snr = sat_snr[sind:eind]

                    nonzero_mask = arc_snr > 1
                    if np.count_nonzero(nonzero_mask) < min_pts:
                        if screenstats:
                            print(f"No useful data on frequency {sat_freq} / sat {sat}: all zeros")
                        continue

                    arc_ele = arc_ele[nonzero_mask]
                    arc_azi = arc_azi[nonzero_mask]
                    arc_seconds = arc_seconds[nonzero_mask]
                    arc_edot = arc_edot[nonzero_mask]
                    arc_snr = arc_snr[nonzero_mask]

                    reqN = 20
                    if len(arc_ele) <= reqN:
                        continue

                    if split_arcs:
                        e_mask = (arc_ele > pair_e1) & (arc_ele <= pair_e2)
                        Nvv = np.count_nonzero(e_mask)

                        if Nvv < 15:
                            continue

                        # Check azimuth compliance using circular mean
                        filtered_azi = arc_azi[e_mask]
                        arc_azim = circular_mean_deg(filtered_azi)

                        if not check_azimuth_compliance(arc_azim, azlist):
                            if screenstats:
                                print(f"Azimuth {arc_azim:.2f} not in requested region")
                            continue

                        final_ele = arc_ele[e_mask]
                        final_azi = filtered_azi
                        final_seconds = arc_seconds[e_mask]
                        final_edot = arc_edot[e_mask]
                        precomputed_az_avg = arc_azim
                    else:
                        e_mask = None
                        final_ele = arc_ele
                        final_azi = arc_azi
                        final_seconds = arc_seconds
                        final_edot = arc_edot
                        precomputed_az_avg = None

                    # Cache arc scale factor (wavelength/2) by (freq, sat)
                    cf_key = (sat_freq, sat)
                    cf = cf_cache.get(cf_key)
                    if cf is None:
                        cf = get_scale_factor(sat_freq, sat)
                        cf_cache[cf_key] = cf

                    metadata = _compute_arc_metadata(
                        final_ele, final_azi, final_seconds,
                        sat, sat_freq, arc_num,
                        pair_e1, pair_e2,
                        az_avg=precomputed_az_avg, cf=cf,
                    )

                    # Detrend and apply e_mask in one step
                    if detrend:
                        dt_snr = remove_dc_component(arc_ele, arc_snr, polyV, dbhz, pele)
                    else:
                        dt_snr = arc_snr.copy() if dbhz else np.power(10, arc_snr / 20)
                    final_snr = dt_snr[e_mask] if e_mask is not None else dt_snr

                    all_arcs.append((metadata, {
                        'ele': final_ele, 'azi': final_azi,
                        'snr': final_snr, 'seconds': final_seconds,
                        'edot': final_edot,
                    }))

    if filter_to_day:
        all_arcs = [
            (meta, data) for meta, data in all_arcs
            if 0 <= meta['arc_timestamp'] < 24
        ]

    return all_arcs

def _parse_elevation_list(
    e1: float,
    e2: float,
    ellist: Optional[List[float]],
) -> List[Tuple[float, float]]:
    """
    Parse elevation angle parameters into list of (e1, e2) pairs.

    Parameters
    ----------
    e1 : float
        Default minimum elevation angle
    e2 : float
        Default maximum elevation angle
    ellist : list of float or None
        Elevation pairs as flat list [e1a, e2a, e1b, e2b, ...]

    Returns
    -------
    list of (float, float)
        List of (min_elev, max_elev) tuples to process

    Raises
    ------
    ValueError
        If ellist has odd length (incomplete pair)
    """
    if ellist is None or len(ellist) == 0:
        return [(e1, e2)]

    if len(ellist) % 2 != 0:
        raise ValueError(
            f"ellist must contain pairs of elevation angles, "
            f"got {len(ellist)} values (odd number)"
        )

    return [(ellist[i], ellist[i + 1]) for i in range(0, len(ellist), 2)]



def check_azimuth_compliance(az_min_ele: float, azlist: List[float]) -> bool:
    """
    Check if azimuth is within allowed regions.

    Parameters
    ----------
    az_min_ele : float
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
        if (az_min_ele >= azim1) and (az_min_ele <= azim2):
            return True
    return False


def _detect_arc_boundaries(
    ele: np.ndarray,
    azm: np.ndarray,
    seconds: np.ndarray,
    e1: float,
    e2: float,
    sat: int,
    min_pts: int = MIN_ARC_POINTS,
    gap_time: float = GAP_TIME_LIMIT,
) -> List[Tuple[int, int, int, int]]:
    """
    Detect arc boundaries based on time gaps and elevation direction changes.

    Elevation span QC (ediff) is handled by ``check_arc_quality()`` in callers,
    not here.  This function only enforces minimum point count.

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

    # Find breakpoints
    ddate = np.ediff1d(seconds)
    delv = np.ediff1d(ele)

    # Collect all breakpoints at once (np.unique returns sorted, no need for np.sort)
    gap_breaks = np.where(ddate > gap_time)[0]
    dir_breaks = np.where(np.diff(np.sign(delv)))[0]
    bkpt = np.unique(np.concatenate(([len(ddate)], gap_breaks, dir_breaks)))

    valid_arcs = []
    iarc = 0

    for ii in range(len(bkpt)):
        if ii == 0:
            sind = 0
        else:
            sind = bkpt[ii - 1] + 1
        eind = bkpt[ii] + 1

        arc_ele = ele[sind:eind]

        if len(arc_ele) == 0:
            continue

        # Check minimum point count
        if (eind - sind) < min_pts:
            continue

        iarc += 1
        valid_arcs.append((sind, eind, sat, iarc))

    return valid_arcs


def remove_dc_component(
    ele: np.ndarray,
    snr: np.ndarray,
    polyV: int,
    dbhz: bool,
    pele: Optional[List[float]] = None,
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
    pele : list of float, optional
        Elevation angle range [min, max] for polynomial fit.
        If provided, the polynomial is fit on data within this range
        but evaluated (and removed) over the full arc.

    Returns
    -------
    np.ndarray
        Detrended SNR data
    """
    data = snr.copy()

    # Convert to linear units if needed
    if not dbhz:
        data = np.power(10, (data / 20))

    # Fit polynomial on pele range if provided, otherwise full arc.
    # Polynomial.fit internally maps x to [-1, 1] before fitting, which keeps
    # the Vandermonde matrix well-conditioned and avoids numpy RankWarning.
    if pele is not None:
        pele_mask = (ele >= pele[0]) & (ele <= pele[1])
        if np.sum(pele_mask) > polyV + 1:
            poly = Polynomial.fit(ele[pele_mask], data[pele_mask], polyV)
        else:
            poly = Polynomial.fit(ele, data, polyV)
    else:
        poly = Polynomial.fit(ele, data, polyV)
    data = data - poly(ele)

    return data



def _compute_arc_metadata(
    ele: np.ndarray,
    azi: np.ndarray,
    seconds: np.ndarray,
    sat: int,
    freq: int,
    arc_num: int,
    e1: float,
    e2: float,
    az_avg: Optional[float] = None,
    cf: Optional[float] = None,
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
    e1 : float, optional
        Lower elevation angle limit for this arc's bin
    e2 : float, optional
        Upper elevation angle limit for this arc's bin
    az_avg : float, optional
        Pre-computed circular mean azimuth (avoids recomputation)
    cf : float, optional
        Pre-computed arc scale factor (wavelength/2)

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
    az_min_ele = azi[ie]

    # Compute edot factor (from window_new lines 975-987)
    # edot in radians/sec — direct linear regression (replaces np.polyfit degree 1)
    ele_rad = ele * (np.pi / 180)
    n = len(seconds)
    sx = seconds.sum()
    sy = ele_rad.sum()
    avgEdot_fit = (n * (seconds * ele_rad).sum() - sx * sy) / (n * (seconds * seconds).sum() - sx * sx)

    # Average tan(elev)
    cunit = np.tan(ele_rad).mean()

    # edot factor: tan(e)/edot in units of 1/(radians/hour)
    edot_factor = cunit / (avgEdot_fit * 3600) if avgEdot_fit != 0 else 0.0

    # Scale factor (wavelength/2)
    if cf is None:
        cf = get_scale_factor(freq, sat)

    # Circular mean azimuth
    if az_avg is None:
        az_avg = circular_mean_deg(azi)

    return {
        'sat': sat,
        'freq': freq,
        'arc_num': arc_num,
        'arc_type': arc_type,
        'ele_start': float(np.min(ele)),
        'ele_end': float(np.max(ele)),
        'az_min_ele': float(az_min_ele),
        'az_avg': float(az_avg),
        'time_start': float(np.min(seconds)),
        'time_end': float(np.max(seconds)),
        'arc_timestamp': float(np.mean(seconds) / 3600),  # hours UTC
        'num_pts': len(ele),
        'delT': float((np.max(seconds) - np.min(seconds)) / 60),  # minutes
        'edot_factor': float(edot_factor),
        'cf': float(cf),
        'e1': float(e1),
        'e2': float(e2),
    }


def load_results_with_failqc(station, year, doy, extension, require_failqc):
    """Load the combined results+failQC ndarray for one day.

    Reads results/{station}/[{extension}/]{doy:03d}.txt and the sibling
    failQC/ file written by retrieve_rh. Both files share the RESULT_COLUMNS
    layout; failQC rows have their RH column overwritten with NaN so that
    downstream consumers filtering on RH.notna() separate pass from fail
    without a second column.

    Parameters
    ----------
    station, year, doy : identifier tuple used by FileManagement.
    extension : strategy extension string ('' for the default strategy).
    require_failqc : bool
        When True, raise FileNotFoundError if the results file exists but
        the failQC sibling does not. The fast-path tracks loader sets this.
        When False, missing failQC is silently tolerated (used by the
        attach_results=['gnssir'] branch of extract_arcs_from_station).

    Returns
    -------
    np.ndarray or None
        Combined 2-D array with the same column layout as RESULT_COLUMNS, or
        None when neither file exists.
    """
    fm_ok = FileManagement(station, 'gnssir_result', year, doy, extension=extension)
    fm_fail = FileManagement(station, 'gnssir_failqc_result', year, doy, extension=extension)
    ok_path = fm_ok.get_file_path(ensure_directory=False)
    fail_path = fm_fail.get_file_path(ensure_directory=False)

    ok_rows = _load_result_file(ok_path) if ok_path.is_file() else None
    fail_rows = _load_result_file(fail_path) if fail_path.is_file() else None

    if ok_rows is None and fail_rows is None:
        return None

    if require_failqc and ok_path.is_file() and not fail_path.is_file():
        raise FileNotFoundError(
            f"failQC file missing at {fail_path}; please rerun gnssir "
            f"(failQC artifacts are now generated by default)"
        )

    if fail_rows is not None:
        rh_col = RESULT_COLUMNS.index('RH')
        fail_rows = fail_rows.copy()
        fail_rows[:, rh_col] = np.nan

    if ok_rows is not None and fail_rows is not None:
        return np.vstack([ok_rows, fail_rows])
    return ok_rows if ok_rows is not None else fail_rows


def extract_arcs_from_tracks(tracks_json, fast=False):
    """Walk active-epoch days in tracks_json and return tagged arcs as a DataFrame.

    Unified entry for the runtime-tagged per-arc dataset used by build_tracks'
    refit pass and by vwc phase/accumulation. Station and extension come from
    tracks_json['metadata']. Two sources are supported:

    * ``fast=False``: re-extract arcs fresh from SNR via
      extract_arcs_from_station, tagging against the (possibly QC-edited)
      in-memory tracks_json through a temp-file round-trip. Authoritative;
      slow.
    * ``fast=True``: read the gnssir results + failQC artifacts written for
      each active-epoch day via load_results_with_failqc, tagging each row
      against tracks_json via lookup_arc. Requires a prior gnssir run with
      save_failqc=True. Rows with no matching track are dropped.

    Returns a DataFrame with columns
    ``mjd, azim, constellation, RH, match_T, track_id, track_epoch``.
    ``match_T`` is always NaN so tracks.fit_segment falls back to the
    constellation's default repeat interval via the constellation column.
    """
    metadata = tracks_json['metadata']
    station = metadata['station']
    extension = metadata.get('extension', '')

    columns = ['mjd', 'azim', 'constellation', 'RH', 'match_T', 'track_id', 'track_epoch']
    days = active_epoch_days(tracks_json)
    if not days:
        return pd.DataFrame(columns=columns)

    if fast:
        index = build_lookup_index(tracks_json)
        track_constellation = {int(tid): track['constellation'] for tid, track in tracks_json['tracks'].items()}

        COL_SAT = RESULT_COLUMNS.index('sat')
        COL_FREQ = RESULT_COLUMNS.index('freq')
        COL_RISE = RESULT_COLUMNS.index('rise')
        COL_AZIM = RESULT_COLUMNS.index('Azim')
        COL_RH = RESULT_COLUMNS.index('RH')
        COL_MJD = RESULT_COLUMNS.index('MJD')

        rows = []
        for y, doy in sorted(days):
            results = load_results_with_failqc(station, y, doy, extension, require_failqc=True)
            if results is None:
                continue
            for i in range(results.shape[0]):
                sat = int(results[i, COL_SAT])
                freq = int(results[i, COL_FREQ])
                rise = int(results[i, COL_RISE])
                az = float(results[i, COL_AZIM])
                mjd = float(results[i, COL_MJD])
                tid, track_epoch, _entry = lookup_arc(sat, freq, mjd, az, rise, index)
                if tid < 0 or track_epoch < 0:
                    continue
                rows.append({
                    'mjd': mjd,
                    'azim': az,
                    'constellation': track_constellation.get(tid, ''),
                    'RH': float(results[i, COL_RH]),
                    'match_T': float('nan'),
                    'track_id': tid,
                    'track_epoch': track_epoch,
                })
        return pd.DataFrame(rows, columns=columns)

    json_path, _ = FileManagement(station, 'make_json', extension=extension).find_json_file()
    if not json_path.exists():
        raise FileNotFoundError(f'station config not found for {station} (extension={extension!r}): {json_path}')
    with open(json_path) as f:
        station_config = json.load(f)
    cfg = {**station_config, 'savearcs': False}

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
        json.dump(tracks_json, tf)
        temp_track_file = tf.name
    track_cache = {}

    freqs_all = all_frequencies()
    rows = []
    silent_buf = io.StringIO()
    try:
        with tqdm(sorted(days), desc=f'extract_arcs_from_tracks {station}', unit='day') as pbar:
            for y, doy in pbar:
                try:
                    with contextlib.redirect_stdout(silent_buf):
                        arcs = extract_arcs_from_station(
                            station, y, doy,
                            freq=freqs_all,
                            track_file=temp_track_file,
                            track_cache=track_cache,
                            attach_results=['gnssir'],
                            extension=extension,
                            station_config=cfg,
                            refraction_verbose=False,
                        )
                    silent_buf.truncate(0)
                    silent_buf.seek(0)
                except FileNotFoundError:
                    continue

                d = g.doy2ymd(int(y), int(doy))
                for meta, _data in arcs:
                    tid = int(meta['track_id'])
                    track_epoch = int(meta['track_epoch'])
                    if tid < 0 or track_epoch < 0:
                        continue
                    gnssir_res = meta.get('gnssir_processing_results')
                    rh = float(gnssir_res['RH']) if gnssir_res is not None else float('nan')
                    mjd = g.getMJD(int(y), d.month, d.day, float(meta['arc_timestamp']))
                    track_def = tracks_json['tracks'].get(str(tid))
                    constellation = track_def['constellation'] if track_def else ''
                    rows.append({
                        'mjd': mjd,
                        'azim': float(meta['az_min_ele']),
                        'constellation': constellation,
                        'RH': rh,
                        'match_T': float('nan'),
                        'track_id': tid,
                        'track_epoch': track_epoch,
                    })
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.remove(temp_track_file)
    return pd.DataFrame(rows, columns=columns)
