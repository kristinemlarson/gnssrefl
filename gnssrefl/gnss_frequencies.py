"""
Central registry of GNSS frequency and constellation metadata.

All frequency codes, wavelengths, satellite ranges, display labels, and SNR
column mappings are defined here. Other modules should use the accessor
functions rather than maintaining their own hardcoded lists.

This module has NO dependencies on other gnssrefl modules at import time,
so it can be safely imported from anywhere without circular import issues.
"""
import numpy as np


# Speed of light (m/s)
_C = 299792458

def _wl(freq_mhz):
    """Wavelength in meters from frequency in MHz."""
    return _C / (freq_mhz * 1e6)


# ---------------------------------------------------------------------------
# Constellation metadata
# ---------------------------------------------------------------------------

CONSTELLATIONS = {
    'GPS':     {'sat_range': (1, 33),   'offset': 0},
    'GLONASS': {'sat_range': (101, 125), 'offset': 100},
    'Galileo': {'sat_range': (201, 241), 'offset': 200},
    'BeiDou':  {'sat_range': (301, 361), 'offset': 300},
}

# ---------------------------------------------------------------------------
# Frequency registry
# ---------------------------------------------------------------------------
# Key:   integer frequency code used throughout gnssrefl
# Value: (constellation, signal_label, wavelength_m, snr_column)
#
# GLONASS wavelengths are per-satellite; stored as None here.
# Use get_wavelength(f, sat) for GLONASS.

FREQUENCIES = {
    # GPS
    1:   ('GPS',     'L1',  _wl(1575.42),     7),
    2:   ('GPS',     'L2',  _wl(1227.60),     8),
    20:  ('GPS',     'L2C', _wl(1227.60),     8),
    5:   ('GPS',     'L5',  _wl(115*10.23),   9),
    # GLONASS, FDMA so wavelength depends on satellite channel number
    101: ('GLONASS', 'L1',  None,             7),
    102: ('GLONASS', 'L2',  None,             8),
    # Galileo
    201: ('Galileo', 'L1',  _wl(1575.420),    7),
    205: ('Galileo', 'L5',  _wl(1176.450),    9),
    206: ('Galileo', 'L6',  _wl(1278.70),     6),
    207: ('Galileo', 'L7',  _wl(1207.140),   10),
    208: ('Galileo', 'L8',  _wl(1191.795),   11),
    # BeiDou, values defined in RINEX 3
    301: ('BeiDou',  'L1',  _wl(1575.42),     7),
    302: ('BeiDou',  'L2',  _wl(1561.098),    8),   # B1-2
    305: ('BeiDou',  'L5',  _wl(1176.45),     9),   # BDS-3
    306: ('BeiDou',  'L6',  _wl(1268.52),     6),   # B3
    307: ('BeiDou',  'L7',  _wl(1207.14),    10),   # B2b, BDS-2
    308: ('BeiDou',  'L8',  _wl(1191.795),   11),
}

# File-naming suffixes. L2C (20) maps to '_L2' for backwards compatibility
_FILE_SUFFIXES = {
    1: '_L1', 2: '_L2', 20: '_L2', 5: '_L5',
}

# ---------------------------------------------------------------------------
# Accessor functions
# ---------------------------------------------------------------------------

def is_valid_frequency(f):
    """Check whether a frequency code is recognized."""
    return f in FREQUENCIES


def all_frequencies():
    """Return sorted list of all valid frequency codes."""
    return sorted(FREQUENCIES.keys())


def gps_default_frequencies():
    """Default GPS-only frequency list for gnssir_input."""
    return [1, 20, 5]


def all_default_frequencies():
    """All-constellation default frequency list for gnssir_input -allfreq."""
    return [f for f in sorted(FREQUENCIES.keys()) if f != 2]


def get_constellation(f):
    """Return constellation name for a frequency code."""
    entry = FREQUENCIES.get(f)
    if entry is None:
        raise ValueError(f'Unknown frequency code: {f}')
    return entry[0]


def get_signal_label(f):
    """Return signal label like 'L1', 'L2C', 'L5'."""
    entry = FREQUENCIES.get(f)
    if entry is None:
        raise ValueError(f'Unknown frequency code: {f}')
    return entry[1]


def get_label(f):
    """Return display label like 'GPS L2C' for plot titles."""
    entry = FREQUENCIES.get(f)
    if entry is None:
        return ''
    return f'{entry[0]} {entry[1]}'


def get_wavelength(f, sat=None):
    """Return wavelength in meters. For GLONASS, sat number is required."""
    entry = FREQUENCIES.get(f)
    if entry is None:
        raise ValueError(f'Unknown frequency code: {f}')
    if entry[2] is not None:
        return entry[2]
    # GLONASS: per-satellite wavelength
    if sat is None:
        raise ValueError(f'GLONASS frequency {f} requires a satellite number')
    from gnssrefl.gps import glonass_channels
    return glonass_channels(f, sat)


def get_scale_factor(f, sat=None):
    """Return wavelength/2 (the LSP scale factor cf)."""
    return get_wavelength(f, sat) / 2


def get_snr_column(f):
    """Return 1-based SNR file column index for a frequency code."""
    entry = FREQUENCIES.get(f)
    if entry is None:
        raise ValueError(f'Unknown frequency code: {f}')
    return entry[3]


def get_sat_range(f):
    """Return (start, stop) tuple for np.arange to build a satellite list."""
    constellation = get_constellation(f)
    return CONSTELLATIONS[constellation]['sat_range']


def get_sat_list(f):
    """Return numpy array of satellite PRNs for a frequency's constellation."""
    start, stop = get_sat_range(f)
    return np.arange(start, stop)


def get_file_suffix(f):
    """Return file naming suffix like '_L2', '_L1'. Non-GPS uses '_freq{f}'."""
    if f in _FILE_SUFFIXES:
        return _FILE_SUFFIXES[f]
    return f'_freq{f}'
