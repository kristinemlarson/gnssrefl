"""
Simple vegetation correction model for VWC estimation. The default and only option until October 2025.

"""

import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import gnssrefl.phase_functions as qp
import gnssrefl.gps as g

xdir = os.environ['REFL_CODE']

def simple_vegetation_filter(station, vxyz, subdir='',
                             bin_hours=24, bin_offset=0, plt2screen=True, fr=20,
                             minvalperbin=10):
    """
    Simple vegetation model (model 1)

    This function applies the simple vegetation correction filter to a vxyz array input. This was the default and
    only available vegetation correction until October 2025.

    Parameters
    ----------
    station : str
        4-char GNSS station name
    vxyz : numpy array
        Track-level phase observations (16 columns)
    subdir : str
        Subdirectory for file organization (default: '')
    bin_hours : int
        Time bin size for subdaily support (default: 24)
    bin_offset : int
        Bin timing offset for subdaily support (default: 0)
    plt2screen : bool
        Whether plots come to the screen (default: True)
    fr : int
        Frequency code (1=L1, 5=L5, 20=L2C, default: 20)
    minvalperbin : int, optional
        Minimum observations required per time bin (default: 10)

    Returns
    -------
    dict
        Dictionary containing:
        - 'mjd': list of Modified Julian Day values
        - 'vwc': numpy array of VWC values (percentage units, not leveled)
        - 'datetime': list of datetime objects for plotting
        - 'bin_starts': numpy array of bin start hours (subdaily) or empty list (daily)
    """

    print('=== Simple Vegetation Model (model 1) ===')

    # Calculate averaged phase from vxyz in memory
    avg_phase = qp.calculate_avg_phase(vxyz, bin_hours, bin_offset, minvalperbin)

    if len(avg_phase) == 0:
        print('No averaged phase data could be calculated - perhaps minvalperbin is too stringent')
        sys.exit()

    # Auto-detect daily vs subdaily based on number of columns
    num_columns = avg_phase.shape[1]
    if num_columns == 9:
        is_subdaily = True
        print(f'Processing {len(avg_phase)} subdaily measurements')
    elif num_columns == 8:
        is_subdaily = False
        print(f'Processing {len(avg_phase)} daily measurements')
    else:
        print(f'Unexpected avg_phase format: {num_columns} columns. Expected 8 (daily) or 9 (subdaily)')
        sys.exit()

    # Extract columns from avg_phase
    # Columns: [Year, DOY, Phase, PhaseSig, NormAmp, FracYear, Month, Day, [BinStart]]
    years = avg_phase[:, 0]
    doys = avg_phase[:, 1]
    ph = avg_phase[:, 2]
    phsig = avg_phase[:, 3]
    amp = avg_phase[:, 4]
    months = avg_phase[:, 6]
    days = avg_phase[:, 7]

    if is_subdaily:
        bin_start_hours = avg_phase[:, 8]

    # Calculate fractional year
    t = years + doys/365.25
    tspan = t[-1] - t[0]
    print('Timespan in years: ', np.round(tspan, 3))

    # Apply 30-day smoothing to amplitude
    window_len = 30
    s = np.r_[amp[window_len - 1:0:-1], amp, amp[-2:-window_len - 1:-1]]
    w = np.ones(window_len, 'd')
    y = np.convolve(w / w.sum(), s, mode='valid')
    y0 = int(window_len / 2 - 1)
    y1 = -int(window_len / 2)
    smamp = y[y0:y1]

    residval = 2  # Residual value for baseline

    # Vegetation weight calculation (4th order polynomial)
    wetwt = (10.6 * np.power(smamp, 4) -
             34.9 * np.power(smamp, 3) +
             41.8 * np.power(smamp, 2) -
             22.6 * smamp + 5.24)

    # Phase correction based on smoothed amplitude
    delphi = (smamp - 1) * 50.25 / 1.48
    newph = ph - delphi

    # Convert to VWC (percentage units, baseline = 2 degrees)
    # Note: This is NOT leveled yet - caller will handle leveling
    newvwc = 1.48 * (newph - residval)

    # Convert to MJD and datetime for unified format
    mjd_values = []
    t_datetime = []

    if is_subdaily:
        for yr, d, h in zip(years, doys, bin_start_hours):
            # Compute MJD from year/doy + fractional hours
            mjd = g.ydoy2mjd(int(yr), int(d)) + int(h) / 24.0
            mjd_values.append(mjd)
            # Create datetime for plotting
            base_dt = datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j')
            dt_with_hours = base_dt + timedelta(hours=int(h))
            t_datetime.append(dt_with_hours)
    else:
        for yr, d in zip(years, doys):
            # Compute MJD from year/doy (daily)
            mjd = g.ydoy2mjd(int(yr), int(d))
            mjd_values.append(mjd)
            # Create datetime for plotting
            t_datetime.append(datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j'))

    # Create diagnostic plot: phase before/after vegetation correction
    plt.figure(figsize=(10, 6))
    plt.suptitle(f'Station: {station} - Vegetation Correction', size=16)

    # Plot: Phase with and without vegetation correction
    ax = plt.gca()
    ax.plot(t_datetime, ph, 'b-', label='original phase')
    ax.plot(t_datetime, newph, 'r-', label='vegetation-corrected phase')
    ax.set_title('Phase Before and After Vegetation Correction')
    ax.set_ylabel('phase (degrees)')
    ax.legend(loc='best')
    ax.grid()
    plt.gcf().autofmt_xdate()

    # Save diagnostic plot
    outdir = Path(xdir) / 'Files' / subdir
    suffix = qp.get_temporal_suffix(fr, bin_hours, bin_offset)
    plot_path = f'{outdir}/{station}_phase_vegcorr{suffix}.png'
    print(f"Saving vegetation correction diagnostic plot to {plot_path}")
    plt.savefig(plot_path)

    # Don't call plt.show() here - let all figures accumulate and display together at the end
    if not plt2screen:
        plt.close('all')

    # Return unified MJD format (matches advanced model)
    return {
        'mjd': mjd_values,
        'vwc': newvwc,  # Percentage units, not leveled
        'datetime': t_datetime,
        'bin_starts': bin_start_hours if is_subdaily else []
    }
