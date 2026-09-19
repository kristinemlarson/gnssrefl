import numpy as np

from gnssrefl.extract_arcs import filter_excluded_satellites
from gnssrefl.gnss_frequencies import (
    BEIDOU_GEO_SATS,
    BEIDOU_IGSO_SATS,
    BEIDOU_NON_MEO_SATS,
    get_sat_list,
)


def _snr_rows(*satellites):
    rows = np.zeros((len(satellites), 11))
    rows[:, 0] = satellites
    return rows


def test_beidou_orbit_classes_and_range():
    assert BEIDOU_NON_MEO_SATS == BEIDOU_GEO_SATS | BEIDOU_IGSO_SATS
    assert BEIDOU_GEO_SATS.isdisjoint(BEIDOU_IGSO_SATS)
    assert 362 in get_sat_list(301)


def test_geo_and_additional_exclusion_behavior():
    snr = _snr_rows(1, 301, 305, 306, 311, 362)
    cases = [
        ({}, [1, 306, 311]),
        ({'include_geo': True, 'exclude_satellites': [1, 305, 306]}, [301, 311, 362]),
        ({'exclude_satellites': [1, 306]}, [311]),
    ]

    for config, expected in cases:
        filtered = filter_excluded_satellites(snr, config)
        assert filtered[:, 0].astype(int).tolist() == expected
