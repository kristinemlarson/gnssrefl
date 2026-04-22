"""
Quality-control edits for tracks.json / vwc_tracks.json files.

Available operations:

- ``split_epoch`` / ``merge_epochs``: subdivide one epoch into two at
  a chosen MJD, or combine two adjacent epochs back into one. Use when
  hardware (receiver or satellite) or significant environmental
  changes occur that motivate a new apriori RH on the same geometric
  track.
- ``ignore_range`` / ``unignore_range``: mark (or un-mark) a time
  window within an epoch so its arcs are excluded from fits and stats.
- ``deactivate_epoch``: turn an epoch off without deleting it, so
  downstream tools skip it.
- ``delete_track``: drop a track entirely from this file onward.
- ``save_tracks``: write the JSON back after refitting every active
  epoch and (for vwc_tracks files) recomputing ``apriori_RH`` /
  ``RH_std`` from the arcs. Read with ``tracks.load_tracks_json``.

Edits are applied to an in-memory dict and only become a self-
consistent file after ``save_tracks`` runs the refit + stats pass.
Structurally invalid edits raise ``ValueError``.
"""

import contextlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np

from gnssrefl.extract_arcs import extract_arcs_from_tracks
from gnssrefl.tracks import write_tracks_json, fit_segment, iso_to_mjd, mjd_to_iso_ceil, mjd_to_iso_floor


DEFAULT_APRIORI_RH_NDAYS = 365


# ===========================================================================
# save
# ===========================================================================

def save_tracks(tracks_json, path, tool, note="", arcs_df=None):
    """Append a history entry, refresh every derived field, and write the JSON.

    For ``file_type == 'vwc_tracks'`` JSON, also recomputes each epoch's
    ``apriori_RH`` and ``RH_std`` from arcs in that epoch's trailing
    ``apriori_rh_ndays`` window. Writes atomically (temp file + rename).

    ``arcs_df`` can be passed by callers that already have the walked
    arcs (avoids re-walking the SNR files). If ``None``, arcs are
    loaded via `extract_arcs_from_tracks`.
    """
    validate_epoch_ids(tracks_json)

    metadata = tracks_json.setdefault('metadata', {})
    history = metadata.setdefault('history', [])
    history.append({
        'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'tool': tool,
        'note': note,
    })

    if arcs_df is None:
        arcs_df = extract_arcs_from_tracks(tracks_json)
    recompute_derived_fields(tracks_json, arcs_df)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + '.', suffix='.tmp', dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, 'w') as f:
            write_tracks_json(tracks_json, f)
        os.replace(tmp_name, path)
    except Exception:
        with contextlib.suppress(FileNotFoundError):
            os.remove(tmp_name)
        raise


# ===========================================================================
# Primitives
# ===========================================================================

def split_epoch(tracks_json, track_id, split_mjd):
    """Split one active epoch into two adjacent actives at ``split_mjd``.

    ``split_mjd`` must lie strictly inside the target epoch's window.
    Both halves inherit the original epoch's fit parameters
    (anchor_time, repeat_interval_d, az_avg_minel, az_drift_rate);
    fresh values come from ``save_tracks``' refit pass.
    """
    track = check_track_exists(tracks_json, track_id)
    idx, epoch = find_active_epoch_containing(track, split_mjd)
    start_mjd = iso_to_mjd(epoch['start_time'])
    end_mjd = iso_to_mjd(epoch['end_time'])
    if not (start_mjd < split_mjd < end_mjd):
        raise ValueError(
            f'split_mjd={split_mjd} must lie strictly inside epoch window '
            f'[{start_mjd}, {end_mjd}] of track {track_id}'
        )

    left = dict(epoch)
    right = dict(epoch)
    left['end_time'] = mjd_to_iso_floor(split_mjd)
    right['start_time'] = mjd_to_iso_ceil(split_mjd)
    # ignored_ranges partition by the split
    left_ranges, right_ranges = [], []
    for r_start, r_end in epoch['ignored_ranges']:
        if r_end <= split_mjd:
            left_ranges.append([r_start, r_end])
        elif r_start >= split_mjd:
            right_ranges.append([r_start, r_end])
        else:
            left_ranges.append([r_start, split_mjd])
            right_ranges.append([split_mjd, r_end])
    left['ignored_ranges'] = left_ranges
    right['ignored_ranges'] = right_ranges

    track['epochs'][idx:idx + 1] = [left, right]
    renumber_epoch_ids(track)
    return tracks_json


def ignore_range(tracks_json, track_id, epoch_id, mjd_start, mjd_end):
    """Append ``[mjd_start, mjd_end]`` to the target active epoch's ignored ranges.

    Range must lie inside the epoch window and satisfy
    ``mjd_end > mjd_start``. ``epoch_id`` is scoped to this saved
    tracks_json; see tracks.py module docstring.
    """
    if mjd_end <= mjd_start:
        raise ValueError(
            f'ignore_range requires mjd_end > mjd_start; got [{mjd_start}, {mjd_end}]'
        )
    track = check_track_exists(tracks_json, track_id)
    epoch = require_active_epoch(track, track_id, epoch_id)
    start_mjd = iso_to_mjd(epoch['start_time'])
    end_mjd = iso_to_mjd(epoch['end_time'])
    if mjd_start < start_mjd or mjd_end > end_mjd:
        raise ValueError(
            f'range [{mjd_start}, {mjd_end}] must lie inside epoch window '
            f'[{start_mjd}, {end_mjd}] of track {track_id} epoch {epoch_id}'
        )
    ranges = epoch.setdefault('ignored_ranges', [])
    ranges.append([float(mjd_start), float(mjd_end)])
    return tracks_json


def unignore_range(tracks_json, track_id, epoch_id, mjd_start, mjd_end):
    """Subtract ``[mjd_start, mjd_end]`` from the epoch's ignored ranges.

    Raises if the subtraction leaves every existing range unchanged
    (i.e. no overlap anywhere). ``epoch_id`` is scoped to this saved
    tracks_json; see tracks.py module docstring.
    """
    if mjd_end <= mjd_start:
        raise ValueError(
            f'unignore_range requires mjd_end > mjd_start; got [{mjd_start}, {mjd_end}]'
        )
    track = check_track_exists(tracks_json, track_id)
    epoch = require_active_epoch(track, track_id, epoch_id)
    existing = epoch['ignored_ranges']

    new_ranges = []
    touched = False
    for r_start, r_end in existing:
        if mjd_end <= r_start or mjd_start >= r_end:
            new_ranges.append([r_start, r_end])
            continue
        touched = True
        if mjd_start > r_start:
            new_ranges.append([r_start, mjd_start])
        if mjd_end < r_end:
            new_ranges.append([mjd_end, r_end])
    if not touched:
        raise ValueError(
            f'range [{mjd_start}, {mjd_end}] does not overlap any ignored range '
            f'of track {track_id} epoch {epoch_id}'
        )
    epoch['ignored_ranges'] = new_ranges
    return tracks_json


def deactivate_epoch(tracks_json, track_id, epoch_id):
    """Mark an active epoch inactive. Refit/stats will skip it on save.

    Zeros ``n_arcs`` and ``n_qc_arcs`` so inactive epochs carry the
    invariant "0 arcs live". ``epoch_id`` is scoped to this saved
    tracks_json; see tracks.py module docstring.
    """
    track = check_track_exists(tracks_json, track_id)
    epoch = require_active_epoch(track, track_id, epoch_id)
    epoch['epoch_type'] = 'inactive'
    epoch['n_arcs'] = 0
    epoch['n_qc_arcs'] = 0
    return tracks_json


def delete_track(tracks_json, track_id):
    """Remove a track entirely from tracks_json['tracks'].

    ``track_id`` is the geometric identity and is stable across saves
    (see tracks.py module docstring); deleting it means that id is gone
    from this snapshot onward.
    """
    check_track_exists(tracks_json, track_id)
    del tracks_json['tracks'][str(int(track_id))]
    return tracks_json


def merge_epochs(tracks_json, track_id, epoch_id_a, epoch_id_b):
    """Merge two adjacent active epochs with matching constellation / match_T.

    Window becomes the union; ``ignored_ranges`` are concatenated.
    ``anchor_time`` / ``repeat_interval_d`` inherit from the earlier
    epoch and are refit on save. Renumbers all epochs after the merged
    pair (epoch_id is scoped to this saved tracks_json; see tracks.py
    module docstring).
    """
    track = check_track_exists(tracks_json, track_id)
    a, b = sorted((int(epoch_id_a), int(epoch_id_b)))
    if b != a + 1:
        raise ValueError(
            f'merge_epochs: epochs {epoch_id_a} and {epoch_id_b} are not '
            f'adjacent in track {track_id}'
        )
    epochs = track['epochs']
    i, j = a, b
    if i < 0 or j >= len(epochs):
        raise ValueError(
            f'merge_epochs: epoch ids out of range for track {track_id}'
        )
    ea, eb = epochs[i], epochs[j]
    if ea['epoch_type'] != 'active' or eb['epoch_type'] != 'active':
        raise ValueError(
            f'merge_epochs: both epochs must be active (got '
            f'{ea["epoch_type"]!r} and {eb["epoch_type"]!r})'
        )
    # Constellation is track-level; no divergence possible, but match_T
    # is the target of the adjacency constraint (same repeat-period model).
    if round(float(ea['repeat_interval_d']), 6) != round(float(eb['repeat_interval_d']), 6):
        raise ValueError(
            f'merge_epochs: repeat_interval_d mismatch between epochs '
            f'{epoch_id_a} and {epoch_id_b} of track {track_id}'
        )

    merged = dict(ea)
    merged['start_time'] = ea['start_time']
    merged['end_time'] = eb['end_time']
    merged['ignored_ranges'] = list(ea['ignored_ranges']) + list(eb['ignored_ranges'])
    epochs[i:j + 1] = [merged]
    renumber_epoch_ids(track)
    return tracks_json


# ===========================================================================
# Internal helpers
# ===========================================================================

def check_track_exists(tracks_json, track_id):
    tid_str = str(int(track_id))
    tracks = tracks_json.get('tracks', {})
    if tid_str not in tracks:
        raise ValueError(f'track_id {track_id} not found in document')
    return tracks[tid_str]


def validate_epoch_ids(tracks_json):
    """Enforce that each track's epoch ids are exactly 0..N-1 in order.

    Raises ValueError on the first violation.
    """
    for tid_str, track in tracks_json.get('tracks', {}).items():
        ids = [ep['epoch_id'] for ep in track['epochs']]
        if ids != list(range(len(ids))):
            raise ValueError(
                f'track {tid_str}: epoch ids {ids} are not 0..N-1 '
                f'(epoch deletion is forbidden; use deactivate_epoch)'
            )


def require_active_epoch(track, track_id, epoch_id):
    epochs = track['epochs']
    idx = int(epoch_id)
    if idx < 0 or idx >= len(epochs):
        raise ValueError(
            f'epoch id {epoch_id} out of range for track {track_id} '
            f'(len={len(epochs)})'
        )
    epoch = epochs[idx]
    if epoch['epoch_type'] != 'active':
        raise ValueError(
            f'track {track_id} epoch {epoch_id} is not active '
            f'(epoch_type={epoch["epoch_type"]!r})'
        )
    return epoch


def find_active_epoch_containing(track, mjd):
    for i, ep in enumerate(track['epochs']):
        if ep['epoch_type'] != 'active':
            continue
        s = iso_to_mjd(ep['start_time'])
        e = iso_to_mjd(ep['end_time'])
        if s <= mjd <= e:
            return i, ep
    raise ValueError(f'no active epoch covers mjd={mjd}')


def renumber_epoch_ids(track):
    for new_id, ep in enumerate(track['epochs']):
        ep['epoch_id'] = new_id


EPOCH_KEY_ORDER = [
    'epoch_id', 'epoch_type',
    'start_time', 'end_time', 'anchor_time',
    'ignored_ranges',
    'duration_d', 'repeat_interval_d',
    'n_arcs', 'n_qc_arcs',
    'az_avg_minel', 'az_drift_rate',
    'apriori_RH', 'RH_std',
]


def reorder_epoch_keys(epoch):
    """Rewrite ``epoch`` in place with keys in canonical order."""
    ordered = {k: epoch[k] for k in EPOCH_KEY_ORDER if k in epoch}
    for k, v in epoch.items():
        if k not in ordered:
            ordered[k] = v
    epoch.clear()
    epoch.update(ordered)


def recompute_derived_fields(tracks_json, arcs_df):
    """Refit active epochs and refresh every derived per-epoch field.

    For ``file_type == 'vwc_tracks'`` JSON, also recomputes each epoch's
    ``apriori_RH`` / ``RH_std`` / ``n_qc_arcs``. The order matters:
    ``recompute_n_arcs`` and ``compute_tracks_stats`` share the same
    ignored-range mask logic and must agree on every epoch.
    """
    refit_active_epochs(tracks_json, arcs_df)
    recompute_durations(tracks_json)
    recompute_n_arcs(tracks_json, arcs_df)
    metadata = tracks_json['metadata']
    if metadata.get('file_type', 'tracks') == 'vwc_tracks':
        ndays = int(metadata.get('apriori_rh_ndays', DEFAULT_APRIORI_RH_NDAYS))
        compute_tracks_stats(tracks_json, arcs_df, ndays)
    recompute_metadata_aggregates(tracks_json, arcs_df)
    for track in tracks_json.get('tracks', {}).values():
        for ep in track['epochs']:
            reorder_epoch_keys(ep)


def recompute_metadata_aggregates(tracks_json, arcs_df):
    """Refresh top-level metadata totals and the data time range.

    Writes ``n_tracks``, ``n_epochs``, ``n_arcs`` (and ``n_qc_arcs`` for
    vwc_tracks) and ``start_time`` / ``end_time`` / ``duration_d`` on
    ``metadata``. Rebuilds metadata key order so the totals sit together.
    Removes the legacy nested ``time_range`` field.
    """
    metadata = tracks_json.setdefault('metadata', {})
    metadata.pop('time_range', None)

    tracks = tracks_json.get('tracks', {})
    is_vwc = metadata.get('file_type', 'tracks') == 'vwc_tracks'

    n_tracks = len(tracks)
    n_epochs = sum(len(t['epochs']) for t in tracks.values())
    n_arcs = sum(int(ep['n_arcs']) for t in tracks.values() for ep in t['epochs'])
    n_qc_arcs = (
        sum(int(ep.get('n_qc_arcs', 0))
            for t in tracks.values() for ep in t['epochs'])
        if is_vwc else None
    )

    if not arcs_df.empty:
        mjd_min = float(arcs_df['mjd'].min())
        mjd_max = float(arcs_df['mjd'].max())
        metadata['start_time'] = mjd_to_iso_floor(mjd_min)
        metadata['end_time'] = mjd_to_iso_ceil(mjd_max)
        metadata['duration_d'] = int(round(mjd_max - mjd_min))

    # Canonical key order: identity, time range, totals, then everything else.
    leading = ['file_type', 'station', 'extension',
               'start_time', 'end_time', 'duration_d',
               'n_tracks', 'n_epochs', 'n_arcs']
    if is_vwc:
        leading.append('n_qc_arcs')

    metadata['n_tracks'] = n_tracks
    metadata['n_epochs'] = n_epochs
    metadata['n_arcs'] = n_arcs
    if is_vwc:
        metadata['n_qc_arcs'] = n_qc_arcs

    ordered = {k: metadata[k] for k in leading if k in metadata}
    for k, v in metadata.items():
        if k not in ordered:
            ordered[k] = v
    metadata.clear()
    metadata.update(ordered)


def refit_active_epochs(tracks_json, arcs_df):
    """For each active epoch, refit anchor_time / repeat_interval_d via fit_segment."""
    if arcs_df.empty:
        return
    grouped = dict(tuple(arcs_df.groupby(['track_id', 'track_epoch'])))
    for tid_str, track in tracks_json['tracks'].items():
        tid = int(tid_str)
        for ep in track['epochs']:
            if ep['epoch_type'] != 'active':
                continue
            track_epoch = int(ep['epoch_id'])
            key = (tid, track_epoch)
            sub = grouped.get(key)
            if sub is None or len(sub) == 0:
                continue
            # Drop arcs in ignored_ranges.
            ranges = ep['ignored_ranges']
            if ranges:
                keep = np.ones(len(sub), dtype=bool)
                for r_start, r_end in ranges:
                    keep &= ~((sub.mjd.values >= r_start) & (sub.mjd.values <= r_end))
                sub = sub[keep]
            if len(sub) == 0:
                continue
            T_fit, anchor_mjd, az_avg_minel, az_drift_rate = fit_segment(sub)
            ep['anchor_time'] = mjd_to_iso_floor(anchor_mjd)
            ep['repeat_interval_d'] = round(T_fit, 6)
            ep['az_avg_minel'] = round(az_avg_minel, 3)
            if az_drift_rate != 0.0:
                ep['az_drift_rate'] = round(az_drift_rate, 7)


def recompute_durations(tracks_json):
    """Refresh ``duration_d`` for every epoch from current start/end times."""
    for track in tracks_json.get('tracks', {}).values():
        for ep in track['epochs']:
            ep['duration_d'] = round(
                iso_to_mjd(ep['end_time']) - iso_to_mjd(ep['start_time']), 2
            )


def recompute_n_arcs(tracks_json, arcs_df):
    """Set ``n_arcs`` on every active epoch from arcs_df.

    Counts arcs whose ``(track_id, track_epoch)`` matches the epoch and
    whose ``mjd`` is outside any ``ignored_ranges``. Writes ``0`` when no
    arcs match. Mirrors the ignored-range mask in `refit_active_epochs`
    so the values agree on active epochs. Inactive epochs are skipped;
    their ``n_arcs`` is zeroed at deactivation time.
    """
    if arcs_df.empty:
        for track in tracks_json.get('tracks', {}).values():
            for ep in track['epochs']:
                if ep['epoch_type'] != 'active':
                    continue
                ep['n_arcs'] = 0
        return
    grouped = dict(tuple(arcs_df.groupby(['track_id', 'track_epoch'])))
    for tid_str, track in tracks_json['tracks'].items():
        tid = int(tid_str)
        for ep in track['epochs']:
            if ep['epoch_type'] != 'active':
                continue
            sub = grouped.get((tid, int(ep['epoch_id'])))
            if sub is None or len(sub) == 0:
                ep['n_arcs'] = 0
                continue
            ranges = ep['ignored_ranges']
            if ranges:
                keep = np.ones(len(sub), dtype=bool)
                for r_start, r_end in ranges:
                    keep &= ~((sub.mjd.values >= r_start) & (sub.mjd.values <= r_end))
                sub = sub[keep]
            ep['n_arcs'] = int(len(sub))


def compute_tracks_stats(tracks_json, arcs_df, apriori_rh_ndays):
    """Compute ``n_qc_arcs`` and apriori_RH/RH_std on active epochs.

    Inactive epochs are skipped; their ``n_qc_arcs`` is zeroed at
    deactivation time.
    """
    if arcs_df.empty:
        for track in tracks_json.get('tracks', {}).values():
            for ep in track['epochs']:
                if ep['epoch_type'] != 'active':
                    continue
                ep['n_qc_arcs'] = 0
        return
    grouped = dict(tuple(arcs_df.groupby(['track_id', 'track_epoch'])))
    for tid_str, track in tracks_json['tracks'].items():
        tid = int(tid_str)
        for ep in track['epochs']:
            if ep['epoch_type'] != 'active':
                continue
            track_epoch = int(ep['epoch_id'])
            sub = grouped.get((tid, track_epoch))
            if sub is None or len(sub) == 0:
                ep['n_qc_arcs'] = 0
                ep['apriori_RH'] = None
                ep['RH_std'] = None
                continue
            ranges = ep['ignored_ranges']
            if ranges:
                keep = np.ones(len(sub), dtype=bool)
                for r_start, r_end in ranges:
                    keep &= ~((sub.mjd.values >= r_start) & (sub.mjd.values <= r_end))
                sub = sub[keep]
            ep['n_qc_arcs'] = int(sub['RH'].notna().sum()) if len(sub) else 0
            if len(sub) == 0:
                ep['apriori_RH'] = None
                ep['RH_std'] = None
                continue
            end_mjd = iso_to_mjd(ep['end_time'])
            rh_cutoff = end_mjd - apriori_rh_ndays
            in_window = sub[sub.mjd.values > rh_cutoff]
            rh_vals = in_window.RH.dropna().values
            n = len(rh_vals)
            if n == 0:
                ep['apriori_RH'] = None
                ep['RH_std'] = None
                continue
            rh_sum = float(rh_vals.sum())
            rh_sum_sq = float((rh_vals * rh_vals).sum())
            mean = rh_sum / n
            ep['apriori_RH'] = round(mean, 4)
            if n >= 3:
                var = max(rh_sum_sq / n - mean * mean, 0.0)
                ep['RH_std'] = round(var ** 0.5, 4)
            else:
                ep['RH_std'] = None
