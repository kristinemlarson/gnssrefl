"""Round-trip tests for the (track_id, track_epoch) tags carried in raw.phase.

The default-path phase file gained two extra columns (TrackID, TrackEpoch)
so that the downstream VWC reader no longer needs to rematch arcs to tracks.
These tests exercise the writer/reader pair and the column-count guard.
"""
from pathlib import Path

import numpy as np
import pytest

from gnssrefl import phase_functions as qp


def make_phase_row(year, doy, hr, sat, az, freq, tid, ep, fr_value=20):
    # Per-day default layout: 16 core cols + (TrackID, TrackEpoch).
    return [year, doy, hr, 12.5, 100, az, sat, 1.5,
            5.0, 25.0, 0.5, 2.0, fr_value, 2.05, 4.0, 6.0,
            tid, ep]


def test_write_out_raw_phase_round_trip(tmp_path):
    """Default per-day input becomes raw.phase with quad/unphase inserted and TrackID/TrackEpoch preserved at the end."""
    rows = np.array([
        make_phase_row(2024, 1, 6.0, 5, 120.0, 20, tid=7041, ep=0),
        make_phase_row(2024, 2, 6.1, 5, 121.0, 20, tid=7041, ep=0),
        make_phase_row(2024, 3, 6.2, 5, 119.5, 20, tid=7041, ep=0),
    ])
    out = tmp_path / 'raw.phase'
    written = qp.write_out_raw_phase(rows, out, legacy=False)

    tid_col = qp.PHASE_COLS.index('TrackID')
    ep_col = qp.PHASE_COLS.index('TrackEpoch')
    quad_col = qp.PHASE_COLS.index('quad')
    unphase_col = qp.PHASE_COLS.index('unphase')

    assert written.shape == (3, len(qp.PHASE_COLS))
    assert np.all(written[:, tid_col] == 7041)
    assert np.all(written[:, ep_col] == 0)
    assert set(written[:, quad_col]).issubset({1, 2, 3, 4})
    loaded = np.loadtxt(out, comments='%')
    np.testing.assert_allclose(loaded[:, tid_col], 7041)
    np.testing.assert_allclose(loaded[:, ep_col], 0)
    np.testing.assert_allclose(loaded[:, unphase_col], written[:, unphase_col])


def test_write_out_raw_phase_legacy_round_trip(tmp_path):
    """Legacy per-day input becomes raw.phase with quad/unphase appended (no tags)."""
    rows = []
    for d in (1, 2, 3):
        rows.append([2024, d, 6.0, 12.5, 100, 120.0, 5, 1.5,
                     5.0, 25.0, 0.5, 2.0, 20, 2.05, 4.0, 6.0])
    rows = np.array(rows)
    out = tmp_path / 'raw.phase'
    written = qp.write_out_raw_phase(rows, out, legacy=True)
    assert written.shape == (3, len(qp.PHASE_COLS_LEGACY))
    loaded = np.loadtxt(out, comments='%')
    assert loaded.shape == (3, len(qp.PHASE_COLS_LEGACY))


def write_synthetic_phase_dir(refl_code, station, year, doy, n_cols):
    """Place a synthetic per-day phase file under REFL_CODE/{year}/phase/{station}/."""
    phase_dir = Path(refl_code) / str(year) / 'phase' / station
    phase_dir.mkdir(parents=True, exist_ok=True)
    fname = phase_dir / f'{doy:03d}.txt'
    rows = []
    for i in range(3):
        row = [year, doy, 6.0 + i * 0.1, 12.5, 100, 120.0 + i * 0.5, 5, 1.5,
               5.0, 25.0, 0.5, 2.0, 20, 2.05, 4.0, 6.0]
        if n_cols == 18:
            row.extend([7041, 0])
        rows.append(row)
    np.savetxt(fname, np.array(rows), fmt='%g')
    return fname


def test_load_phase_filter_default_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv('REFL_CODE', str(tmp_path))
    station = 'tst1'
    write_synthetic_phase_dir(tmp_path, station, 2024, 1, n_cols=18)

    out_dir = tmp_path / 'Files' / station
    out_dir.mkdir(parents=True, exist_ok=True)

    data_exist, *_rest, results = qp.load_phase(
        station, 2024, 2024, 20, snowmask=None, legacy=False,
    )
    assert data_exist
    # results is transposed: shape (n_cols, n_rows)
    assert results.shape[0] == len(qp.PHASE_COLS)
    np.testing.assert_allclose(results[qp.PHASE_COLS.index('TrackID'), :], 7041)
    np.testing.assert_allclose(results[qp.PHASE_COLS.index('TrackEpoch'), :], 0)


def test_load_phase_filter_default_rejects_legacy_file(tmp_path, monkeypatch):
    """A 16-col phase file in the default path must error with a clear message."""
    monkeypatch.setenv('REFL_CODE', str(tmp_path))
    station = 'tst2'
    write_synthetic_phase_dir(tmp_path, station, 2024, 1, n_cols=16)
    out_dir = tmp_path / 'Files' / station
    out_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(SystemExit):
        qp.load_phase(
            station, 2024, 2024, 20, snowmask=None, legacy=False,
        )
