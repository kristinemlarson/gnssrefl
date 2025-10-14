"""
Simple vegetation correction model for VWC estimation

This module implements the simple vegetation correction algorithm based on
Clara Chew's original Matlab code (write_vegcorrect_smc.m) used in PBO H2O.

The simple model uses a polynomial relationship between normalized amplitude
and vegetation effects to correct phase measurements before converting to VWC.
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from datetime import datetime
from pathlib import Path

import gnssrefl.gps as g
import gnssrefl.gnssir_v2 as gnssir
import gnssrefl.phase_functions as qp
from gnssrefl.utils import FileManagement

xdir = os.environ['REFL_CODE']


def simple_vegetation_filter(station, year, vxyz, tmin, tmax, subdir='',
                             bin_hours=24, bin_offset=0, plt2screen=True, fr=20,
                             level_doys=None, polyorder=-99, circles=False,
                             hires_figs=False, extension='', year_end=None, minvalperbin=10):
    """
    Apply simple vegetation correction model to phase data and compute VWC

    This is the original/simple vegetation correction model that uses a polynomial
    relationship between normalized amplitude and phase corrections.

    Parameters
    ----------
    station : str
        4-char GNSS station name
    year : int
        Calendar year (start)
    vxyz : numpy array
        Track-level phase observations (16 columns)
        Columns documented in vwc_cl.py lines 261-276
    tmin : float
        Min soil moisture value based on soil texture
    tmax : float
        Max soil moisture value based on soil texture
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
    level_doys : list of int, optional
        [start_doy, end_doy] defining the dry season for baseline calculation
    polyorder : int
        Override for polynomial order used in leveling (default: -99, auto)
    circles : bool
        Final plot using circles instead of line (default: False)
    hires_figs : bool
        Whether to make eps instead of png files (default: False)
    extension : str
        Extension used for json analysis file (default: '')
    year_end : int, optional
        Last year for multi-year analysis (default: same as year)
    minvalperbin : int, optional
        Minimum observations required per time bin (default: 10)

    Returns
    -------
    None (writes VWC output file directly)
    """

    print('>>>>>>>>>>> Simple Vegetation Model <<<<<<<<<<<<')

    if not year_end:
        year_end = year

    # Set default level_doys if not provided
    if level_doys is None:
        level_doys = [152, 244]  # Default summer dry season for northern hemisphere
        print(f'Using default level_doys: {level_doys}')
    else:
        print(f'Using provided level_doys: {level_doys}')

    # Calculate averaged phase from vxyz in memory
    avg_phase = qp.calculate_avg_phase(vxyz, year, year_end, bin_hours, bin_offset, minvalperbin)

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

    # Simple vegetation correction algorithm (from Clara's original code)
    residval = 2  # Residual value for baseline

    # Vegetation weight calculation (4th order polynomial)
    wetwt = (10.6 * np.power(smamp, 4) -
             34.9 * np.power(smamp, 3) +
             41.8 * np.power(smamp, 2) -
             22.6 * smamp + 5.24)

    # Phase correction based on smoothed amplitude
    delphi = (smamp - 1) * 50.25 / 1.48
    newph = ph - delphi

    # Convert to VWC
    vwc = 100 * tmin + 1.48 * (ph - residval)
    newvwc = 100 * tmin + 1.48 * (newph - residval)

    # Apply baseline leveling using unified function
    nv, leveling_info = qp.apply_vwc_leveling(
        newvwc, tmin,
        method='polynomial',
        years=years, doys=doys, level_doys=level_doys, polyorder=polyorder,
        station=station, plot_debug=plt2screen, plt2screen=plt2screen,
        subdir=subdir, fr=fr, bin_hours=bin_hours, bin_offset=bin_offset
    )

    # Extract nodes for plotting (polynomial method returns nodes)
    nodes = leveling_info.get('nodes', np.empty(shape=[0, 3]))

    # Create datetime objects for plotting
    if is_subdaily:
        from datetime import timedelta
        t_datetime = []
        for yr, d, h in zip(years, doys, bin_start_hours):
            base_dt = datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j')
            dt_with_hours = base_dt + timedelta(hours=int(h))
            t_datetime.append(dt_with_hours)
    else:
        t_datetime = [datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j')
                     for yr, d in zip(years, doys)]

    # Create diagnostic plot: phase before/after vegetation correction
    plt.figure(figsize=(10, 10))
    plt.subplots_adjust(hspace=0.2)
    plt.suptitle(f'Station: {station}', size=16)

    # Subplot 1: Phase with and without vegetation correction
    ax = plt.subplot(2, 1, 1)
    ax.plot(t_datetime, ph, 'b-', label='original')
    ax.plot(t_datetime, newph, 'r-', label='vegcorrected')
    ax.set_title('With and Without Vegetation Correction')
    ax.set_ylabel('phase (degrees)')
    ax.legend(loc='best')
    ax.grid()
    plt.gcf().autofmt_xdate()

    # Check if baseline leveling was successful
    if len(nodes) == 0:
        print('No summer nodes found. Exiting.')
        if plt2screen:
            plt.show()
        else:
            plt.close('all')
        sys.exit()

    # Prepare node data for plotting
    st = nodes[:, 0] + nodes[:, 1]/365.25
    st_datetime = [datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j')
                   for yr, d in zip(nodes[:, 0], nodes[:, 1])]
    sp = nodes[:, 2]
    print(nodes)

    # Reconstruct the polynomial level for plotting
    polyordernum = len(nodes) - 1
    if polyorder >= 0:
        polyordernum = polyorder
    anothermodel = np.polyfit(st, sp, polyordernum)
    new_level = np.polyval(anothermodel, t)

    # Subplot 2: VWC with leveling nodes and polynomial fit
    ax = plt.subplot(2, 1, 2)
    ax.plot(t_datetime, newvwc, 'b-', label='new vwc')
    ax.plot(st_datetime, sp, 'ro', label='nodes')
    ax.plot(t_datetime, new_level, 'r-', label='level')
    ax.set_ylabel('VWC')
    ax.set_title('Volumetric Water Content')
    ax.legend(loc='best')
    ax.grid()
    plt.gcf().autofmt_xdate()

    # Save diagnostic plot
    outdir = Path(xdir) / 'Files' / subdir
    suffix = qp.get_temporal_suffix(fr, bin_hours, bin_offset)
    if hires_figs:
        plot_path = f'{outdir}/{station}_phase_vwc_result{suffix}.eps'
    else:
        plot_path = f'{outdir}/{station}_phase_vwc_result{suffix}.png'
    print(f"Saving to {plot_path}")
    plt.savefig(plot_path)

    # Create final VWC plot
    if hires_figs:
        plot_path = f'{outdir}/{station}_vol_soil_moisture{suffix}.eps'
    else:
        plot_path = f'{outdir}/{station}_vol_soil_moisture{suffix}.png'

    qp.vwc_plot(station, t_datetime, nv, plot_path, circles, plt2screen)

    if plt2screen:
        plt.show()
    else:
        plt.close('all')

    # Write VWC output file
    file_manager = FileManagement(station, 'volumetric_water_content', extension=extension)
    base_vwcfile = file_manager.get_file_path()

    vwcfile = base_vwcfile.parent / f"{station}_vwc{suffix}.txt"
    print('VWC results being written to ', vwcfile)

    with open(vwcfile, 'w') as w:
        N = len(nv)
        freq_map = {1: "L1", 2: "L2C", 20: "L2C", 5: "L5"}
        freq_name = freq_map.get(fr, f"Frequency {fr}")

        w.write("% Soil Moisture Results for GNSS Station {0:4s} \n".format(station))
        w.write("% Frequency used: {0} \n".format(freq_name))
        w.write("% {0:s} \n".format('https://github.com/kristinemlarson/gnssrefl'))

        if is_subdaily:
            w.write(f"% Subdaily VWC with {bin_hours}-hour bins (offset: {bin_offset}h)\n")
            w.write(qp.get_bin_schedule_info(bin_hours, bin_offset) + "\n")
            w.write("% FracYr    Year   DOY   VWC Month Day BinStart \n")
        else:
            w.write("% FracYr    Year   DOY   VWC Month Day \n")

        for iw in range(0, N):
            fdate = t[iw]
            myyear = years[iw]
            mm = months[iw]
            dd = days[iw]
            mydoy = doys[iw]
            watercontent = nv[iw]

            # Only write positive, reasonable soil moisture values
            if watercontent > 0 and watercontent < 0.5:
                if is_subdaily:
                    bin_start = bin_start_hours[iw]
                    w.write(f"{fdate:10.4f} {myyear:4.0f} {mydoy:4.0f} {watercontent:8.3f} "
                           f"{mm:3.0f} {dd:3.0f} {bin_start:3.0f} \n")
                else:
                    w.write(f"{fdate:10.4f} {myyear:4.0f} {mydoy:4.0f} {watercontent:8.3f} "
                           f"{mm:3.0f} {dd:3.0f} \n")
