import argparse
import contextlib
import json
import numpy as np
import os
import sys
import time
import multiprocessing

from tqdm import tqdm

import gnssrefl.gps as g
import gnssrefl.gnssir_v2 as guts2
import gnssrefl.phase_functions as qp
from gnssrefl.tracks import warn_legacy_apriori_and_exit
from gnssrefl.utils import FileManagement, str2bool


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("doy", help="doy", type=int)
    parser.add_argument("-snr", default=None, help="snr file ending", type=int)
    parser.add_argument("-fr", default=None, nargs="*", type=int,
                        help="Default path: subset of frequencies present in vwc_tracks.json, "
                             "e.g. -fr 1 101 for GPS + GLONASS L1 (default: all freqs in vwc_tracks.json). "
                             "GPS (especially L2C) is widely validated; support for other constellations "
                             "and signals is in testing and, with this caveat, available for research. "
                             "Legacy path (-legacy T): single frequency (1, 20, or 5).")
    parser.add_argument("-doy_end", default=None, type=int, help="doy end")
    parser.add_argument("-year_end", default=None, type=int, help="year end")
    parser.add_argument("-extension", default='', help="analysis extension for json file", type=str)
    parser.add_argument("-e1", default=None, type=float),
    parser.add_argument("-e2", default=None, type=float),
    parser.add_argument("-plt", default=None, type=str, help="plots come to the screen - which you do not want!")
    parser.add_argument("-screenstats", default=None, type=str, help="stats come to the screen")
    parser.add_argument("-gzip", default=None, type=str, help="gzip SNR files after use, default is True" )
    parser.add_argument("-par", default=None, type=int, help="Number of processes to spawn (up to 10)")
    parser.add_argument("-midnite", default=None, type=str, help="load adjacent day data for midnight-crossing arcs (default is true)")
    parser.add_argument("-ampl", default=None, type=float, help="Min spectral amplitude")
    parser.add_argument("-savearcs", default=None, type=str, help="save individual arcs, default is False")
    parser.add_argument("-savearcs_format", default=None, type=str, help="format of saved arcs (txt or pickle), default is txt")
    parser.add_argument("-dec", default=None, type=int, help="decimate SNR data to this sampling rate")
    parser.add_argument("-dbhz", default=None, type=str, help="keep SNR in dB-Hz units (default is false)")
    parser.add_argument("-recompute_lsp", default=None, type=str, help="recompute LSP for all arcs instead of using gnssir results (default is false)")
    parser.add_argument("-legacy", default=None, type=str,
                        help="use the legacy GPS-only apriori_RH flow (default False). "
                             "Deprecated; may be removed after 2027-01-01.")

    g.print_version_to_screen()

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['plt', 'screenstats', 'gzip', 'midnite', 'savearcs', 'dbhz', 'recompute_lsp', 'legacy']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def quickphase(station: str, year: int, doy: int, year_end: int = None, doy_end: int = None, snr: int = 66,
        fr=None, e1: float = None, e2: float = None, plt: bool = False, screenstats: bool = False, gzip: bool = None, extension: str = '', par: int = None, midnite: bool = True, ampl: float = None, savearcs: bool = False, savearcs_format: str = None, dec: int = None, dbhz: bool = None, recompute_lsp: bool = False,
        legacy: bool = False):
    """
    quickphase computes phase, which are subsequently used in vwc. The command line call is phase
    (which maybe we should change).

    By default, tagging of arcs with apriori RH and track-mean azimuth is
    driven by vwc_tracks.json (produced by vwc_input). One unified pipeline
    across GPS/GLONASS/Galileo/BeiDou. Pass -legacy T to use the old GPS-only
    flow that reads apriori_rh_{fr}.txt.

    Examples
    --------
    phase p038 2021 4
        analyzes data for year 2021 and day of year 4

    phase p038 2021 1 -doy_end 365
        analyzes data for the whole year

    phase p038 2021 1 -doy_end 365 -par 5
        analyzes data for the whole year using 5 parallel processes

    Parameters
    ----------
    station: str
        4 character ID of the station.
    year: int
        full Year to evaluate.
    doy: int
        day of year to evaluate.
    year_end: int, optional
        year to end analysis. Using this option will create a range from year-year_end.
        Default is None.
    doy_end: int, optional
        Day of year to end analysis. Using this option will create a range of doy-doy_end.
        If also using year_end, then this will be the day to end analysis in the year_end requested.
        Default is None.
    snr : int, optional
        SNR format. This tells the code what elevation angles are in the SNR file
        value options:

            66 (default) : data with elevation angles less than 30 degrees

            99 : data with elevation angles between 5 and 30 degrees

            88 : data with all elevation angles

            50 : data with elevation angles less than 10 degrees

    fr : list of int, optional
        Default path: subset of the frequencies present in vwc_tracks.json.
        When None (default), all freqs in vwc_tracks.json are processed. An
        error is raised if a requested freq is not in vwc_tracks.json.
        Legacy path: single frequency (1, 20, or 5). Default 20 (L2C).
    e1 : float, optional
        Elevation angle lower limit in degrees for the LSP. default is from json (typically 5)
    e2: float, optional
        Elevation angle upper limit in degrees for the LSP. default is from json (typically 25)
    plt: bool, optional
        Whether to plot results. Default is False
    screenstats: bool, optional
        Whether to print stats to the screen. Default is False
    gzip : bool, optional
        gzip the SNR file after use.  Default is True
    par : int, optional
        Number of parallel processes to spawn (up to 10). Default is 1 (single process).
    midnite : bool, optional
        Allow midnight crossings. When True, loads +/- 2 hours from adjacent days. Default is True.

    Returns
    -------
    Saves a file for each day in the doy-doy_end range: $REFL_CODE/<year>/phase/<station>/<doy>.txt

    columns in files:
        year doy hour phase nv azimuth sat ampl emin emax delT aprioriRH freq estRH pk2noise LSPAmp

    """

    if len(station) != 4:
        print('Station name must be four characters long. Exiting.')
        sys.exit()

    # Read station json once, pass to get_vwc_frequency to avoid double-loading
    station_config = guts2.read_json_file(station, extension)

    if legacy:
        print('Note: -legacy T is deprecated and may be removed after 2027-01-01.')
        # Legacy accepts a single freq. argparse gives a list; unwrap or reject.
        if fr and len(fr) > 1:
            print(f'Error: -legacy T accepts a single frequency only; got {fr}.')
            sys.exit()
        fr_cmd = str(fr[0]) if fr else None
        fr_list = qp.get_vwc_frequency(station, extension, fr_cmd, station_config=station_config)
        # Check that an apriori file exists for each requested frequency.
        for f in fr_list:
            ex = qp.apriori_file_exist(station, f, extension)
            if not ex:
                print(f'No apriori RH file exists for frequency {f}. Please run vwc_input -legacy T.')
                sys.exit()
    else:
        vwc_tracks_path = FileManagement(station, 'vwc_tracks_file', extension=extension).get_file_path(ensure_directory=False)
        if not vwc_tracks_path.exists():
            warn_legacy_apriori_and_exit(station, 'vwc_tracks.json', extension)
            print(f'vwc_tracks.json not found at {vwc_tracks_path}. Run `vwc_input` first.')
            sys.exit()
        print(f'using vwc tracks file: {vwc_tracks_path}')
        with open(vwc_tracks_path) as f:
            vwc_doc = json.load(f)
        available_freqs = sorted({int(t['freq']) for t in vwc_doc['tracks'].values()})
        if fr:
            fr_list = [int(f) for f in fr]
            missing = [f for f in fr_list if f not in available_freqs]
            if missing:
                print(f'Error: requested frequencies {missing} are not in vwc_tracks.json.')
                print(f'Available: {available_freqs}')
                sys.exit()
        else:
            fr_list = available_freqs
        print(f'processing frequencies: {fr_list}')

    # in case you want to analyze multiple days of data
    if not doy_end:
        doy_end = doy

    # in case you want to analyze only data within one year
    if not year_end:
        year_end = year

    exitS = g.check_inputs(station, year, doy, snr)

    if exitS:
        sys.exit()

    year_end_max_doy = g.dec31(year_end)
    if doy_end == 366 and year_end_max_doy == 365:
        print(f'doy_end 366 clamped to 365 for non-leap year {year_end}')
        doy_end = 365
    elif doy_end > year_end_max_doy:
        print(f'doy_end {doy_end} is not valid for {year_end} (max {year_end_max_doy}). Exiting')
        sys.exit()

    if e1 is not None:
        station_config['e1'] = e1
    if e2 is not None:
        station_config['e2'] = e2
    if ampl is not None:
        station_config['reqAmp'] = [ampl]
    station_config['screenstats'] = screenstats
    station_config['midnite'] = midnite
    if gzip is not None:
        station_config['gzip'] = gzip
    else:
        guts2.gzip_migration(station_config, station, extension)
    station_config['savearcs'] = savearcs
    if savearcs_format is not None:
        station_config['savearcs_format'] = savearcs_format
    if dec is not None:
        station_config['dec'] = dec
    if dbhz is not None:
        station_config['dbhz'] = dbhz
    station_config['recompute_lsp'] = recompute_lsp

    # Set up timing and parallel processing
    t1 = time.time()

    # Set default for par and validate
    if isinstance(par, type(None)):
        par = 1

    if not isinstance(par, int) or par <= 0 or par > 10:
        print('Number of processes must be between 1 and 10. Submit again. Exiting.')
        sys.exit()

    # Check for single day processing
    if (year == year_end) and (doy == doy_end):
        if par > 1:
            print('You are analyzing only one day of data - no reason to submit multiple processes')
            par = 1

    # Create args for worker function
    args = {
        'station': station, 'snr': snr, 'fr_list': fr_list,
        'station_config': station_config, 'extension': extension,
        'legacy': legacy,
    }

    total_arcs = 0
    if par == 1:
        print('Sequential processing\n')
        process_phase_sequential(year, year_end, doy, doy_end, args)
    else:
        print('Per-day output suppressed in parallel mode. Run without -par to see detailed output.')

        # Build flat list of (year, doy) work units
        MJD1 = int(g.ydoy2mjd(year, doy))
        MJD2 = int(g.ydoy2mjd(year_end, doy_end))
        day_list = []
        for mjd in range(MJD1, MJD2 + 1):
            y, d = g.modjul_to_ydoy(mjd)
            day_list.append((y, d))

        manager = multiprocessing.Manager()
        error_queue = manager.Queue()
        pool = multiprocessing.Pool(processes=par)

        worker_args = [(y, d, args, error_queue) for y, d in day_list]
        total_arcs = 0
        with tqdm(pool.imap_unordered(process_phase_day_worker, worker_args),
                  total=len(day_list),
                  desc=f"phase {station}",
                  unit="day") as pbar:
            for n_arcs in pbar:
                total_arcs += n_arcs
                elapsed = time.time() - t1
                ms_per_arc = elapsed / total_arcs * 1000 if total_arcs else 0
                pbar.set_postfix_str(f"{total_arcs} arcs, {ms_per_arc:.1f} ms/arc")

        pool.close()
        pool.join()

        if not error_queue.empty():
            print("One (or more) of the processes encountered errors. Will not proceed until errors are fixed.")
            i = 1
            while not error_queue.empty():
                e = error_queue.get()
                print(f"Error {i} type: {type(e)}. Error {i} message: {e}")
                i += 1
            sys.exit(1)

    t2 = time.time()
    elapsed = round(t2-t1, 2)
    ndays = int(g.ydoy2mjd(year_end, doy_end)) - int(g.ydoy2mjd(year, doy)) + 1
    if par > 1 and total_arcs:
        ms_per_arc = round(elapsed / total_arcs * 1000, 1)
        print(f'Processed {ndays} days, {total_arcs} arcs in {elapsed} s ({ms_per_arc} ms/arc)')
    else:
        print(f'Processed {ndays} days in {elapsed} s ({round(elapsed/ndays, 2)} s/day)')


def count_result_arcs(result_path):
    """Count non-comment lines in a result file."""
    try:
        with open(result_path) as f:
            return sum(1 for line in f if not line.startswith('%'))
    except FileNotFoundError:
        return 0


def process_phase_day(year, doy, args):
    """Process a single day for sequential mode."""
    print(f'Analyzing year/day of year {year}/{doy}')
    qp.phase_tracks(args['station'], year, doy, args['snr'], args['fr_list'],
                   args['station_config'], args['extension'],
                   legacy=args['legacy'])


def process_phase_sequential(year, year_end, doy, doy_end, args):
    """Sequential processing function"""
    if year_end != year:  # Multi-year processing
        year_range = np.arange(year, year_end+1)
        for y in np.arange(year, year_end+1):
            if y == year_range[0]:
                date_range = np.arange(doy, 366)
            elif y == year_range[-1]:
                date_range = np.arange(1, doy_end+1)
            else:
                date_range = np.arange(1, 366)

            for d in date_range:
                process_phase_day(y, d, args)
    else:  # Single year processing
        for d in np.arange(doy, doy_end + 1):
            process_phase_day(year, d, args)


def process_phase_day_worker(worker_args):
    """Worker for parallel phase processing. Returns arc count for progress bar."""
    year, doy, args, error_queue = worker_args
    try:
        with contextlib.redirect_stdout(open(os.devnull, 'w')):
            qp.phase_tracks(args['station'], year, doy, args['snr'], args['fr_list'],
                           args['station_config'], args['extension'],
                           legacy=args['legacy'])
        xdir = str(os.environ['REFL_CODE'])
        station = args['station']
        extension = args.get('extension') or ''
        result_path = os.path.join(xdir, str(year), 'phase', station, extension, f'{doy:03d}.txt')
        return count_result_arcs(result_path)
    except Exception as e:
        print('***********************************************************************')
        print('Error in phase processing: ', year, doy)
        print('***********************************************************************')
        error_queue.put(e)
        return 0

def main():
    args = parse_arguments()
    quickphase(**args)


if __name__ == "__main__":
    main()
