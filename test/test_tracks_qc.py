"""Unit tests for gnssrefl.tracks_qc primitives and save orchestration."""

import pandas as pd
import pytest

from gnssrefl import tracks_qc as qc
from gnssrefl.tracks import iso_to_mjd, mjd_to_iso_ceil, mjd_to_iso_floor


def _make_epoch(eid, start_mjd, end_mjd, anchor_mjd=None, T=0.997, az=120.0):
    if anchor_mjd is None:
        anchor_mjd = start_mjd
    return {
        'epoch_id': eid,
        'epoch_type': 'active',
        'start_time': mjd_to_iso_floor(start_mjd),
        'end_time': mjd_to_iso_ceil(end_mjd),
        'anchor_time': mjd_to_iso_floor(anchor_mjd),
        'duration_d': round(end_mjd - start_mjd, 2),
        'n_arcs': 100,
        'repeat_interval_d': T,
        'az_avg_minel': az,
        'ignored_ranges': [],
    }


def _make_doc(file_type='tracks'):
    return {
        'metadata': {
            'file_type': file_type,
            'station': 'test',
            'extension': '',
            'generated_at': '2026-04-18T00:00:00Z',
            'history': [
                {'timestamp': '2026-04-18T00:00:00Z', 'tool': 'build_tracks', 'note': ''},
            ],
        },
        'tracks': {
            '7041': {
                'constellation': 'GPS',
                'sat': 5,
                'freq': 20,
                'rise': 1,
                'epochs': [
                    _make_epoch(0, 60000.0, 60100.0),
                    _make_epoch(1, 60200.0, 60300.0),
                ],
            },
        },
    }


def _arcs_df(rows=()):
    """Canonical 7-col arcs frame save_tracks expects.
    ``rows`` = iterable of (mjd, RH, epoch); RH may be NaN."""
    return pd.DataFrame([
        {'mjd': m, 'azim': 120.0, 'constellation': 'GPS',
         'RH': rh, 'match_T': float('nan'),
         'track_id': 7041, 'track_epoch': ep}
        for m, rh, ep in rows
    ], columns=['mjd', 'azim', 'constellation', 'RH', 'match_T',
                'track_id', 'track_epoch'])


# ---------------------------------------------------------------------------
# split_epoch
# ---------------------------------------------------------------------------

def test_split_epoch_happy():
    tracks_json = _make_doc()
    qc.split_epoch(tracks_json, track_id=7041, split_mjd=60050.0)
    epochs = tracks_json['tracks']['7041']['epochs']
    assert len(epochs) == 3
    assert [ep['epoch_id'] for ep in epochs] == [0, 1, 2]
    assert iso_to_mjd(epochs[0]['end_time']) <= 60050.0
    assert iso_to_mjd(epochs[1]['start_time']) >= 60050.0
    assert iso_to_mjd(epochs[1]['end_time']) >= 60100.0 - 1
    # parameter inheritance
    assert epochs[0]['repeat_interval_d'] == epochs[1]['repeat_interval_d']
    assert epochs[0]['az_avg_minel'] == epochs[1]['az_avg_minel']


def test_split_epoch_outside_window_raises():
    tracks_json = _make_doc()
    with pytest.raises(ValueError):
        qc.split_epoch(tracks_json, track_id=7041, split_mjd=60150.0)


def test_split_epoch_on_inactive_raises():
    tracks_json = _make_doc()
    tracks_json['tracks']['7041']['epochs'][0]['epoch_type'] = 'inactive'
    with pytest.raises(ValueError):
        qc.split_epoch(tracks_json, track_id=7041, split_mjd=60050.0)


# ---------------------------------------------------------------------------
# ignore_range
# ---------------------------------------------------------------------------

def test_ignore_range_happy():
    tracks_json = _make_doc()
    qc.ignore_range(tracks_json, track_id=7041, epoch_id=0,
                    mjd_start=60010.0, mjd_end=60020.0)
    ranges = tracks_json['tracks']['7041']['epochs'][0]['ignored_ranges']
    assert ranges == [[60010.0, 60020.0]]


def test_ignore_range_inactive_epoch_raises():
    tracks_json = _make_doc()
    tracks_json['tracks']['7041']['epochs'][0]['epoch_type'] = 'inactive'
    with pytest.raises(ValueError):
        qc.ignore_range(tracks_json, track_id=7041, epoch_id=0,
                        mjd_start=60010.0, mjd_end=60020.0)


def test_ignore_range_outside_window_raises():
    tracks_json = _make_doc()
    with pytest.raises(ValueError):
        qc.ignore_range(tracks_json, track_id=7041, epoch_id=0,
                        mjd_start=60090.0, mjd_end=60150.0)


def test_ignore_range_invalid_interval_raises():
    tracks_json = _make_doc()
    with pytest.raises(ValueError):
        qc.ignore_range(tracks_json, track_id=7041, epoch_id=0,
                        mjd_start=60020.0, mjd_end=60010.0)


# ---------------------------------------------------------------------------
# unignore_range
# ---------------------------------------------------------------------------

def test_unignore_range_full_match_removes():
    tracks_json = _make_doc()
    qc.ignore_range(tracks_json, 7041, 0, 60010.0, 60020.0)
    qc.unignore_range(tracks_json, 7041, 0, 60010.0, 60020.0)
    assert tracks_json['tracks']['7041']['epochs'][0]['ignored_ranges'] == []


def test_unignore_range_subrange_splits():
    tracks_json = _make_doc()
    qc.ignore_range(tracks_json, 7041, 0, 60010.0, 60030.0)
    qc.unignore_range(tracks_json, 7041, 0, 60015.0, 60020.0)
    assert tracks_json['tracks']['7041']['epochs'][0]['ignored_ranges'] == [
        [60010.0, 60015.0],
        [60020.0, 60030.0],
    ]


def test_unignore_range_no_overlap_raises():
    tracks_json = _make_doc()
    qc.ignore_range(tracks_json, 7041, 0, 60010.0, 60020.0)
    with pytest.raises(ValueError):
        qc.unignore_range(tracks_json, 7041, 0, 60050.0, 60060.0)


# ---------------------------------------------------------------------------
# deactivate_epoch
# ---------------------------------------------------------------------------

def test_deactivate_epoch_happy():
    tracks_json = _make_doc()
    qc.deactivate_epoch(tracks_json, track_id=7041, epoch_id=0)
    assert tracks_json['tracks']['7041']['epochs'][0]['epoch_type'] == 'inactive'


def test_deactivate_already_inactive_raises():
    tracks_json = _make_doc()
    tracks_json['tracks']['7041']['epochs'][0]['epoch_type'] = 'inactive'
    with pytest.raises(ValueError):
        qc.deactivate_epoch(tracks_json, track_id=7041, epoch_id=0)


# ---------------------------------------------------------------------------
# merge_epochs
# ---------------------------------------------------------------------------

def test_merge_epochs_happy():
    tracks_json = _make_doc()
    orig_start = tracks_json['tracks']['7041']['epochs'][0]['start_time']
    orig_end = tracks_json['tracks']['7041']['epochs'][1]['end_time']
    qc.merge_epochs(tracks_json, track_id=7041, epoch_id_a=0, epoch_id_b=1)
    epochs = tracks_json['tracks']['7041']['epochs']
    assert len(epochs) == 1
    assert epochs[0]['start_time'] == orig_start
    assert epochs[0]['end_time'] == orig_end
    assert epochs[0]['epoch_id'] == 0


def test_merge_nonadjacent_raises():
    tracks_json = _make_doc()
    qc.split_epoch(tracks_json, track_id=7041, split_mjd=60050.0)
    # now epochs = [0, 1, 2]; try merging 0 and 2
    with pytest.raises(ValueError):
        qc.merge_epochs(tracks_json, track_id=7041, epoch_id_a=0, epoch_id_b=2)


def test_merge_mismatched_repeat_raises():
    tracks_json = _make_doc()
    tracks_json['tracks']['7041']['epochs'][1]['repeat_interval_d'] = 7.97
    with pytest.raises(ValueError):
        qc.merge_epochs(tracks_json, track_id=7041, epoch_id_a=0, epoch_id_b=1)


# ---------------------------------------------------------------------------
# save_tracks — history + orchestration
# ---------------------------------------------------------------------------

def test_history_appended_on_save(tmp_path):
    tracks_json = _make_doc()
    out_path = tmp_path / 'tracks.json'
    arcs_df = _arcs_df([
        (60010.0, 2.0, 0), (60080.0, 2.1, 0),
        (60210.0, 2.2, 1), (60280.0, 2.3, 1),
    ])

    qc.save_tracks(tracks_json, out_path, tool='test_tool', note='hello',
                   arcs_df=arcs_df)
    history = tracks_json['metadata']['history']
    assert len(history) == 2
    assert history[-1]['tool'] == 'test_tool'
    assert history[-1]['note'] == 'hello'
    assert out_path.exists()


def test_save_recomputes_vwc_stats(tmp_path):
    tracks_json = _make_doc(file_type='vwc_tracks')
    tracks_json['metadata']['apriori_rh_ndays'] = 365
    out_path = tmp_path / 'vwc_tracks.json'
    arcs_df = _arcs_df([
        (60010.0, 2.0, 0), (60050.0, 2.2, 0), (60090.0, 2.4, 0),
    ])

    qc.save_tracks(tracks_json, out_path, tool='test', note='', arcs_df=arcs_df)
    ep0 = tracks_json['tracks']['7041']['epochs'][0]
    assert ep0['apriori_RH'] is not None
    assert ep0['apriori_RH'] == pytest.approx(2.2, abs=1e-3)
    assert ep0['RH_std'] is not None
    assert ep0['n_qc_arcs'] == 3
    # epoch 1 has no arcs in the input frame
    ep1 = tracks_json['tracks']['7041']['epochs'][1]
    assert ep1['apriori_RH'] is None
    assert ep1['RH_std'] is None
    assert ep1['n_qc_arcs'] == 0
    assert ep1['n_arcs'] == 0


def test_save_honors_ignored_ranges(tmp_path):
    tracks_json = _make_doc(file_type='vwc_tracks')
    qc.ignore_range(tracks_json, 7041, 0, 60040.0, 60060.0)
    out_path = tmp_path / 'vwc_tracks.json'
    arcs_df = _arcs_df([
        (60010.0, 2.0, 0),
        (60050.0, 99.0, 0),   # in ignored range
        (60090.0, 2.4, 0),
    ])

    qc.save_tracks(tracks_json, out_path, tool='test', note='', arcs_df=arcs_df)
    ep0 = tracks_json['tracks']['7041']['epochs'][0]
    # mean should be 2.2 (99.0 filtered out by ignored_ranges)
    assert ep0['apriori_RH'] == pytest.approx(2.2, abs=1e-3)
    assert ep0['n_qc_arcs'] == 2
    assert ep0['n_arcs'] == 2


# ---------------------------------------------------------------------------
# delete_track
# ---------------------------------------------------------------------------

def test_delete_track_happy():
    tracks_json = _make_doc()
    qc.delete_track(tracks_json, track_id=7041)
    assert '7041' not in tracks_json['tracks']


def test_delete_track_missing_raises():
    tracks_json = _make_doc()
    with pytest.raises(ValueError):
        qc.delete_track(tracks_json, track_id=9999)


# ---------------------------------------------------------------------------
# validate_epoch_ids
# ---------------------------------------------------------------------------

def test_validate_epoch_ids_detects_deletion(tmp_path):
    tracks_json = _make_doc()
    # Simulate a buggy contributor deleting an epoch.
    del tracks_json['tracks']['7041']['epochs'][0]
    with pytest.raises(ValueError, match='epoch ids'):
        qc.validate_epoch_ids(tracks_json)
    # And the check fires from save_tracks too.
    with pytest.raises(ValueError, match='epoch ids'):
        qc.save_tracks(tracks_json, tmp_path / 'out.json', tool='t',
                       arcs_df=_arcs_df())


def test_save_recomputes_n_arcs_after_split(tmp_path):
    tracks_json = _make_doc()
    qc.split_epoch(tracks_json, track_id=7041, split_mjd=60050.0)
    arcs_df = _arcs_df([
        # 2 arcs in left half (epoch 0)
        (60010.0, 2.0, 0), (60030.0, 2.1, 0),
        # 3 arcs in right half (epoch 1)
        (60060.0, 2.2, 1), (60080.0, 2.3, 1), (60095.0, 2.4, 1),
    ])
    qc.save_tracks(tracks_json, tmp_path / 'out.json', tool='t', arcs_df=arcs_df)
    epochs = tracks_json['tracks']['7041']['epochs']
    # Both split halves should have correct n_arcs (not the parent's stale 100).
    assert epochs[0]['n_arcs'] == 2
    assert epochs[1]['n_arcs'] == 3


def test_deactivate_epoch_zeros_arc_counts():
    tracks_json = _make_doc()
    epochs = tracks_json['tracks']['7041']['epochs']
    epochs[0]['n_arcs'] = 50
    epochs[0]['n_qc_arcs'] = 30
    qc.deactivate_epoch(tracks_json, track_id=7041, epoch_id=0)
    assert epochs[0]['n_arcs'] == 0
    assert epochs[0]['n_qc_arcs'] == 0


def test_save_preserves_inactive_n_arcs(tmp_path):
    tracks_json = _make_doc()
    epochs = tracks_json['tracks']['7041']['epochs']
    epochs[1]['epoch_type'] = 'inactive'
    epochs[1]['n_arcs'] = 0
    epochs[1]['n_qc_arcs'] = 0
    arcs_df = _arcs_df([(60010.0, 2.0, 0), (60080.0, 2.1, 0)])
    qc.save_tracks(tracks_json, tmp_path / 'out.json', tool='t', arcs_df=arcs_df)
    assert epochs[1]['n_arcs'] == 0
    assert epochs[1]['n_qc_arcs'] == 0
