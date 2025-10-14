#!/usr/bin/env python3

"""
VWC Hourly Rolling Module

This module provides functionality for generating hourly rolling VWC measurements
by processing all possible bin offsets and combining them into a chronologically
ordered dataset.

Extracted from vwc_cl.py for better separation of concerns.
"""

import argparse
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

from datetime import datetime, timedelta
from pathlib import Path

import gnssrefl.gps as g
import gnssrefl.phase_functions as qp
import gnssrefl.advanced_vegetation_correction as avc
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
    parser.add_argument("-subdir", default=None, type=str, help="use non-default subdirectory for output files")
    parser.add_argument("-tmin", default=None, type=float, help="minimum soil texture. Default is 0.05.")
    parser.add_argument("-tmax", default=None, type=float, help="maximum soil texture. Default is 0.50.")
    parser.add_argument("-warning_value", default=None, type=float, help="Phase RMS (deg) threshold for bad tracks, default is 5.5 degrees")
    parser.add_argument("-auto_removal", default=None, type=str, help="Whether you want to remove bad tracks automatically, default is False")
    parser.add_argument("-hires_figs", default=None, type=str, help="Whether you want eps instead of png files")
    parser.add_argument("-advanced", default=None, type=str, help="Shorthand for -vegetation_model 2 (advanced vegetation model)")
    parser.add_argument("-vegetation_model", default=None, type=str, help="Vegetation correction model: 1 (simple, default) or 2 (advanced)")
    parser.add_argument("-extension", default='', type=str, help="which extension -if any - used in analysis json")

    g.print_version_to_screen()

    args = parser.parse_args().__dict__

    boolean_args = ['plt','snow_filter','auto_removal','hires_figs','advanced']
    args = str2bool(args, boolean_args)
    return {key: value for key, value in args.items() if value is not None}


def combine_vwc_files_to_hourly(station, fr, bin_hours, subdir, extension):
    """
    Combine all offset VWC files into a single chronologically ordered hourly rolling dataset.
    
    Reads all VWC offset files (e.g., p038_vwc_L2_6hr+0.txt, p038_vwc_L2_6hr+1.txt, etc.),
    sorts all measurements by fractional year, and writes a combined rolling hourly VWC file.
    """
    import numpy as np
    from pathlib import Path
    
    all_measurements = []
    
    # Use FileManagement for consistent path handling
    file_manager = FileManagement(station, 'volumetric_water_content', extension=extension)
    base_vwc_path = file_manager.get_file_path()
    
    # Determine frequency suffix (consistent with phase_functions.py)
    if fr == 20:
        freq_suffix = "_L2"
    elif fr == 1:
        freq_suffix = "_L1"
    elif fr == 5:
        freq_suffix = "_L5"
    else:
        freq_suffix = f"_L{fr}"
    
    # Read all offset VWC files
    for offset in range(bin_hours):
        vwc_file = base_vwc_path.parent / f"{station}_vwc{freq_suffix}_{bin_hours}hr+{offset}.txt"
        
        if vwc_file.exists():
            try:
                data = np.loadtxt(vwc_file, comments='%')
                if len(data.shape) == 1:  # Single row
                    data = data.reshape(1, -1)
                
                # Add to collection
                for row in data:
                    all_measurements.append(row)
                print(f"  Read {len(data)} VWC measurements from offset {offset}")
            except Exception as e:
                print(f"  Warning: Could not read VWC offset file {vwc_file}: {e}")
        else:
            print(f"  Warning: VWC offset file {vwc_file} not found")
    
    if not all_measurements:
        print("  Error: No VWC measurements found in any offset files")
        return np.array([])
    
    # Convert to numpy array for sorting
    all_measurements = np.array(all_measurements)
    
    # Sort by Year, Month, Day, BinStart for perfect chronological order
    sort_indices = np.lexsort((
        all_measurements[:, 6],  # BinStart (primary sort)
        all_measurements[:, 5],  # Day  
        all_measurements[:, 4],  # Month
        all_measurements[:, 1]   # Year (final sort)
    ))
    sorted_measurements = all_measurements[sort_indices]
    
    # Write combined rolling hourly VWC file
    rolling_vwc_file = base_vwc_path.parent / f"{station}_vwc{freq_suffix}_rolling{bin_hours}hr.txt"
    
    # Write header
    with open(rolling_vwc_file, 'w') as f:
        f.write(f"% Soil Moisture Results for GNSS Station {station}\n")
        f.write("% Frequency used: L2C\n" if fr == 20 else f"% Frequency used: L{fr}\n")
        f.write("% https://github.com/kristinemlarson/gnssrefl\n")
        f.write(f"% Hourly rolling VWC from {bin_hours}-hour windows\n")
        f.write("% FracYr    Year   DOY   VWC Month Day BinStart\n")
        
        # Write sorted data
        for row in sorted_measurements:
            f.write(f"{row[0]:10.4f} {int(row[1]):4d} {int(row[2]):4d} {row[3]:8.3f} {int(row[4]):3d} {int(row[5]):3d} {int(row[6]):3d}\n")
    
    print(f"  Wrote {len(sorted_measurements)} VWC measurements to {rolling_vwc_file}")
    return sorted_measurements


def plot_hourly_vs_daily_vwc(station, fr, bin_hours, subdir, extension, year, year_end):
    """
    Plot hourly rolling VWC (gray dots) vs daily VWC (bold red) for comparison.
    
    Requires both daily and hourly VWC files to exist.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    from pathlib import Path
    from datetime import datetime, timedelta
    
    # Determine frequency suffix
    if fr == 20:
        freq_suffix = "_L2"
    elif fr == 1:
        freq_suffix = "_L1"
    elif fr == 5:
        freq_suffix = "_L5"
    else:
        freq_suffix = f"_L{fr}"
    
    # Use FileManagement for consistent path handling with extensions
    file_manager = FileManagement(station, 'volumetric_water_content', extension=extension)
    base_vwc_path = file_manager.get_file_path()
    
    # Generate file paths using consistent suffix patterns
    daily_file = base_vwc_path.parent / f"{station}_vwc{freq_suffix}_24hr+0.txt"
    hourly_file = base_vwc_path.parent / f"{station}_vwc{freq_suffix}_rolling{bin_hours}hr.txt"
    
    # Check if both files exist
    if not daily_file.exists():
        print(f"Warning: Daily VWC file not found: {daily_file}")
        print("Run 'vwc' with 24-hour bins first to generate daily VWC for comparison")
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
               minvalperbin: int = None, min_req_pts_track: int = None, polyorder: int = -99,
               snow_filter: bool = False, subdir: str = None, tmin: float = None, tmax: float = None,
               warning_value: float = None, auto_removal: bool = False, hires_figs: bool = False,
               advanced: bool = False, vegetation_model: int = None, extension: str = None):
    """
    Generate hourly rolling VWC from all possible bin offsets.
    
    This function runs vwc() for each offset (0, 1, 2, ..., bin_hours-1) to create
    separate VWC files, then combines them chronologically into a single hourly rolling dataset.
    
    Examples
    --------
    vwc_hourly p038 2022
        6-hour rolling bins for station p038 (default)
    vwc_hourly p038 2022 -bin_hours 12 -minvalperbin 5
        12-hour rolling bins with minimum 5 tracks per bin
        
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
    (other parameters same as vwc function)
    
    Returns
    -------
    Creates hourly rolling VWC file: station_vwc_L2_rolling6hr.txt
    """
    # Validate bin_hours
    valid_bin_hours = [1, 2, 3, 4, 6, 8, 12]  # No 24hr for rolling
    if bin_hours not in valid_bin_hours:
        print(f"Error: bin_hours must be one of {valid_bin_hours} for hourly rolling")
        sys.exit()
    
    # Set default for subdaily analysis
    if minvalperbin is None:
        minvalperbin = 5
    
    # Map extension to subdir (following gnssrefl convention: station/extension)
    if extension and not subdir:
        subdir = f'{station}/{extension}'
    
    print(f"Generating hourly rolling VWC with {bin_hours}-hour windows")
    print(f"Processing {bin_hours} offsets for station {station}, year {year}")
    
    # Handle vegetation model selection
    veg_model = 1  # default is simple model
    if advanced:
        veg_model = 2  # -advanced T is shorthand for model 2
    elif vegetation_model:
        # Accept numeric string or integer
        if isinstance(vegetation_model, str) and vegetation_model.isnumeric():
            veg_model = int(vegetation_model)
        else:
            veg_model = vegetation_model

        # Validate model number
        if veg_model not in [1, 2]:
            print(f'Vegetation model {veg_model} is not supported. Use 1 (simple) or 2 (advanced). Exiting.')
            sys.exit()

    # Model 2 (advanced): Use efficient track-based processing
    if veg_model == 2:
        print(f"Using efficient model 2 processing with saved track data")
        
        # Get resolved frequency
        fr_list = qp.get_vwc_frequency(station, extension, fr)
        if len(fr_list) > 1:
            print("Error: vwc_hourly can only process one frequency at a time.")
            sys.exit()
        resolved_fr = fr_list[0]
        
        print(f"\n=== Generating all {bin_hours} VWC offsets using saved track data ===")
        
        # Process each offset efficiently using saved track data
        success_count = 0
        for offset in range(bin_hours):
            print(f"Processing offset {offset}/{bin_hours-1} ({offset:02d}-{(offset+bin_hours)%24:02d}h bins)")
            
            success = clara_efficient_hourly_vwc(station, year, resolved_fr, 
                                                bin_hours, offset, minvalperbin, subdir)
            if success:
                success_count += 1
            else:
                print(f"  Failed to generate VWC for offset {offset}")
        
        if success_count == 0:
            print("Error: No VWC files generated. Run 'vwc' with -save_tracks T first.")
            sys.exit()
        
        print(f"Successfully generated {success_count}/{bin_hours} VWC offset files using efficient processing")
        
        # Skip the traditional processing and go to combination
        resolved_fr = resolved_fr  # Already set above
        
    else:
        # Simple model: Use traditional approach
        print(f"Using traditional processing for simple vegetation model")
        
        # First run daily VWC for comparison plotting - FORCE plots off
        print(f"\n=== Generating Daily VWC for comparison ===")
        vwc(station=station, year=year, year_end=year_end, fr=fr, plt=False, screenstats=False,
            bin_hours=24, minvalperbin=minvalperbin, bin_offset=0,
            min_req_pts_track=min_req_pts_track, polyorder=polyorder,
            snow_filter=snow_filter, subdir=subdir, tmin=tmin, tmax=tmax,
            warning_value=warning_value, auto_removal=auto_removal, hires_figs=hires_figs,
            advanced=advanced, vegetation_model=veg_model, extension=extension)
        
        # Process each offset - FORCE plots off for all batch processing
        for offset in range(bin_hours):
            print(f"\n=== Processing offset {offset}/{bin_hours-1} ({offset:02d}-{(offset+bin_hours)%24:02d}h bins) ===")
            
            # Call vwc with plots FORCED off for batch processing
            vwc(station=station, year=year, year_end=year_end, fr=fr, plt=False, screenstats=False,
                bin_hours=bin_hours, minvalperbin=minvalperbin, bin_offset=offset,
                min_req_pts_track=min_req_pts_track, polyorder=polyorder,
                snow_filter=snow_filter, subdir=subdir, tmin=tmin, tmax=tmax,
                warning_value=warning_value, auto_removal=auto_removal, hires_figs=hires_figs,
                advanced=advanced, vegetation_model=veg_model, extension=extension)
        
        # Get parameters that were resolved during first vwc call for file combination
        fr_list = qp.get_vwc_frequency(station, extension, fr)
        if len(fr_list) > 1:
            print("Error: vwc_hourly can only process one frequency at a time.")
            sys.exit()
        resolved_fr = fr_list[0]
    
    # Combine all VWC offset files
    print(f"\n=== Combining all {bin_hours} VWC offset files ===")
    combined_vwc = combine_vwc_files_to_hourly(station, resolved_fr, bin_hours, subdir, extension)
    
    if len(combined_vwc) > 0:
        print(f"\nSuccess! Generated {len(combined_vwc)} hourly rolling VWC measurements")
        if resolved_fr == 20:
            freq_suffix = "_L2"
        elif resolved_fr == 1:
            freq_suffix = "_L1"
        elif resolved_fr == 5:
            freq_suffix = "_L5"
        else:
            freq_suffix = f"_L{resolved_fr}"
        
        final_file = f"{station}_vwc{freq_suffix}_rolling{bin_hours}hr.txt"
        print(f"Output file: $REFL_CODE/Files/{subdir if subdir else station}/{final_file}")
        
        print(f"\nWARNING: vwc_hourly is experimental code and currently under development.")
        print(f"Please see https://github.com/kristinemlarson/gnssrefl/issues/358 for the latest discussion.")
        
        # Generate comparison plot if requested
        if plt:
            print(f"\n=== Generating VWC Comparison Plot ===")
            plot_hourly_vs_daily_vwc(station, resolved_fr, bin_hours, subdir, extension, year, year_end)
    else:
        print("\nError: No VWC measurements generated from any offset")
        sys.exit()


def main_hourly():
    """CLI entry point for vwc_hourly command"""
    args = parse_arguments_hourly()
    vwc_hourly(**args)


def main():
    """Alternative entry point (for compatibility)"""
    main_hourly()


def load_and_rebin_track_data(station, year, subdir, fr, bin_hours, bin_offset, minvalperbin):
    """
    Load saved individual track data and re-bin into specified time windows
    
    This function provides efficient re-binning of Clara model results without
    reprocessing the vegetation corrections. It reads all track files into a
    single data structure then performs time binning.
    
    Parameters
    ----------
    station : str
        4-character station name
    year : int
        Analysis year
    subdir : str
        Subdirectory for track files
    fr : int
        Frequency code (20 for L2C, etc.)
    bin_hours : int
        Time bin size in hours
    bin_offset : int
        Bin timing offset in hours
    minvalperbin : int
        Minimum tracks required per time bin
        
    Returns
    -------
    binned_mjd : list
        MJD values for time bins
    binned_vwc : list  
        Aggregated VWC values for time bins
    binned_binstarts : list
        Bin start hours for each time bin
    """
    import os
    import numpy as np
    import glob
    
    # Find track data directory
    xdir = os.environ['REFL_CODE']
    if subdir:
        track_dir = f'{xdir}/Files/{subdir}/individual_tracks'
    else:
        track_dir = f'{xdir}/Files/{station}/individual_tracks'
    
    if not os.path.exists(track_dir):
        print(f'No saved track data found in {track_dir}')
        print('Run vwc with -save_tracks T first to generate individual track files')
        return [], [], []
    
    # Load all track files for this station/year/frequency
    freq_suffix = qp.get_temporal_suffix(fr)
    pattern = f'{track_dir}/{station}_track_sat*_quad*_{year}{freq_suffix}.txt'
    track_files = glob.glob(pattern)
    
    if not track_files:
        print(f'No track files found matching pattern: {pattern}')
        print('Run vwc with -save_tracks T first to generate individual track files')
        return [], [], []
    
    print(f'Loading {len(track_files)} saved track files for efficient re-binning...')
    
    # Load ALL track data into single arrays
    all_data = []
    for track_file in track_files:
        try:
            # Load track data (skip header lines starting with %)
            data = np.loadtxt(track_file, comments='%')
            if len(data.shape) == 1:
                data = data.reshape(1, -1)
            all_data.append(data)
        except Exception as e:
            print(f'Warning: Could not load track file {track_file}: {e}')
            continue
    
    if not all_data:
        print('No valid track data loaded')
        return [], [], []
    
    # Combine all track data into single array
    combined_data = np.vstack(all_data)
    print(f'Loaded {len(combined_data)} individual track observations from saved files')
    
    # Extract columns: Year(0), DOY(1), Hour(2), MJD(3), VWC(16)
    years = combined_data[:, 0]
    doys = combined_data[:, 1] 
    hours = combined_data[:, 2]
    mjds = combined_data[:, 3]
    vwc = combined_data[:, 16] / 100.0  # Convert VWC from percentage to fraction (0-1)
    
    # Now perform time binning
    return rebin_track_vwc_data(years, doys, hours, mjds, vwc, bin_hours, bin_offset, minvalperbin)


def rebin_track_vwc_data(years, doys, hours, mjds, vwc, bin_hours, bin_offset, minvalperbin):
    """
    Re-bin individual track VWC data into specified time windows
    
    Parameters
    ----------
    years, doys, hours, mjds, vwc : numpy.ndarray
        Individual track observation data
    bin_hours : int
        Time bin size in hours
    bin_offset : int
        Bin timing offset in hours
    minvalperbin : int
        Minimum tracks required per time bin
        
    Returns
    -------
    binned_mjd : list
        MJD values for time bins
    binned_vwc : list
        Aggregated VWC values for time bins  
    binned_binstarts : list
        Bin start hours for each time bin
    """
    import numpy as np
    
    # Generate time bins covering the data range
    unique_days = np.unique(np.floor(mjds))
    
    binned_mjd = []
    binned_vwc = []
    binned_binstarts = []
    
    # Process each day with time bins
    for day_mjd in unique_days:
        # Convert MJD to datetime then extract year and DOY
        dt = g.mjd_to_datetime(day_mjd)
        year_val = dt.year
        doy_val = dt.timetuple().tm_yday
        
        # Generate time bins for this day
        for offset in range(0, 24, bin_hours):
            actual_bin_start = (offset + bin_offset) % 24
            bin_end = (actual_bin_start + bin_hours) % 24
            
            # Select tracks that fall within this time bin
            if bin_end <= actual_bin_start:  # Crosses midnight
                day_mask = (np.floor(mjds) == day_mjd) | (np.floor(mjds) == day_mjd + 1)
                time_mask = day_mask & ((hours >= actual_bin_start) | (hours < bin_end))
            else:
                day_mask = np.floor(mjds) == day_mjd
                time_mask = day_mask & (hours >= actual_bin_start) & (hours < bin_end)
            
            # Get VWC values for this time bin
            bin_vwc = vwc[time_mask]
            
            # Apply minimum count threshold
            if len(bin_vwc) >= minvalperbin:
                binned_mjd.append(day_mjd)
                binned_vwc.append(np.mean(bin_vwc))
                binned_binstarts.append(actual_bin_start)
    
    print(f'Generated {len(binned_mjd)} time-binned VWC estimates from track data')
    return binned_mjd, binned_vwc, binned_binstarts


def clara_efficient_hourly_vwc(station, year, fr, bin_hours, bin_offset, minvalperbin, subdir=''):
    """
    Efficient hourly VWC generation using saved Clara model track data
    
    This function provides a fast alternative to full vegetation model reprocessing
    for hourly VWC generation. It requires that individual track files have been
    previously saved using -save_tracks T.
    
    Parameters
    ----------
    station : str
        4-character station name
    year : int
        Analysis year
    fr : int
        Frequency code (20 for L2C, etc.)
    bin_hours : int
        Time bin size in hours
    bin_offset : int
        Bin timing offset in hours
    minvalperbin : int
        Minimum tracks required per time bin
    subdir : str
        Subdirectory for output files
        
    Returns
    -------
    success : bool
        True if VWC file was successfully generated
    """
    # Load and re-bin saved track data
    binned_mjd, binned_vwc, binned_binstarts = load_and_rebin_track_data(
        station, year, subdir, fr, bin_hours, bin_offset, minvalperbin)
    
    if not binned_mjd:
        return False
    
    # Write VWC output file
    avc.write_vwc_output(station, binned_mjd, binned_vwc, year, subdir, 
                         bin_hours, bin_offset, fr, binned_binstarts)
    
    print(f'Successfully generated efficient VWC output with {len(binned_mjd)} time bins')
    return True


if __name__ == "__main__":
    main()