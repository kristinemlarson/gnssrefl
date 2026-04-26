"""
tracks_cl.py: CLI wrapper for the multi-GNSS tracks.json builder.

Thin argparse wrapper around gnssrefl.tracks.build_tracks. Walks SNR
files for the requested station and year window, folds arcs into multi-GNSS
ground-truth tracks, and writes the result to
``REFL_CODE/Files/{station}/{extension}/tracks.json``.

Examples
--------
generate_tracks mchl 2023 -year_end 2025
    build mchl tracks for 2023-2025

generate_tracks mchl 2024 -extension m1
    build mchl/m1 tracks (always overwrites any existing tracks.json)

generate_tracks mchl 2024 -source snr
    force SNR walk even when results/+failQC/ are available
"""

import argparse
import sys

import gnssrefl.gps as g
from gnssrefl.tracks import build_tracks


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="4-char station name", type=str)
    parser.add_argument("year", help="start year", type=int)
    parser.add_argument("-year_end", default=None, type=int,
                        help="end year (inclusive). Defaults to start year.")
    parser.add_argument("-extension", default='', type=str,
                        help="strategy extension subdirectory")
    parser.add_argument("-snr_type", default=None, type=int,
                        help="SNR file type (default 66)")
    parser.add_argument("-source", default=None, choices=['auto', 'results', 'snr'],
                        help="arc source: 'auto' (prefer results/+failQC/, fall back "
                             "to SNR walk), 'results' (require gnssir output, fast), "
                             "'snr' (walk SNR files, slow but covers all freqs). "
                             "Default auto.")

    g.print_version_to_screen()

    args = parser.parse_args().__dict__
    return {key: value for key, value in args.items() if value is not None}


def main():
    args = parse_arguments()
    try:
        build_tracks(**args)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f'generate_tracks: {exc}')
        sys.exit(1)


if __name__ == "__main__":
    main()
