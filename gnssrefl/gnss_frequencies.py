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
C = 299792458

def wl(freq_mhz):
    """Wavelength in meters from frequency in MHz."""
    return C / (freq_mhz * 1e6)


# GLONASS slot -> FDMA channel mapping.
# Static snapshot; channels actually vary over time (the authoritative value is
# carried per-record in the GLONASS broadcast nav file) and a future fix should
# read them from the nav ephemeris.
#
# Slots 1-24: long-standing mapping from Simon Williams (originally in gps.py, ported in v4.1.3).
# Slots 25-28: current as of early 2026 per IGS satellite metadata
# (files.igs.org/pub/station/general/igs_satellite_metadata.snx).
# Slot 25 is the historical value; outdated as of 2025:145 but previously stood for 18 years.
_GLONASS_SLOT_CHANNEL = {
    1: 1, 2: -4, 3: 5, 4: 6, 5: 1, 6: -4, 7: 5, 8: 6,
    9: -2, 10: -7, 11: 0, 12: -1, 13: -2, 14: -7, 15: 0, 16: -1,
    17: 4, 18: -3, 19: 3, 20: 2, 21: 4, 22: -3, 23: 3, 24: 2,
    25: 3, 26: -6, 27: -5, 28: 7,
}


def get_glonass_channel(prn):
    """Return the FDMA channel number for a GLONASS satellite, or None if unknown."""
    if prn > 100:
        prn = prn - 100
    return _GLONASS_SLOT_CHANNEL.get(int(prn))


def get_glonass_wavelength(f, prn):
    """Return GLONASS wavelength in meters for frequency code f and satellite prn.

    GLONASS uses FDMA so each satellite transmits on a slightly different
    carrier determined by its channel number. f is 101 (G1) or 102 (G2).
    Raises ValueError if the satellite slot has no known channel assignment.
    """
    ch = get_glonass_channel(prn)
    if ch is None:
        raise ValueError(f'No GLONASS channel assignment known for slot {prn % 100}')
    if f == 101:
        return C / (1602e6 + ch * 0.5625e6)
    if f == 102:
        return C / (1246e6 + ch * 0.4375e6)
    return 0.0


# ---------------------------------------------------------------------------
# Constellation metadata
# ---------------------------------------------------------------------------

CONSTELLATIONS = {
    'GPS':     {'sat_range': (1, 33),   'offset': 0},
    'GLONASS': {'sat_range': (101, 129), 'offset': 100},
    'Galileo': {'sat_range': (201, 241), 'offset': 200},
    'BeiDou':  {'sat_range': (301, 361), 'offset': 300},
}

# BeiDou GEO + IGSO satellites (non-MEO), currently excluded.
BEIDOU_NON_MEO_SATS = frozenset({301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 313, 338, 339, 340, 359, 360, 361})

# ---------------------------------------------------------------------------
# Frequency registry
# ---------------------------------------------------------------------------
# Signal labels (L1, L2, L5, L6, L7, L8) follow the RINEX 3 frequency-band
# numbering convention. For each constellation, the physical frequency the
# band number maps to is given in:
#
#   RINEX 3.05 §5.2.17 "Observation codes", Tables 14-20
#   https://files.igs.org/pub/data/format/rinex305.pdf
#
# Code 20 ('L2C') is the modernized GPS civilian signal on the L2 band;
# code 2 is the legacy L2 P-code. Both transmit at 1227.60 MHz.
#
# Key:   integer frequency code used throughout gnssrefl
# Value: (constellation, signal_label, wavelength_m, snr_column)
#
# GLONASS wavelengths are per-satellite (FDMA); stored as None here.
# Use get_wavelength(f, sat) for GLONASS.

FREQUENCIES = {
    # GPS
    1:   ('GPS',     'L1',  wl(1575.42),     7),
    2:   ('GPS',     'L2',  wl(1227.60),     8),
    20:  ('GPS',     'L2C', wl(1227.60),     8),
    5:   ('GPS',     'L5',  wl(115*10.23),   9),
    # GLONASS, FDMA so wavelength depends on satellite channel number
    101: ('GLONASS', 'L1',  None,             7),
    102: ('GLONASS', 'L2',  None,             8),
    # Galileo
    201: ('Galileo', 'L1',  wl(1575.420),    7),
    205: ('Galileo', 'L5',  wl(1176.450),    9),
    206: ('Galileo', 'L6',  wl(1278.70),     6),
    207: ('Galileo', 'L7',  wl(1207.140),   10),
    208: ('Galileo', 'L8',  wl(1191.795),   11),
    # BeiDou, values defined in RINEX 3
    301: ('BeiDou',  'L1',  wl(1575.42),     7),
    302: ('BeiDou',  'L2',  wl(1561.098),    8),   # B1-2
    305: ('BeiDou',  'L5',  wl(1176.45),     9),   # BDS-3
    306: ('BeiDou',  'L6',  wl(1268.52),     6),   # B3
    307: ('BeiDou',  'L7',  wl(1207.14),    10),   # B2b, BDS-2
    308: ('BeiDou',  'L8',  wl(1191.795),   11),
}

# Reverse index: (constellation_char, signal_label) -> frequency code.
# Constellation chars follow RINEX convention: G=GPS, R=GLONASS, E=Galileo, C=BeiDou.
CONSTELLATION_CHARS = {
    'GPS': 'G', 'GLONASS': 'R', 'Galileo': 'E', 'BeiDou': 'C',
}
SIGNAL_TO_FREQ = {
    (CONSTELLATION_CHARS[constellation], label): code
    for code, (constellation, label, _, _) in FREQUENCIES.items()
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


def get_display_label(f):
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
    return get_glonass_wavelength(f, sat)


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
    """Return file naming suffix like '_G_L1', '_E_L7', '_C_L5'.

    Format is '_<constellation_char>_<signal_label>' using the RINEX 3
    constellation chars (G/R/E/C) and band labels (L1/L2/L2C/L5/L6/L7/L8).
    """
    cons, label, _, _ = FREQUENCIES[f]
    return f'_{CONSTELLATION_CHARS[cons]}_{label}'


def signal_label_to_freq(constellation_char, signal_label):
    """Return the frequency code for a RINEX constellation char and signal label.

    Parameters
    ----------
    constellation_char : str
        Single RINEX char: 'G' (GPS), 'R' (GLONASS), 'E' (Galileo), 'C' (BeiDou)
    signal_label : str
        Signal label like 'L1', 'L2', 'L5', 'L6', 'L7', 'L8', 'L2C'

    Returns
    -------
    int
        Frequency code (e.g. 1, 20, 205, 302)

    Raises
    ------
    KeyError
        If the (constellation_char, signal_label) pair is not recognized
    """
    return SIGNAL_TO_FREQ[(constellation_char, signal_label)]


# ---------------------------------------------------------------------------
# Default frequency selections (used by gnssir_input)
# ---------------------------------------------------------------------------

def gps_default_frequencies():
    """Default GPS-only frequency list for gnssir_input."""
    return [1, 20, 5]


def all_default_frequencies():
    """All-constellation default frequency list for gnssir_input -allfreq.

    GPS L2 P-code (code 2) is excluded; we prefer L2C (code 20).
    """
    return [f for f in sorted(FREQUENCIES.keys()) if f != 2]
