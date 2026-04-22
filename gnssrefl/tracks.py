"""
tracks.py: multi-GNSS track ground-truth for gnssrefl.

This module owns both sides of the multi-GNSS tracks.json artifact:

  * Build side: build_tracks walks SNR files via gnssrefl.extract_arcs,
    folds arcs into per-(sat, freq) periodic ground tracks, fits a single
    epoch per track, and writes the JSON.

  * Runtime side: load_tracks_json, build_lookup_index, lookup_arc, and
    attach_track_id consume the JSON to tag arcs at extract time with
    their (track_id, track_epoch).

Why
---
gnssrefl currently identifies VWC tracks by clustering arcs on azimuth alone
(+/-3 deg from cluster center). This works for GPS because GPS ground tracks
repeat every sidereal day, so a sat's daily passes have stable azimuths.
For non-GPS the repeat period is multi-day:

    GPS:        1 sidereal day  (2 orbits/day)
    GLONASS:    8 sidereal days (17 orbits / 8 sid days)
    Galileo:   10 sidereal days (17 orbits / 10 sid days)
    BeiDou MEO: 7 sidereal days (13 orbits / 7 sid days)

Within one repeat period a single sat traces 10-17 distinct ground tracks
across the sky. Pure az clustering can't separate them (they cover the
whole horizon), so the existing VWC code restricts to GPS. This module
produces a clean ground-truth track set for the other constellations.

This is the minimal MVP variant: each track has exactly one stable epoch
(epoch_id == 0). The schema reserves ``epochs`` as a list so future
changepoint-detection work can add entries without breaking readers.

Identity scope
--------------
There are two layers of identity in the tracks system:

* track_id is forever. The same id appears in every artifact derived from
  any tracks-shaped JSON (tracks.json, vwc_tracks.json, the per-day phase
  files, the vwc output files).
* epoch_id equals the epoch's list index (0..N-1) within one saved
  tracks_json. It is regenerated on every save_tracks and renumbered on
  every structural mutation (split_epoch, merge_epochs).
"""

import contextlib
import io
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

import gnssrefl.gps as g
from gnssrefl.gnss_frequencies import (
    BEIDOU_NON_MEO_SATS,
    all_frequencies,
    get_constellation,
)
from gnssrefl.gnssir_v2 import read_json_file
from gnssrefl.utils import FileManagement, circular_mean_deg
# Deferred imports of extract_arcs / phase_functions live inside the
# functions below; they form an import cycle with this module.


# ===========================================================================
# Constants
# ===========================================================================

SID_DAY = 0.99726958  # solar days
MJD_EPOCH = datetime(1858, 11, 17)

# Per-constellation ground-track repeat period(s) in sidereal days.
# BeiDou GEO/IGSO are filtered upstream via BEIDOU_NON_MEO_SATS.
CONSTELLATION_INFO = {
    'GPS':     {'T_sid_list': [1]},
    'GLONASS': {'T_sid_list': [8]},
    'Galileo': {'T_sid_list': [10]},
    'BeiDou':  {'T_sid_list': [7]},
}

# Matching tolerances, shared by build (when extending a track) and runtime lookup.
AZ_TOL = 5.0           # deg
TIME_TOL_MIN = 30      # minutes
MAX_GAP_CYCLES = 15    # bridge up to N missed cycles for a single match

# track_id == -1 means "not in a track"; kept rows always have track_id >= 0.

# How far outside [first_mjd, last_mjd] a query may fall and still match.
LOOKUP_MJD_BUFFER_D = 1.0


# ===========================================================================
# Time / azimuth helpers
# ===========================================================================

def doy_hour_to_mjd(year, doy, hours):
    """Convert (year, doy, fractional hours UTC) to MJD."""
    dt = datetime(year, 1, 1) + timedelta(days=int(doy) - 1, hours=float(hours))
    return (dt - MJD_EPOCH).total_seconds() / 86400.0


def mjd_to_iso_floor(mjd):
    """MJD -> ISO 8601 Z UTC string, rounded DOWN to the nearest second."""
    dt = MJD_EPOCH + timedelta(days=float(mjd))
    dt = dt.replace(microsecond=0)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def mjd_to_iso_ceil(mjd):
    """MJD -> ISO 8601 Z UTC string, rounded UP to the nearest second."""
    dt = MJD_EPOCH + timedelta(days=float(mjd))
    if dt.microsecond > 0:
        dt = dt.replace(microsecond=0) + timedelta(seconds=1)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def iso_to_mjd(iso_str):
    """ISO 8601 'YYYY-MM-DDTHH:MM:SSZ' UTC string -> MJD float."""
    dt = datetime.strptime(iso_str, '%Y-%m-%dT%H:%M:%SZ')
    return (dt - MJD_EPOCH).total_seconds() / 86400.0


def unwrap_az(az):
    """Bring all azimuths into a single ±180° window centered on az[0]."""
    if len(az) == 0:
        return az
    shifted = ((az - az[0] + 180) % 360) - 180
    return az[0] + shifted


# ===========================================================================
# BUILD SIDE
# ===========================================================================

def load_arcs(station, year, year_end, extension, snr_type=66, fast=False):
    """Collect per-arc geometry for station across [year..year_end] into a DataFrame.

    Unified SNR-walk and results-walk entry point. Both paths return the same
    schema (year, doy, sat, freq, mjd, azim, rise); the results path also
    carries RH (useful for later stats).

    * ``fast=False`` (default): walk SNR files day by day via
      extract_arcs_from_station. Authoritative; covers every frequency the
      SNR file contains. Slow.
    * ``fast=True``: read the gnssir results/ + failQC/ artifacts via
      load_results_with_failqc. Orders of magnitude faster, but only covers
      frequencies gnssir was configured to run. Requires a prior gnssir run
      with save_failqc=True.

    BeiDou GEO/IGSO PRNs in BEIDOU_NON_MEO_SATS are skipped here so the
    rest of the pipeline never sees them.
    """
    # Deferred: circular with extract_arcs.
    from gnssrefl.extract_arcs import RESULT_COLUMNS, extract_arcs_from_station, load_results_with_failqc

    rows = []
    t0 = time.time()

    if fast:
        COL_SAT = RESULT_COLUMNS.index('sat')
        COL_FREQ = RESULT_COLUMNS.index('freq')
        COL_RISE = RESULT_COLUMNS.index('rise')
        COL_AZIM = RESULT_COLUMNS.index('Azim')
        COL_MJD = RESULT_COLUMNS.index('MJD')
        COL_RH = RESULT_COLUMNS.index('RH')

        print(f'loading arcs for {station} {year}-{year_end} from results/+failQC/ (fast path)')
        n_days = n_missing = 0
        for y in range(year, year_end + 1):
            for doy in range(1, g.dec31(y) + 1):
                results = load_results_with_failqc(station, y, doy, extension, require_failqc=True)
                if results is None:
                    n_missing += 1
                    continue
                n_days += 1
                for i in range(results.shape[0]):
                    sat = int(results[i, COL_SAT])
                    if sat in BEIDOU_NON_MEO_SATS:
                        continue
                    rows.append({
                        'year': y, 'doy': doy, 'sat': sat,
                        'freq': int(results[i, COL_FREQ]),
                        'mjd':  float(results[i, COL_MJD]),
                        'azim': float(results[i, COL_AZIM]),
                        'rise': int(results[i, COL_RISE]),
                        'RH':   float(results[i, COL_RH]),
                    })
        print(f'done: {n_days} days processed, {n_missing} missing, {len(rows):,} arcs in {time.time()-t0:.1f}s')
        if not rows:
            raise RuntimeError('no arcs loaded from results/+failQC/: run gnssir first or use -source snr to build tracks directly from SNR files')
        return pd.DataFrame(rows)

    cfg = read_json_file(station, extension=extension, noexit=True, silent=True)
    if not cfg:
        raise FileNotFoundError(f'station config not found for {station} (extension={extension!r})')
    e1 = cfg['e1']
    e2 = cfg['e2']
    pele = cfg['pele']

    # Don't trigger savearcs side-effects from the gnssir json
    cfg = {**cfg, 'savearcs': False}

    freqs_all = all_frequencies()
    print(f'extracting arcs for {station} {year}-{year_end}, e1={e1} e2={e2}, {len(freqs_all)} freqs')

    n_processed = n_missing = n_errors = 0
    silent_buf = io.StringIO()
    day_list = [(y, doy) for y in range(year, year_end + 1) for doy in range(1, 367)]
    with tqdm(day_list, desc=f'load_arcs {station}', unit='day') as pbar:
        for y, doy in pbar:
            try:
                with contextlib.redirect_stdout(silent_buf):
                    arcs = extract_arcs_from_station(
                        station, y, doy,
                        freq=freqs_all,
                        snr_type=snr_type,
                        e1=e1, e2=e2, pele=pele,
                        detrend=False,
                        station_config=cfg,
                        screenstats=False,
                        refraction_verbose=False,
                    )
                silent_buf.truncate(0)
                silent_buf.seek(0)
            except FileNotFoundError:
                n_missing += 1
                continue
            except Exception as exc:
                n_errors += 1
                if n_errors <= 5:
                    pbar.write(f'  warning {y}/{doy}: {type(exc).__name__}: {exc}')
                continue

            for meta, _data in arcs:
                sat = int(meta['sat'])
                if sat in BEIDOU_NON_MEO_SATS:
                    continue
                rows.append({
                    'year': y,
                    'doy':  doy,
                    'sat':  sat,
                    'freq': int(meta['freq']),
                    'mjd':  doy_hour_to_mjd(y, doy, meta['arc_timestamp']),
                    'azim': float(meta['az_min_ele']),
                    'rise': 1 if meta['arc_type'] == 'rising' else -1,
                })

            n_processed += 1
            pbar.set_postfix_str(f'{len(rows):,} arcs')

    print(f'done: {n_processed} days processed, {n_missing} missing SNR files, '
          f'{n_errors} errors, {len(rows):,} arcs in {time.time()-t0:.0f}s')

    if not rows:
        raise RuntimeError('no arcs loaded: check station, year range, and SNR files')
    return pd.DataFrame(rows)


def results_dir_has_files(station, year, year_end, extension):
    """True if any year in the range has a populated results/ dir for station."""
    refl_code = os.environ.get('REFL_CODE', '')
    if not refl_code:
        return False
    for y in range(year, year_end + 1):
        results_dir = Path(refl_code) / str(y) / 'results' / station
        if extension:
            results_dir = results_dir / extension
        if results_dir.exists() and any(results_dir.iterdir()):
            return True
    return False


def assign_tracks(df_freq, T_candidates_solar):
    """Walk arcs forward in MJD and assign track ids.

    Returns (df_sorted, track_ids, match_T) where match_T[i] is the candidate
    T (in solar days) used to extend arc i, or NaN if arc i seeded a new track.
    """
    df_freq = df_freq.sort_values('mjd').reset_index(drop=True)
    n = len(df_freq)
    track_ids = np.full(n, -1, dtype=np.int64)
    match_T = np.full(n, np.nan)

    time_tol = TIME_TOL_MIN / 1440  # solar days
    next_id = 0
    sat_tracks = {}

    sats  = df_freq.sat.values.astype(np.int64)
    mjds  = df_freq.mjd.values
    azs   = df_freq.azim.values
    rises = (df_freq['rise'].values > 0)

    for i in range(n):
        sat  = int(sats[i])
        mjd  = mjds[i]
        az   = azs[i]
        rise = bool(rises[i])

        cands = sat_tracks.get(sat, [])
        best_j = -1
        best_T = -1.0
        best_score = float('inf')

        for j in range(len(cands)):
            tid, mjd_a, az_a, rise_a = cands[j]
            if rise_a != rise:
                continue
            dt = mjd - mjd_a
            if dt <= 0:
                continue
            daz = (az - az_a + 180.0) % 360.0 - 180.0
            if abs(daz) > AZ_TOL:
                continue

            for T in T_candidates_solar:
                ncycles = int(round(dt / T))
                if ncycles < 1 or ncycles > MAX_GAP_CYCLES:
                    continue
                phase_err = abs(dt - ncycles * T)
                if phase_err > time_tol:
                    continue
                score = phase_err / time_tol + abs(daz) / AZ_TOL
                if score < best_score:
                    best_score = score
                    best_j = j
                    best_T = T

        if best_j >= 0:
            tid = cands[best_j][0]
            cands[best_j] = [tid, mjd, az, rise]
            track_ids[i] = tid
            match_T[i] = best_T
        else:
            tid = next_id
            next_id += 1
            cands.append([tid, mjd, az, rise])
            sat_tracks[sat] = cands
            track_ids[i] = tid

    return df_freq, track_ids, match_T


def fit_segment(arcs):
    """Fit T and azimuth model for a single track's arcs.

    Returns (T_fit, anchor_mjd, az_avg_minel, az_drift_rate).
    az_drift_rate is only nonzero for BeiDou (secular azimuth drift).
    """
    arcs = arcs.sort_values('mjd')
    mjd = arcs.mjd.values
    az_raw = arcs.azim.values
    n = len(mjd)
    constellation = arcs.constellation.iloc[0]

    match_T = arcs.match_T.dropna()
    T_init = float(match_T.median()) if len(match_T) else CONSTELLATION_INFO[constellation]['T_sid_list'][0] * SID_DAY

    anchor = float(mjd[0])
    cycles = np.round((mjd - anchor) / T_init).astype(np.int64)
    T_fit = T_init
    if n >= 2 and (cycles.max() - cycles.min()) > 0:
        for _ in range(5):
            T_new, anchor_new = np.polyfit(cycles, mjd, 1)
            new_cycles = np.round((mjd - anchor_new) / T_new).astype(np.int64)
            T_fit, anchor = float(T_new), float(anchor_new)
            if np.array_equal(new_cycles, cycles):
                break
            cycles = new_cycles

    if constellation == 'BeiDou' and n >= 2:
        az_u = unwrap_az(az_raw)
        az_drift_rate, az_avg_minel = np.polyfit(mjd - anchor, az_u, 1)
        az_drift_rate = float(az_drift_rate)
        az_avg_minel = float(az_avg_minel)
    else:
        az_drift_rate = 0.0
        az_avg_minel = float(circular_mean_deg(az_raw)) if n else 0.0

    return T_fit, anchor, az_avg_minel, az_drift_rate


def build_tracks(station, year, year_end=None, extension='',
                 snr_type=66, source='auto'):
    """Build tracks.json for a station over [year .. year_end].

    Collects per-arc geometry (sat, freq, mjd, azim, rise), folds arcs into
    periodic tracks, drops fragment tracks below the per-freq filter
    threshold (10 percent of per-freq median arcs per track), fits a single
    periodic epoch per surviving track, and writes the JSON via
    FileManagement.

    Two arc sources are supported, selected by ``source``:

    * ``'snr'``      walk SNR files via load_arcs: authoritative, slow,
                     covers every frequency the SNR file contains.
    * ``'results'``  read results/ + failQC/ via load_arcs_from_results:
                     fast, but only covers frequencies gnssir was run with.
    * ``'auto'``     (default) prefer ``'results'`` if any results/ dir is
                     populated in range; else fall back to ``'snr'``.

    Parameters
    ----------
    station : str
        4-char station name (lowercase)
    year : int
        Start year
    year_end : int, optional
        End year inclusive. Defaults to ``year``.
    extension : str
        Strategy extension subdirectory. Default ''.
    snr_type : int
        SNR file type for the SNR-walk path. Default 66.
    source : str
        Arc source: 'auto' | 'results' | 'snr'. Default 'auto'.

    Returns
    -------
    tracks_json : dict
        In-memory tracks_json matching the on-disk JSON.
    arcs_df : pandas.DataFrame or None
        Per-arc DataFrame in the extract_arcs_gnssir_results schema
        (mjd, azim, constellation, RH, match_T, track_id, track_epoch),
        or None when source='snr' (no RH available).
    """
    if year_end is None:
        year_end = year
    if year_end < year:
        raise ValueError(f'year_end ({year_end}) must be >= year ({year})')

    fm = FileManagement(station, 'tracks_file', extension=extension)
    out_path = fm.get_file_path(ensure_directory=True)

    if source == 'auto':
        source = 'results' if results_dir_has_files(station, year, year_end, extension) else 'snr'
        print(f'tracks source: auto-detected {source!r}')
    if source == 'results':
        df = load_arcs(station, year, year_end, extension, fast=True)
    elif source == 'snr':
        df = load_arcs(station, year, year_end, extension, snr_type=snr_type, fast=False)
    else:
        raise ValueError(f"source must be 'auto', 'results', or 'snr'; got {source!r}")

    print(f'tolerances: az +/-{AZ_TOL} deg, time +/-{TIME_TOL_MIN} min, '
          f'max_gap {MAX_GAP_CYCLES} cycles')

    available_freqs = [f for f in all_frequencies() if (df.freq == f).any()]
    print(f'processing frequencies: {available_freqs}')

    all_results = []
    id_offset = 0
    for freq in available_freqs:
        constellation = get_constellation(freq)
        info = CONSTELLATION_INFO[constellation]
        repeat_interval_d_list = [t * SID_DAY for t in info['T_sid_list']]

        sub_cols = ['sat', 'mjd', 'azim', 'rise']
        if 'RH' in df.columns:
            sub_cols = sub_cols + ['RH']
        sub = df[df.freq == freq][sub_cols].copy()
        if len(sub) == 0:
            continue

        sub_sorted, tids, match_T = assign_tracks(sub, repeat_interval_d_list)
        sub_sorted['track_id'] = tids
        sub_sorted['match_T'] = match_T
        sub_sorted['freq'] = freq
        sub_sorted['constellation'] = constellation

        # Globally unique track ids across freqs (real ids only)
        mask = sub_sorted.track_id >= 0
        sub_sorted.loc[mask, 'track_id'] += id_offset
        if mask.any():
            id_offset = int(sub_sorted.loc[mask, 'track_id'].max() + 1)

        all_results.append(sub_sorted)

    out = pd.concat(all_results, ignore_index=True)
    kept = out[out.track_id >= 0].reset_index(drop=True)

    print(f'building tracks_json over {len(kept):,} kept arcs '
          f'({kept.track_id.nunique():,} unique track_ids)')

    tracks_dict = {}
    for tid, t_arcs in kept.groupby('track_id'):
        T_fit, anchor_mjd, az_avg_minel, az_drift_rate = fit_segment(t_arcs)
        first_mjd = float(t_arcs.mjd.min())
        last_mjd = float(t_arcs.mjd.max())
        epoch = {
            'epoch_id':          0,
            'epoch_type':        'active',
            'start_time':        mjd_to_iso_floor(first_mjd),
            'end_time':          mjd_to_iso_ceil(last_mjd),
            'anchor_time':       mjd_to_iso_floor(anchor_mjd),
            'ignored_ranges':    [],
            'duration_d':        round(last_mjd - first_mjd, 2),
            'repeat_interval_d': round(T_fit, 6),
            'n_arcs':            int(len(t_arcs)),
            'az_avg_minel':      round(az_avg_minel, 3),
        }
        if az_drift_rate != 0.0:
            epoch['az_drift_rate'] = round(az_drift_rate, 7)

        first = t_arcs.iloc[0]
        tracks_dict[str(int(tid))] = {
            'constellation': str(first.constellation),
            'sat':           int(first.sat),
            'freq':          int(first.freq),
            'rise':          int(first['rise']),
            'epochs':        [epoch],
        }

    tracks_dict = dict(sorted(tracks_dict.items(), key=lambda x: int(x[0])))

    data_mjd_min = float(kept.mjd.min())
    data_mjd_max = float(kept.mjd.max())

    now_iso = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    n_arcs_total = sum(int(t['epochs'][0]['n_arcs']) for t in tracks_dict.values())
    tracks_json = {
        'metadata': {
            'file_type':          'tracks',
            'station':            station,
            'extension':          extension,
            'start_time':          mjd_to_iso_floor(data_mjd_min),
            'end_time':            mjd_to_iso_ceil(data_mjd_max),
            'duration_d':          int(round(data_mjd_max - data_mjd_min)),
            'n_tracks':            len(tracks_dict),
            'n_epochs':            len(tracks_dict),
            'n_arcs':              n_arcs_total,
            'generated_at':        now_iso,
            'history': [
                {'timestamp': now_iso, 'tool': 'build_tracks', 'note': ''},
            ],
        },
        'tracks': tracks_dict,
    }

    with open(out_path, 'w') as f:
        write_tracks_json(tracks_json, f)

    print(f'wrote {out_path}')
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f'  file size:   {size_mb:.2f} MB')
    print(f'  tracks:      {tracks_json["metadata"]["n_tracks"]}')

    if 'RH' in kept.columns:
        arcs_df = pd.DataFrame({
            'mjd':           kept['mjd'].astype(float).values,
            'azim':          kept['azim'].astype(float).values,
            'constellation': kept['constellation'].astype(str).values,
            'RH':            kept['RH'].astype(float).values,
            'match_T':       np.nan,
            'track_id':      kept['track_id'].astype(int).values,
            'track_epoch':   0,
        })
    else:
        arcs_df = None

    return tracks_json, arcs_df


# ===========================================================================
# RUNTIME SIDE
# ===========================================================================

_IGNORED_RANGE_PAIR_RE = re.compile(
    r'\[\s+(-?[\d.eE+\-]+),\s+(-?[\d.eE+\-]+)\s+\]'
)


def write_tracks_json(tracks_json, f):
    """Write tracks_json to file handle ``f`` with custom indentation for
    readability: indent=2 at the structural level, but each inner
    ``ignored_ranges`` pair ``[mjd_start, mjd_end]`` is collapsed onto a
    single line so the range reads as one atomic value.
    """
    text = json.dumps(tracks_json, indent=2)
    text = _IGNORED_RANGE_PAIR_RE.sub(r'[\1, \2]', text)
    f.write(text)


def load_tracks_json(path):
    """Load a tracks.json file from disk and return the tracks_json dict."""
    with open(path) as f:
        return json.load(f)


def build_lookup_index(tracks_json):
    """Build a (sat, freq) -> [(track_id, track_epoch, def_dict), ...] index.

    Each ``def_dict`` carries the fields needed by lookup_arc:
        rise, repeat_interval_d, anchor_mjd, az_avg_minel, az_drift_rate,
        first_mjd, last_mjd, epoch_type
    """
    index = {}
    for tid_str, track in tracks_json['tracks'].items():
        sat = int(track['sat'])
        if sat in BEIDOU_NON_MEO_SATS:
            continue
        freq = int(track['freq'])
        rise = int(track['rise'])
        track_id = int(tid_str)
        for ep in track['epochs']:
            track_epoch = int(ep['epoch_id'])
            first_mjd = iso_to_mjd(ep['start_time'])
            last_mjd = iso_to_mjd(ep['end_time'])
            kind = ep['epoch_type']
            if kind == 'active':
                anchor_mjd = iso_to_mjd(ep['anchor_time'])
                repeat_interval_d = float(ep['repeat_interval_d'])
                az_avg_minel = float(ep['az_avg_minel'])
                az_drift_rate = float(ep.get('az_drift_rate', 0.0))
            else:
                anchor_mjd = first_mjd
                repeat_interval_d = float('nan')
                az_avg_minel = float('nan')
                az_drift_rate = 0.0
            entry = (track_id, track_epoch, {
                'rise':         rise,
                'first_mjd':    first_mjd,
                'last_mjd':     last_mjd,
                'anchor_mjd':   anchor_mjd,
                'repeat_interval_d':      repeat_interval_d,
                'az_avg_minel':       az_avg_minel,
                'az_drift_rate':     az_drift_rate,
                'epoch_type':   kind,
                'apriori_RH':   ep.get('apriori_RH'),
                'ignored_ranges': [
                    [float(r[0]), float(r[1])] for r in ep['ignored_ranges']
                ],
            })
            index.setdefault((sat, freq), []).append(entry)
    return index


def lookup_arc(sat, freq, mjd, az, rise, index,
               az_tol=AZ_TOL, time_tol_min=TIME_TOL_MIN,
               mjd_buffer_d=LOOKUP_MJD_BUFFER_D):
    """Look up the (track_id, track_epoch, epoch_entry) for a single arc.

    Active matches require the query to fall inside the track's
    ``[first_mjd - buffer, last_mjd + buffer]`` interval AND fit the periodic
    model within ``time_tol_min`` and ``az_tol``.

    Returns
    -------
    (track_id, track_epoch, entry) : tuple
        ``(-1, -1, None)`` if no track def covers this arc. ``entry`` is the
        matched epoch dict from ``build_lookup_index`` (keys include
        ``az_avg_minel`` and ``apriori_RH``) when the match succeeds.
    """
    cands = index.get((int(sat), int(freq)), [])
    best_score = float('inf')
    best_match = (-1, -1, None)

    for tid, track_epoch, t in cands:
        if t['rise'] != rise:
            continue
        if mjd < t['first_mjd'] - mjd_buffer_d:
            continue
        if mjd > t['last_mjd'] + mjd_buffer_d:
            continue
        if t['epoch_type'] != 'active':
            continue
        in_ignored = False
        for r_start, r_end in t['ignored_ranges']:
            if r_start <= mjd <= r_end:
                in_ignored = True
                break
        if in_ignored:
            continue

        dt_anchor = mjd - t['anchor_mjd']
        expected_az = t['az_avg_minel'] + t['az_drift_rate'] * dt_anchor
        daz = abs(((az - expected_az + 180.0) % 360.0) - 180.0)
        if daz > az_tol:
            continue
        T = t['repeat_interval_d']
        n_cycles = round(dt_anchor / T)
        expected = t['anchor_mjd'] + n_cycles * T
        err_min = abs(mjd - expected) * 1440.0
        if err_min > time_tol_min:
            continue
        score = daz / az_tol + err_min / time_tol_min
        if score < best_score:
            best_score = score
            best_match = (tid, track_epoch, t)

    return best_match


def attach_track_id(arcs, track_file_path, year, doy, track_cache=None):
    """Tag each arc's metadata with track info from tracks-shaped JSON.

    Works against both ``tracks.json`` (the station-wide catalog) and
    ``vwc_tracks.json`` (the VWC-eligible filtered subset, which adds a per
    epoch ``apriori_RH`` field).

    Each ``metadata`` dict gets these new keys:
        ``track_id``, ``track_epoch`` (both -1 on no match),
        ``track_azim`` (``az_avg_minel`` of the matched epoch, or ``None``),
        ``apriori_RH`` (matched epoch's ``apriori_RH``, or ``None``; only
        present in ``vwc_tracks.json``).

    Parameters
    ----------
    arcs : list of (metadata, data) tuples
        Output of ``extract_arcs``, modified in place.
    track_file_path : path-like
        Path to a tracks-shaped JSON file (``tracks.json`` from
        build_tracks, or ``vwc_tracks.json`` from ``vwc_input``).
    year, doy : int
        Year and day-of-year of the arcs (used together with each arc's
        ``arc_timestamp`` to compute MJD for the lookup).
    track_cache : dict, optional
        Shared dict for reusing the same tracks JSON across many calls. Pass
        the same dict on each call; the JSON is loaded and indexed on the
        first call and reused thereafter.

    Returns
    -------
    list
        The same ``arcs`` list (modified in place), for chaining.
    """
    track_file_path = str(track_file_path)
    if track_cache is not None and track_cache.get('path') == track_file_path:
        index = track_cache['index']
    else:
        tracks_json = load_tracks_json(track_file_path)
        index = build_lookup_index(tracks_json)
        if track_cache is not None:
            track_cache['path'] = track_file_path
            track_cache['index'] = index

    d = g.doy2ymd(int(year), int(doy))

    for metadata, _data in arcs:
        sat = int(metadata['sat'])
        freq = int(metadata['freq'])
        az = float(metadata['az_min_ele'])
        rise = 1 if metadata['arc_type'] == 'rising' else -1
        mjd = g.getMJD(int(year), d.month, d.day, float(metadata['arc_timestamp']))

        track_id, track_epoch, entry = lookup_arc(sat, freq, mjd, az, rise, index)
        metadata['track_id'] = int(track_id)
        metadata['track_epoch'] = int(track_epoch)
        if entry is not None:
            metadata['track_azim'] = float(entry['az_avg_minel'])
            metadata['apriori_RH'] = entry.get('apriori_RH')
        else:
            metadata['track_azim'] = None
            metadata['apriori_RH'] = None

    return arcs


def attach_legacy_apriori(arcs, station, extension=''):
    """Tag arcs with legacy GPS-only per-freq apriori_rh_{fr}.txt entries.

    Groups arcs by frequency, loads ``apriori_rh_{fr}.txt`` once per freq, and
    matches each arc to a track by (satellite, circular azimuth distance <= 3 deg),
    the same rule used historically by the legacy VWC pipeline.

    Sets ``meta['apriori_RH']``, ``meta['track_azim']``, ``meta['track_id']``,
    and ``meta['track_epoch']`` on every arc. ``apriori_RH`` / ``track_azim``
    are ``None`` on miss; ``track_id`` / ``track_epoch`` are ``-1`` on miss.
    ``track_epoch`` is always ``0`` on match (the legacy path has only one
    epoch per track).
    """
    # Deferred: circular with phase_functions via extract_arcs.
    from gnssrefl.phase_functions import read_apriori_rh
    from gnssrefl.utils import circular_distance_deg

    apriori_by_freq = {}

    for metadata, _data in arcs:
        metadata['apriori_RH'] = None
        metadata['track_azim'] = None
        metadata['track_id'] = -1
        metadata['track_epoch'] = -1

        freq = int(metadata['freq'])
        if freq not in apriori_by_freq:
            try:
                apriori_by_freq[freq] = read_apriori_rh(station, freq, extension)
            except (SystemExit, FileNotFoundError):
                apriori_by_freq[freq] = None
        table = apriori_by_freq[freq]
        if table is None or len(table) == 0:
            continue

        sat = int(metadata['sat'])
        az_min_ele = float(metadata['az_min_ele'])
        for row in table:
            if int(row[2]) != sat:
                continue
            track_azim = float(row[3])
            if circular_distance_deg(az_min_ele, track_azim) <= 3:
                metadata['apriori_RH'] = float(row[1])
                metadata['track_azim'] = track_azim
                metadata['track_id'] = int(row[0])
                metadata['track_epoch'] = 0
                break

    return arcs


def warn_legacy_apriori_and_exit(station, missing_file, extension=''):
    """If any GPS ``apriori_rh_{fr}.txt`` exists, print a -legacy T hint and exit.

    Called from modern-path entry points when ``missing_file`` (e.g.
    ``vwc_tracks.json``) is absent, to nudge users who still have artifacts
    from a legacy GPS-only run toward passing ``-legacy T``.
    """
    for fr in (1, 20, 5):
        fm = FileManagement(station, 'apriori_rh_file', frequency=fr, extension=extension)
        if fm.get_file_path(ensure_directory=False).exists():
            print(f'Note: {missing_file} not found, but an apriori_rh file exists from a previous')
            print('GPS-only run. Did you mean to pass -legacy T to use that file?')
            sys.exit()


def active_epoch_days(tracks_json):
    """Set of (year, doy) pairs spanning the union of active epoch windows."""
    days = set()
    for track in tracks_json.get('tracks', {}).values():
        for ep in track['epochs']:
            if ep['epoch_type'] != 'active':
                continue
            s_mjd = iso_to_mjd(ep['start_time'])
            e_mjd = iso_to_mjd(ep['end_time'])
            cur = int(np.floor(s_mjd))
            end = int(np.floor(e_mjd))
            while cur <= end:
                dt = MJD_EPOCH + timedelta(days=cur)
                doy = (dt - datetime(dt.year, 1, 1)).days + 1
                days.add((dt.year, doy))
                cur += 1
    return days


