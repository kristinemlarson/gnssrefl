"""Golden file regression tests for gnssir, phase, and arc output.

These tests run gnssir and phase against committed fixture data and compare
output to known-good baselines in test/data/expected/. Any unintended change
to numeric output will cause a failure.

To regenerate golden files after an INTENTIONAL change, see
test/regenerate_golden_files.md.
"""
from pathlib import Path

import numpy as np
import pytest

EXPECTED_DIR = Path(__file__).parent / "data" / "expected"


def _compare_output(actual_path, expected_path):
    """Compare actual vs expected output files, fail with a summary if different."""
    actual = np.loadtxt(actual_path, comments="%")
    expected = np.loadtxt(expected_path, comments="%")
    if actual.shape[0] != expected.shape[0]:
        pytest.fail(f"Row count changed: expected {expected.shape[0]}, got {actual.shape[0]}")
    mask = ~np.isclose(actual, expected, rtol=1e-6).all(axis=1)
    n = mask.sum()
    if n > 0:
        pytest.fail(f"{n} of {len(expected)} rows differ")


def test_gnssir_output_unchanged(refl_code_with_mchl):
    from gnssrefl.gnssir_cl import gnssir

    tmp = refl_code_with_mchl
    gnssir("mchl", 2025, 11, screenstats=False, plt=False)

    _compare_output(
        tmp / "2025" / "results" / "mchl" / "011.txt",
        EXPECTED_DIR / "gnssir" / "2025" / "011.txt",
    )


def test_gnssir_midnite_output_unchanged(refl_code_with_mchl):
    from gnssrefl.gnssir_cl import gnssir

    tmp = refl_code_with_mchl
    gnssir("mchl", 2025, 11, midnite=True, screenstats=False, plt=False)

    _compare_output(
        tmp / "2025" / "results" / "mchl" / "011.txt",
        EXPECTED_DIR / "gnssir_midnite" / "2025" / "011.txt",
    )


def test_phase_output_unchanged(refl_code_with_mchl):
    from gnssrefl.gnssir_cl import gnssir
    from gnssrefl.quickPhase import quickphase

    tmp = refl_code_with_mchl
    # phase needs gnssir results first
    gnssir("mchl", 2025, 11, screenstats=False, plt=False)
    quickphase("mchl", 2025, 11, screenstats=False, plt=False)

    _compare_output(
        tmp / "2025" / "phase" / "mchl" / "011.txt",
        EXPECTED_DIR / "phase" / "2025" / "011.txt",
    )


def _compare_arcs(actual_dir, expected_dir):
    """Compare arc files between actual and expected directories."""
    actual_files = {f.name for f in actual_dir.glob("*.txt")}
    expected_files = {f.name for f in expected_dir.glob("*.txt")}

    missing = sorted(expected_files - actual_files)
    new = sorted(actual_files - expected_files)
    common = sorted(actual_files & expected_files)

    changed = []
    for name in common:
        act = np.loadtxt(actual_dir / name, comments="%")
        exp = np.loadtxt(expected_dir / name, comments="%")
        if act.shape != exp.shape or not np.allclose(act, exp, rtol=1e-6):
            col_names = ["elev", "dSNR", "sec"]
            bad_cols = []
            if act.shape == exp.shape:
                for ci, cn in enumerate(col_names):
                    if not np.allclose(act[:, ci], exp[:, ci], rtol=1e-6):
                        bad_cols.append(cn)
            else:
                bad_cols.append(f"shape {exp.shape}->{act.shape}")
            changed.append((name, bad_cols))

    n_diffs = len(missing) + len(new) + len(changed)
    if n_diffs == 0:
        return

    lines = [f"Arc output changed -- {n_diffs} arc difference{'s' if n_diffs != 1 else ''}:"]

    if missing:
        lines.append("")
        lines.append("MISSING arcs (expected but not produced):")
        for name in missing:
            lines.append(f"  {name}")

    if new:
        lines.append("")
        lines.append("NEW arcs (produced but not expected):")
        for name in new:
            lines.append(f"  {name}")

    if changed:
        lines.append("")
        lines.append("CHANGED arcs:")
        for name, bad_cols in changed:
            lines.append(f"  {name}  diverged in: {', '.join(bad_cols)}")

    pytest.fail("\n".join(lines))


def test_gnssir_arcs_unchanged(refl_code_with_mchl):
    from gnssrefl.gnssir_cl import gnssir

    tmp = refl_code_with_mchl
    gnssir("mchl", 2025, 11, savearcs=True, screenstats=False, plt=False)

    _compare_arcs(
        tmp / "2025" / "arcs" / "mchl" / "011",
        EXPECTED_DIR / "arcs" / "2025" / "011",
    )


def test_gnssir_midnite_arcs_unchanged(refl_code_with_mchl):
    from gnssrefl.gnssir_cl import gnssir

    tmp = refl_code_with_mchl
    gnssir("mchl", 2025, 11, midnite=True, savearcs=True, screenstats=False, plt=False)

    _compare_arcs(
        tmp / "2025" / "arcs" / "mchl" / "011",
        EXPECTED_DIR / "arcs_midnite" / "2025" / "011",
    )
