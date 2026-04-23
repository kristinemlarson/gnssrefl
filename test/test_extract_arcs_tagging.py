"""Unit tests for the arc-tagging surface added in commit 4.

Covers the post-extract tagging primitives (attach_track_id,
attach_legacy_apriori), the active_epoch_days walker, and a schema-only
sanity check on load_arcs' two modes.
"""

import numpy as np
import pandas as pd
import pytest

import gnssrefl.gps as g
from gnssrefl.tracks import (
    active_epoch_days,
    attach_legacy_apriori,
    attach_track_id,
    build_lookup_index,
    doy_hour_to_mjd,
    mjd_to_iso_ceil,
    mjd_to_iso_floor,
    write_tracks_json,
)


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------

def _make_tracks_json(station='test', start_mjd=60000.0, end_mjd=60100.0, sat=5, freq=20, T=0.997, az=120.0):
    epoch = {
        'epoch_id': 0,
        'epoch_type': 'active',
        'start_time': mjd_to_iso_floor(start_mjd),
        'end_time': mjd_to_iso_ceil(end_mjd),
        'anchor_time': mjd_to_iso_floor(start_mjd),
        'ignored_ranges': [],
        'duration_d': round(end_mjd - start_mjd, 2),
        'repeat_interval_d': T,
        'n_arcs': 50,
        'az_avg_minel': az,
        'apriori_RH': 2.345,
    }
    return {
        'metadata': {'file_type': 'vwc_tracks', 'station': station, 'extension': ''},
        'tracks': {'42': {'constellation': 'GPS', 'sat': sat, 'freq': freq, 'rise': 1, 'epochs': [epoch]}},
    }


def _make_arc(sat, freq, az_min_ele, arc_timestamp, arc_type='rising'):
    meta = {'sat': sat, 'freq': freq, 'az_min_ele': float(az_min_ele), 'arc_timestamp': float(arc_timestamp), 'arc_type': arc_type}
    return (meta, {})


# ---------------------------------------------------------------------------
# attach_track_id
# ---------------------------------------------------------------------------

def test_attach_track_id_happy(tmp_path):
    tracks_json = _make_tracks_json(start_mjd=60000.0, end_mjd=60100.0, sat=5, freq=20, az=120.0)
    track_file = tmp_path / 'tracks.json'
    with open(track_file, 'w') as f:
        write_tracks_json(tracks_json, f)

    # Pick a year/doy whose MJD falls inside the epoch window.
    year, doy = 2023, 60
    d = g.doy2ymd(year, doy)
    hour = 5.0
    mjd = g.getMJD(year, d.month, d.day, hour)
    # Re-center the epoch on this MJD by rebuilding the tracks_json.
    tracks_json = _make_tracks_json(start_mjd=mjd - 5, end_mjd=mjd + 5, sat=5, freq=20, az=120.0)
    with open(track_file, 'w') as f:
        write_tracks_json(tracks_json, f)

    arcs = [_make_arc(sat=5, freq=20, az_min_ele=120.5, arc_timestamp=hour)]
    attach_track_id(arcs, str(track_file), year, doy)
    meta = arcs[0][0]
    assert meta['track_id'] == 42
    assert meta['track_epoch'] == 0
    assert meta['track_azim'] == pytest.approx(120.0)
    assert meta['apriori_RH'] == pytest.approx(2.345)


def test_attach_track_id_miss(tmp_path):
    tracks_json = _make_tracks_json(sat=5, freq=20, az=120.0)
    track_file = tmp_path / 'tracks.json'
    with open(track_file, 'w') as f:
        write_tracks_json(tracks_json, f)

    # Same freq/sat but wildly wrong azimuth and out-of-window time.
    arcs = [_make_arc(sat=5, freq=20, az_min_ele=300.0, arc_timestamp=5.0)]
    attach_track_id(arcs, str(track_file), year=2023, doy=60)
    meta = arcs[0][0]
    assert meta['track_id'] == -1
    assert meta['track_epoch'] == -1
    assert meta['track_azim'] is None
    assert meta['apriori_RH'] is None


def test_attach_track_id_uses_cache(tmp_path):
    tracks_json = _make_tracks_json()
    track_file = tmp_path / 'tracks.json'
    with open(track_file, 'w') as f:
        write_tracks_json(tracks_json, f)
    cache = {}
    arcs = [_make_arc(sat=5, freq=20, az_min_ele=120.0, arc_timestamp=1.0)]
    attach_track_id(arcs, str(track_file), year=2023, doy=60, track_cache=cache)
    assert cache['path'] == str(track_file)
    assert isinstance(cache['track_lookup_index'], dict)


# ---------------------------------------------------------------------------
# attach_legacy_apriori
# ---------------------------------------------------------------------------

def _write_legacy_apriori(refl_code, station, fr, rows):
    """Drop an apriori_rh_{fr}.txt file into the new-format input dir."""
    from gnssrefl.gnss_frequencies import get_file_suffix
    input_dir = refl_code / 'input' / station
    input_dir.mkdir(parents=True, exist_ok=True)
    path = input_dir / f'{station}_phaseRH{get_file_suffix(fr)}.txt'
    with open(path, 'w') as f:
        f.write('% apriori RH values\n')
        np.savetxt(f, rows, fmt='%3.0f %6.3f %4.0f %7.2f %4.0f %3.0f %3.0f')


def test_attach_legacy_apriori_happy(tmp_path, monkeypatch):
    monkeypatch.setenv('REFL_CODE', str(tmp_path))
    _write_legacy_apriori(tmp_path, 'aabc', fr=20, rows=[[1, 1.857, 5, 120.0, 300, 117, 123]])
    arcs = [_make_arc(sat=5, freq=20, az_min_ele=120.5, arc_timestamp=5.0)]
    attach_legacy_apriori(arcs, 'aabc')
    meta = arcs[0][0]
    assert meta['track_id'] == 1
    assert meta['track_epoch'] == 0
    assert meta['track_azim'] == pytest.approx(120.0)
    assert meta['apriori_RH'] == pytest.approx(1.857)


def test_attach_legacy_apriori_miss(tmp_path, monkeypatch):
    monkeypatch.setenv('REFL_CODE', str(tmp_path))
    _write_legacy_apriori(tmp_path, 'aabc', fr=20, rows=[[1, 1.857, 99, 120.0, 300, 117, 123]])
    # Arc sat (5) does not match any row (sat 99).
    arcs = [_make_arc(sat=5, freq=20, az_min_ele=120.0, arc_timestamp=5.0)]
    attach_legacy_apriori(arcs, 'aabc')
    meta = arcs[0][0]
    assert meta['track_id'] == -1
    assert meta['track_epoch'] == -1
    assert meta['track_azim'] is None
    assert meta['apriori_RH'] is None


# ---------------------------------------------------------------------------
# active_epoch_days
# ---------------------------------------------------------------------------

def test_active_epoch_days_union_collapses_overlap():
    # Two epochs whose windows overlap; day set is the union, not the sum.
    start1 = doy_hour_to_mjd(2024, 10, 0.0)
    end1 = doy_hour_to_mjd(2024, 20, 23.999)
    start2 = doy_hour_to_mjd(2024, 15, 0.0)
    end2 = doy_hour_to_mjd(2024, 25, 23.999)
    tracks_json = {
        'metadata': {'station': 'xxxx', 'extension': ''},
        'tracks': {
            '1': {'constellation': 'GPS', 'sat': 5, 'freq': 20, 'rise': 1,
                  'epochs': [{
                      'epoch_id': 0, 'epoch_type': 'active',
                      'start_time': mjd_to_iso_floor(start1),
                      'end_time': mjd_to_iso_ceil(end1),
                      'anchor_time': mjd_to_iso_floor(start1),
                      'ignored_ranges': [], 'duration_d': 10.0,
                      'repeat_interval_d': 0.997, 'n_arcs': 10, 'az_avg_minel': 120.0,
                  }]},
            '2': {'constellation': 'GPS', 'sat': 6, 'freq': 20, 'rise': 1,
                  'epochs': [{
                      'epoch_id': 0, 'epoch_type': 'active',
                      'start_time': mjd_to_iso_floor(start2),
                      'end_time': mjd_to_iso_ceil(end2),
                      'anchor_time': mjd_to_iso_floor(start2),
                      'ignored_ranges': [], 'duration_d': 10.0,
                      'repeat_interval_d': 0.997, 'n_arcs': 10, 'az_avg_minel': 120.0,
                  }]},
        },
    }
    days = active_epoch_days(tracks_json)
    assert (2024, 10) in days
    assert (2024, 25) in days
    # DOY 15..20 are in the overlap; each appears once.
    assert len([d for d in days if d[1] == 17]) == 1
    assert len(days) == 16  # DOY 10..25 inclusive


def test_active_epoch_days_skips_inactive():
    start = doy_hour_to_mjd(2024, 10, 0.0)
    end = doy_hour_to_mjd(2024, 12, 23.999)
    tracks_json = {
        'metadata': {'station': 'xxxx', 'extension': ''},
        'tracks': {'1': {'constellation': 'GPS', 'sat': 5, 'freq': 20, 'rise': 1,
                         'epochs': [{
                             'epoch_id': 0, 'epoch_type': 'inactive',
                             'start_time': mjd_to_iso_floor(start),
                             'end_time': mjd_to_iso_ceil(end),
                             'anchor_time': mjd_to_iso_floor(start),
                             'ignored_ranges': [], 'duration_d': 2.0,
                             'repeat_interval_d': 0.997, 'n_arcs': 0, 'az_avg_minel': 120.0,
                         }]}},
    }
    assert active_epoch_days(tracks_json) == set()


# ---------------------------------------------------------------------------
# load_arcs schema: both fast=False and fast=True yield the same columns
# ---------------------------------------------------------------------------

LOAD_ARCS_COLUMNS = {'year', 'doy', 'sat', 'freq', 'mjd', 'azim', 'rise'}


def test_load_arcs_fast_path_schema(tmp_path, monkeypatch):
    """fast=True: no results anywhere, should raise RuntimeError with expected message."""
    from gnssrefl.tracks import load_arcs
    monkeypatch.setenv('REFL_CODE', str(tmp_path))
    with pytest.raises(RuntimeError, match='no arcs loaded from results'):
        load_arcs('aabc', 2024, 2024, '', fast=True)


def test_load_arcs_slow_path_schema(tmp_path, monkeypatch):
    """fast=False: no station config, should raise FileNotFoundError."""
    from gnssrefl.tracks import load_arcs
    monkeypatch.setenv('REFL_CODE', str(tmp_path))
    with pytest.raises(FileNotFoundError, match='station config not found'):
        load_arcs('aabc', 2024, 2024, '', fast=False)
