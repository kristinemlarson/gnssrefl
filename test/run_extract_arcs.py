#!/usr/bin/env python3
"""Run extract_arcs regression tests, writing arc output to REFL_CODE."""
import os, sys

STATION, YEAR, DOY = 'mchl', 2025, 11
# GPS + GLONASS + Galileo (all constellations present in mchl SNR data)
MULTI_FREQS = [1, 20, 5, 101, 102, 201, 205, 206, 207, 208]
COMMON_KWARGS = dict(
    e1=5.0, e2=25.0, polyV=4, pele=[5, 30],
    azlist=[0, 360], year=YEAR, doy=DOY,
)


def _snr_path():
    """Return .gz path to day-11 SNR file (np.loadtxt handles .gz natively)."""
    return os.path.join(
        os.environ['REFL_CODE'], '2025/snr/mchl/mchl0110.25.snr66.gz',
    )


def run_extract_arcs_direct():
    from gnssrefl.read_snr_files import read_snr
    from gnssrefl.extract_arcs import extract_arcs, setup_arcs_directory, save_arc

    _, snr_array, _, _ = read_snr(_snr_path(), buffer_hours=0)
    arcs = extract_arcs(snr_array, freq=MULTI_FREQS, **COMMON_KWARGS)
    sdir = setup_arcs_directory(STATION, YEAR, DOY)
    for meta, data in arcs:
        save_arc(meta, data, sdir, STATION, YEAR, DOY)


def run_extract_arcs_from_file():
    from gnssrefl.extract_arcs import extract_arcs_from_file, setup_arcs_directory, save_arc

    arcs = extract_arcs_from_file(
        _snr_path(), freq=MULTI_FREQS, buffer_hours=0, **COMMON_KWARGS,
    )
    sdir = setup_arcs_directory(STATION, YEAR, DOY)
    for meta, data in arcs:
        save_arc(meta, data, sdir, STATION, YEAR, DOY)


def run_extract_arcs_from_station():
    from gnssrefl.gnssir_v2 import read_json_file
    from gnssrefl.extract_arcs import extract_arcs_from_station

    station_config = read_json_file(STATION, '')
    station_config['savearcs'] = True
    station_config['savearcs_format'] = 'txt'
    station_config['nooverwrite'] = False
    extract_arcs_from_station(
        STATION, YEAR, DOY,
        freq=station_config['freqs'], snr_type=66, buffer_hours=2,
        e1=station_config['e1'], e2=station_config['e2'], polyV=station_config['polyV'],
        pele=station_config['pele'], azlist=station_config['azval2'], station_config=station_config,
    )


TESTS = {
    'test_extract_arcs_output_unchanged': run_extract_arcs_direct,
    'test_extract_arcs_from_file_output_unchanged': run_extract_arcs_from_file,
    'test_extract_arcs_from_station_output_unchanged': run_extract_arcs_from_station,
}

if __name__ == '__main__':
    TESTS[sys.argv[1]]()
