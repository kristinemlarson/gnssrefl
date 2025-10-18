#!/usr/bin/env python3

"""
VWC Hourly Rolling Module

This module generates VWC estimates from n-hour windows that start at every hour
throughout the day, creating a rolling/sliding time window dataset.

For example, with 6-hour windows (bin_hours=6), this creates VWC estimates from:
    - Window 00:00-06:00
    - Window 01:00-07:00
    - Window 02:00-08:00
    - ... continuing through each hour of the day

"""

import argparse
import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

from datetime import datetime, timedelta
from pathlib import Path

import gnssrefl.gps as g
import gnssrefl.phase_functions as qp
from gnssrefl.utils import str2bool, FileManagement
from gnssrefl.vwc_cl import vwc


def parse_arguments_hourly():
    """Parse command line arguments for vwc_hourly command"""
    parser = argparse.ArgumentParser(description="Generate hourly rolling VWC from subdaily time bins")
    parser.add_argument("station", help="station", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("-year_end", default=None, help="year_end", type=int)
    parser.add_argument("-fr", help="frequency: 1 (L1), 20 (L2C), 5 (L5). Only L2C officially supported.", type=str)
    parser.add_argument("-plt", default=None, type=str, help="boolean for plotting to screen")
    parser.add_argument("-bin_hours", default=6, type=int, help="time bin size in hours (1,2,3,4,6,8,12). Default is 6")
    parser.add_argument("-minvalperbin", default=None, type=int, help="min number of satellite tracks needed per time bin. Default is 10")
    parser.add_argument("-min_req_pts_track", default=None, type=int, help="min number of points for a track to be kept. Default is 100")
    parser.add_argument("-polyorder", default=None, type=int, help="override on polynomial order")
    parser.add_argument("-snow_filter", default=None, type=str, help="boolean, try to remove snow contaminated points. Default is F")
    parser.add_argument("-tmin", default=None, type=float, help="minimum soil texture. Default is 0.05.")
    parser.add_argument("-tmax", default=None, type=float, help="maximum soil texture. Default is 0.50.")
    parser.add_argument("-warning_value", default=None, type=float, help="Phase RMS (deg) threshold for bad tracks, default is 5.5 degrees")
    parser.add_argument("-auto_removal", default=None, type=str, help="Whether you want to remove bad tracks automatically, default is False")
    parser.add_argument("-hires_figs", default=None, type=str, help="Whether you want eps instead of png files")
    parser.add_argument("-advanced", default=None, type=str, help="Shorthand for -vegetation_model 2 (advanced vegetation model)")
    parser.add_argument("-vegetation_model", default=None, type=str, help="Vegetation correction model: 1 (simple, default) or 2 (advanced)")
    parser.add_argument("-extension", default='', type=str, help="which extension -if any - used in analysis json")
    parser.add_argument("-simple_level", default=None, type=str, help="Use simple global leveling instead of polynomial (default: False)")
    parser.add_argument("-level_doys", nargs="*", help="doy limits to define level nodes", type=int)

    g.print_version_to_screen()

    args = parser.parse_args().__dict__

    boolean_args = ['plt','snow_filter','auto_removal','hires_figs','advanced','simple_level']
    args = str2bool(args, boolean_args)
    return {key: value for key, value in args.items() if value is not None}


def combine_offset_files_to_vwc_data(station, fr, bin_hours, extension=''):
    """
    Combine all offset VWC files into a unified vwc_data dictionary. Used for vegetation model 1 processing.

    Reads all VWC offset files (e.g., p038_vwc_L2_6hr+0.txt, p038_vwc_L2_6hr+1.txt, etc.),
    sorts all measurements chronologically, and returns a vwc_data dict.

    Returns
    -------
    vwc_data : dict or None
        Dictionary with 'mjd', 'vwc', 'datetime', 'bin_starts'
        Returns None if no data found
    """
    all_measurements = []

    file_manager = FileManagement(station, 'volumetric_water_content', extension=extension)
    base_vwc_path = file_manager.get_file_path()

    if fr == 20:
        freq_suffix = "_L2"
    elif fr == 1:
        freq_suffix = "_L1"
    elif fr == 5:
        freq_suffix = "_L5"
    else:
        freq_suffix = f"_L{fr}"

    # Read all offset VWC files to combine
    for offset in range(bin_hours):
        vwc_file = base_vwc_path.parent / f"{station}_vwc{freq_suffix}_{bin_hours}hr+{offset}.txt"

        if vwc_file.exists():
            try:
                data = np.loadtxt(vwc_file, comments='%')
                if len(data.shape) == 1:  # Single row
                    data = data.reshape(1, -1)

                for row in data:
                    all_measurements.append(row)
                print(f"  Read {len(data)} VWC measurements from offset {offset}")
            except Exception as e:
                print(f"  Warning: Could not read VWC offset file {vwc_file}: {e}")
        else:
            print(f"  Warning: VWC offset file {vwc_file} not found")

    if not all_measurements:
        print("  Error: No VWC measurements found in any offset files")
        return None

    # Convert to numpy array
    all_measurements = np.array(all_measurements)

    # Build temporary arrays for MJD calculation
    # File columns: [FracYr(0), Year(1), DOY(2), VWC(3), Month(4), Day(5), BinStart(6)]
    years = all_measurements[:, 1].astype(int)
    doys = all_measurements[:, 2].astype(int)
    vwc = all_measurements[:, 3]
    bin_starts = all_measurements[:, 6].astype(int)

    # Convert year/doy/binhour to MJD
    mjd_values = []
    datetimes = []
    for yr, doy, bin_hr in zip(years, doys, bin_starts):
        mjd = g.ydoy2mjd(int(yr), int(doy)) + int(bin_hr) / 24.0
        mjd_values.append(mjd)
        datetimes.append(g.mjd_to_datetime(mjd))

    # Sort by MJD for chronological ordering
    mjd_array = np.array(mjd_values)
    sort_indices = np.argsort(mjd_array)

    mjd_values = [mjd_values[i] for i in sort_indices]
    vwc = vwc[sort_indices]
    datetimes = [datetimes[i] for i in sort_indices]
    bin_starts = bin_starts[sort_indices]

    vwc_data = {
        'mjd': mjd_values,
        'vwc': vwc.tolist(),
        'datetime': datetimes,
        'bin_starts': bin_starts.tolist()
    }

    print(f"  Combined {len(mjd_values)} VWC measurements from offset files")
    return vwc_data


def plot_hourly_vs_daily_vwc(station, fr, bin_hours, extension=''):
    """
    Plot hourly rolling VWC (gray dots) vs daily VWC (bold red) for comparison.

    Requires both daily and hourly VWC files to exist.
    """

    if fr == 20:
        freq_suffix = "_L2"
    elif fr == 1:
        freq_suffix = "_L1"
    elif fr == 5:
        freq_suffix = "_L5"
    else:
        freq_suffix = f"_L{fr}"

    file_manager = FileManagement(station, 'volumetric_water_content', extension=extension)
    base_vwc_path = file_manager.get_file_path()

    daily_file = base_vwc_path.parent / f"{station}_vwc{freq_suffix}_24hr+0.txt"
    hourly_file = base_vwc_path.parent / f"{station}_vwc{freq_suffix}_rolling{bin_hours}hr.txt"
    
    # Ensure both files exist
    if not daily_file.exists():
        print(f"Warning: Daily VWC file not found: {daily_file}")
        return
    
    if not hourly_file.exists():
        print(f"Warning: Hourly VWC file not found: {hourly_file}")
        return
    
    try:
        # Read daily VWC data
        daily_data = np.loadtxt(daily_file, comments='%')
        if len(daily_data.shape) == 1:
            daily_data = daily_data.reshape(1, -1)
        
        # Read hourly VWC data  
        hourly_data = np.loadtxt(hourly_file, comments='%')
        if len(hourly_data.shape) == 1:
            hourly_data = hourly_data.reshape(1, -1)
        
        # Create datetime arrays
        daily_times = []
        for row in daily_data:
            year_val, doy = int(row[1]), int(row[2])
            daily_times.append(datetime.strptime(f'{year_val} {doy}', '%Y %j'))
        
        hourly_times = []
        for row in hourly_data:
            year_val, doy, bin_start = int(row[1]), int(row[2]), int(row[6])
            hourly_times.append(datetime.strptime(f'{year_val} {doy}', '%Y %j') + timedelta(hours=bin_start))
        
        # Create plot
        plt.figure(figsize=(12, 6))
        
        # Plot hourly data as faded gray dots
        plt.plot(hourly_times, hourly_data[:, 3], 'o', color='gray', alpha=0.4, markersize=3, 
                label=f'Hourly rolling ({bin_hours}hr windows)')
        
        # Plot daily data as bold red line
        plt.plot(daily_times, daily_data[:, 3], '-', color='red', linewidth=2,
                label='Daily VWC')
        
        # Formatting
        plt.xlabel('Date')
        plt.ylabel('Volumetric Water Content')
        plt.title(f'Station {station}: Daily vs Hourly Rolling VWC')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Auto-format x-axis dates
        plt.gcf().autofmt_xdate()
        
        plt.show()
        
    except Exception as e:
        print(f"Error creating VWC comparison plot: {e}")


def vwc_hourly(station: str, year: int, year_end: int = None, fr: str = None, plt: bool = True, bin_hours: int = 6,
               minvalperbin: int = 5, min_req_pts_track: int = None, polyorder: int = -99,
               snow_filter: bool = False, tmin: float = None, tmax: float = None,
               warning_value: float = None, auto_removal: bool = False, hires_figs: bool = False,
               advanced: bool = False, vegetation_model: int = None, extension: str = '',
               simple_level: bool = False, level_doys: list = []):
    """
    Generate VWC estimates from n-hour windows that start at every hour throughout
    the day, creating a rolling/sliding time window dataset.

    For example, with bin_hours=6, this creates VWC estimates from:
    - Window 00:00-06:00
    - Window 01:00-07:00
    - Window 02:00-08:00
    - ... continuing through the day

    WARNING
    -------
    This function is EXPERIMENTAL. Only daily (24-hour) VWC measurements are
    officially supported. Subdaily/hourly results should be used with caution
    and are provided for research purposes only.

    Vegetation Models
    ---------------
    Vegetation Model 1 (simple):
        Runs vwc() for each offset (0, 1, 2, ..., bin_hours-1) to create separate
        VWC files, then combines them chronologically.

        NOTE: Each offset calculates its own vegetation correction baseline, which
        can introduce systematic biases between offsets. See issue #358:
        https://github.com/kristinemlarson/gnssrefl/issues/358

    Vegetation Model 2 (advanced):
        Runs vwc() once with -save_tracks to generate track files, then aggregates
        those saved tracks into different time bins. This avoids reprocessing the
        vegetation corrections for each offset and eliminates the bias issue present in Model 1.

    Examples
    --------
    vwc_hourly p038 2022
        6-hour rolling bins for station p038 (default, model 1)
    vwc_hourly p038 2022 -bin_hours 12 -minvalperbin 5
        12-hour rolling bins with minimum 5 tracks per bin
    vwc_hourly okl2 2012 -vegetation_model 2
        6-hour rolling bins using advanced vegetation model (model 2, recommended)

    Parameters
    ----------
    station : str
        4 character ID of the station
    year : int
        full Year
    year_end : int, optional
        last year for analysis
    fr : str, optional
        GNSS frequency. Default is from JSON or 20 (L2C)
    bin_hours : int, optional
        time bin size in hours (1,2,3,4,6,8,12). Default is 6
    minvalperbin : int, optional
        min number of satellite tracks needed per time bin. Default is 5
    simple_level : bool, optional
        use simple leveling instead of polynomial (default: False)
    level_doys : list, optional
        pair of day of years for baseline leveling period
    (other parameters same as vwc function)

    Returns
    -------
    Creates hourly rolling VWC file: station_vwc_L2_rolling6hr.txt
    """
    valid_bin_hours = [1, 2, 3, 4, 6, 8, 12]  # No 24hr for rolling
    if bin_hours not in valid_bin_hours:
        print(f"Error: bin_hours must be one of {valid_bin_hours} for hourly rolling")
        sys.exit()

    print(f"Generating hourly rolling VWC with {bin_hours}-hour windows")
    print(f"Processing {bin_hours} offsets for station {station}, year {year}")

    # Resolve frequency once for both models
    fr_list = qp.get_vwc_frequency(station, extension, fr)
    if len(fr_list) > 1:
        print("Error: vwc_hourly can only process one frequency at a time.")
        sys.exit()
    resolved_fr = fr_list[0]

    if advanced:
        veg_model = 2
    elif vegetation_model:
        veg_model = int(vegetation_model)
    else:
        veg_model = 1

    # Process based on vegetation model
    if veg_model == 1:
        # Simple model
        print(f"Using traditional offset+aggregation processing for simple vegetation model")

        # First run daily VWC for comparison plotting
        print(f"\n=== Generating Daily VWC for comparison ===")
        vwc(station=station, year=year, year_end=year_end, fr=fr, plt=False, screenstats=False,
            bin_hours=24, minvalperbin=minvalperbin, bin_offset=0,
            min_req_pts_track=min_req_pts_track, polyorder=polyorder,
            snow_filter=snow_filter, tmin=tmin, tmax=tmax,
            warning_value=warning_value, auto_removal=auto_removal, hires_figs=hires_figs,
            advanced=advanced, vegetation_model=veg_model, extension=extension,
            simple_level=simple_level, level_doys=level_doys)

        # Process each offset
        for offset in range(bin_hours):
            print(f"\n=== Processing offset {offset}/{bin_hours-1} ({offset:02d}-{(offset+bin_hours)%24:02d}h bins) ===")

            vwc(station=station, year=year, year_end=year_end, fr=fr, plt=False, screenstats=False,
                bin_hours=bin_hours, minvalperbin=minvalperbin, bin_offset=offset,
                min_req_pts_track=min_req_pts_track, polyorder=polyorder,
                snow_filter=snow_filter, tmin=tmin, tmax=tmax,
                warning_value=warning_value, auto_removal=auto_removal, hires_figs=hires_figs,
                advanced=advanced, vegetation_model=veg_model, extension=extension,
                simple_level=simple_level, level_doys=level_doys)

        # Combine all VWC offset files
        print("=== Combining all", bin_hours, "VWC offset files ===")
        vwc_data = combine_offset_files_to_vwc_data(station, resolved_fr, bin_hours, extension)

        if vwc_data is None:
            print("Error: No VWC measurements generated from any offset")
            sys.exit()

    elif veg_model == 2:
        # Model 2 (advanced)
        print(f"Using efficient model 2 processing with saved track data")

        # Get parameters from set_parameters to ensure we have defaults
        _, tmin, tmax, _, _, year_end, plt, _, _, _, _, _, extension, \
            _, _, _, level_doys, _ = qp.set_parameters(
                station, level_doys, None, tmin, tmax, min_req_pts_track,
                resolved_fr, year, year_end, plt, auto_removal, warning_value, extension,
                bin_hours, minvalperbin, 0
            )

        # Delete existing track files for requested year(s) and regenerate
        xdir = os.environ['REFL_CODE']
        subdir_path = f"{station}/{extension}" if extension else station
        track_dir = f'{xdir}/Files/{subdir_path}/individual_tracks'

        # Determine year range to delete/regenerate
        freq_suffix = qp.get_temporal_suffix(resolved_fr)
        years_to_regenerate = range(year, (year_end if year_end else year) + 1)

        # Delete track files for requested years only
        if os.path.exists(track_dir):
            deleted_count = 0
            for yr in years_to_regenerate:
                pattern = f'{track_dir}/{station}_track_sat*_quad*_{yr}{freq_suffix}.txt'
                files_to_delete = glob.glob(pattern)
                for f in files_to_delete:
                    os.remove(f)
                    deleted_count += 1
            if deleted_count > 0:
                print(f'Deleted {deleted_count} existing track files for year(s) {year}-{year_end if year_end else year}')

        # Generate fresh track files for requested years
        print("=== Generating track data with vwc -save_tracks T ===")
        vwc(station=station, year=year, year_end=year_end, fr=resolved_fr, plt=False, screenstats=False,
            bin_hours=24, minvalperbin=minvalperbin, bin_offset=0,
            min_req_pts_track=min_req_pts_track, polyorder=polyorder,
            snow_filter=snow_filter, tmin=tmin, tmax=tmax,
            warning_value=warning_value, auto_removal=auto_removal, hires_figs=hires_figs,
            advanced=True, vegetation_model=2, extension=extension,
            simple_level=simple_level, level_doys=level_doys, save_tracks=True)

        print("=== Generating hourly rolling VWC from saved track data ===")

        # Generate all hourly rolling bins from track data
        vwc_data = generate_rolling_vwc_from_tracks(station, resolved_fr, bin_hours, minvalperbin, extension, year, year_end)

        if vwc_data is None:
            print("Error: Failed to generate VWC data from tracks.")
            sys.exit()

        # Apply leveling to the complete rolling dataset
        print("=== Applying leveling to rolling VWC data ===")
        leveled_vwc, leveling_info = qp.apply_vwc_leveling(
            vwc_data['vwc'],
            tmin,
            simple=simple_level,
            mjd=vwc_data['mjd'],
            level_doys=level_doys,
            polyorder=polyorder,
            station=station, plot_debug=False, plt2screen=False,
            extension=extension,
            fr=resolved_fr, bin_hours=bin_hours, bin_offset=0
        )

        # Update vwc_data with leveled values
        vwc_data['vwc'] = leveled_vwc if isinstance(leveled_vwc, list) else leveled_vwc.tolist()

    else:
        print(f"Error: Vegetation model {veg_model} is not supported. Use 1 (simple) or 2 (advanced).")
        sys.exit()

    print("=== Writing rolling VWC output file ===")
    qp.write_rolling_vwc_output(station, vwc_data, resolved_fr, bin_hours, extension, vegetation_model=veg_model)

    print(f"Successfully generated {len(vwc_data['vwc'])} hourly rolling VWC measurements")
    print("WARNING: vwc_hourly is experimental code and currently under development.")
    print("Please see https://github.com/kristinemlarson/gnssrefl/issues/358 for the latest discussion.")

    if plt:
        print("=== Generating VWC Comparison Plot ===")
        plot_hourly_vs_daily_vwc(station, resolved_fr, bin_hours, extension)


def main_hourly():
    """CLI entry point for vwc_hourly command"""
    args = parse_arguments_hourly()
    vwc_hourly(**args)


def main():
    """Alternative entry point (for compatibility)"""
    main_hourly()


def generate_rolling_vwc_from_tracks(station, fr, bin_hours, minvalperbin, extension='', year=None, year_end=None):
    """
    Generate complete hourly rolling VWC dataset from saved track files.

    Loads all track data once and creates bins at every hour (0:00, 1:00, 2:00, etc.)
    for the entire dataset.

    Parameters
    ----------
    station : str
        4-character station name
    fr : int
        Frequency code (20 for L2C, etc.)
    bin_hours : int
        Time bin size in hours (e.g., 6 for 6-hour windows)
    minvalperbin : int
        Minimum tracks required per time bin
    extension : str
        Extension for file paths (default: '')
    year : int, optional
        Start year for filtering track files
    year_end : int, optional
        End year for filtering track files

    Returns
    -------
    vwc_data : dict or None
        Dictionary with 'mjd', 'vwc', 'datetime', 'bin_starts' (NOT leveled yet)
        Returns None if no track data found
    """
    xdir = os.environ['REFL_CODE']
    subdir_path = f"{station}/{extension}" if extension else station
    track_dir = f'{xdir}/Files/{subdir_path}/individual_tracks'

    if not os.path.exists(track_dir):
        print(f'No saved track data found in {track_dir}')
        print('Run vwc with -save_tracks T first to generate individual track files')
        return None

    freq_suffix = qp.get_temporal_suffix(fr)

    # Determine year range
    if year and year_end:
        years_to_load = range(year, year_end + 1)
    elif year:
        years_to_load = [year]
    else:
        # Load all years if not specified
        pattern = f'{track_dir}/{station}_track_sat*_quad*_*{freq_suffix}.txt'
        track_files = glob.glob(pattern)
        years_to_load = None

    # Load track files for specified years
    if years_to_load:
        track_files = []
        for yr in years_to_load:
            pattern = f'{track_dir}/{station}_track_sat*_quad*_{yr}{freq_suffix}.txt'
            track_files.extend(glob.glob(pattern))

    if not track_files:
        print(f'No track files found matching pattern: {pattern}')
        print('Run vwc with -save_tracks T first to generate individual track files')
        return None

    print(f'Loading {len(track_files)} saved track files for hourly rolling VWC generation...')

    # Combine all track data into single array
    all_data = []
    for track_file in track_files:
        try:
            data = np.loadtxt(track_file, comments='%')
            if len(data.shape) == 1:
                data = data.reshape(1, -1)
            all_data.append(data)
        except Exception as e:
            print(f'Warning: Could not load track file {track_file}: {e}')
            continue

    if not all_data:
        print('No valid track data loaded')
        return None

    combined_data = np.vstack(all_data)
    print(f'Loaded {len(combined_data)} individual track observations from saved files')

    # Extract columns: Year(0), DOY(1), Hour(2), MJD(3), VWC(16)
    hours = combined_data[:, 2]
    mjds = combined_data[:, 3]
    vwc = combined_data[:, 16]  # VWC in percentage units (0-60), leveling will convert to decimal

    # Generate hourly rolling bins for ALL hours (0, 1, 2, ..., 23)
    unique_days = np.unique(np.floor(mjds))

    all_mjd = []
    all_vwc = []
    all_binstarts = []

    print(f'Generating hourly rolling bins ({bin_hours}-hour windows at every hour)...')

    # For each day, create bins starting at every hour
    for day_mjd in unique_days:
        for bin_start_hour in range(24):  # 0, 1, 2, ..., 23
            bin_end_hour = (bin_start_hour + bin_hours) % 24

            # Select tracks that fall within this time bin
            if bin_end_hour <= bin_start_hour:  # Crosses midnight
                day_mask = (np.floor(mjds) == day_mjd) | (np.floor(mjds) == day_mjd + 1)
                time_mask = day_mask & ((hours >= bin_start_hour) | (hours < bin_end_hour))
            else:
                day_mask = np.floor(mjds) == day_mjd
                time_mask = day_mask & (hours >= bin_start_hour) & (hours < bin_end_hour)

            # Get VWC values for this time bin
            bin_vwc = vwc[time_mask]

            # Apply minimum count threshold
            if len(bin_vwc) >= minvalperbin:
                all_mjd.append(day_mjd + bin_start_hour / 24.0)  # Add fractional hour to MJD
                all_vwc.append(np.mean(bin_vwc))
                all_binstarts.append(bin_start_hour)

    if not all_mjd:
        print('No valid time bins generated (try reducing -minvalperbin)')
        return None

    print(f'Generated {len(all_mjd)} hourly rolling VWC measurements')

    # Build vwc_data dict (NOT leveled yet - that happens in calling function)
    datetimes = [g.mjd_to_datetime(mjd) for mjd in all_mjd]
    vwc_data = {
        'mjd': all_mjd,
        'vwc': all_vwc,
        'datetime': datetimes,
        'bin_starts': all_binstarts
    }

    return vwc_data


if __name__ == "__main__":
    main()