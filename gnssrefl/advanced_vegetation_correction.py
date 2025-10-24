"""
Advanced vegetation correction model for VWC estimation.

Reference: DOI 10.1007/s10291-015-0462-4

Ported to gnssrefl from original MATLAB in October 2025.
"""

import scipy
import scipy.signal
import scipy.spatial
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from pathlib import Path

import gnssrefl.sd_libs as sd
import gnssrefl.gps as g
import gnssrefl.phase_functions as qp

def advanced_vegetation_filter(station, vxyz, subdir='',
                               bin_hours=24, bin_offset=0, pltit=True, fr=20, minvalperbin=10, save_tracks=False):
    """
    Advanced vegetation model (model 2)

    This function applies the advanced vegetation correction filter to a vxyz array input.

    Parameters
    ----------
    station : str
        4-char GNSS station name
    vxyz : numpy array
        Full track-level data from vwc (16 columns)
    subdir : str
        Subdirectory for file organization (default: '')
    bin_hours : int
        Time bin size for future subdaily support (default: 24)
    bin_offset : int
        Bin timing offset for future subdaily support (default: 0)
    pltit : bool
        Whether plots come to the screen
    fr : int
        Frequency code (1=L1, 5=L5, 20=L2C, default: 20)
    minvalperbin : int
        Minimum values required per time bin (default: 10)
    save_tracks : bool
        Save individual track VWC data to files (default: False)

    Returns
    -------
    dict
        Dictionary containing:
        - 'mjd': list of Modified Julian Day values
        - 'vwc': list of VWC values (percentage units, not leveled)
        - 'datetime': list of datetime objects for plotting
        - 'bin_starts': list of bin start hours (subdaily only) or empty list
    """
    
    print('=== Advanced Vegetation Model (model 2) ===')
    print(f'Processing {len(vxyz)} track observations for station {station}')

    if fr != 20:
        print(f"\nWarning: The advanced vegetation model was developed and tested only with L2C data.")

    # Clara's default parameters (from original MATLAB code)
    remoutli = 1        # Remove outliers? 0=no, 1=yes
    baseperc = 0.2      # Amplitude normalization percentage (top 20%)
    zphival = 0.15      # Fraction of values for phase zeroing
    ampvarday = 5       # Days for variance calculation
    ampvarlimit = 5     # Variance threshold for amplitude outliers
    acc_rhdrift = 1     # Apply RH drift correction

    # Savgol filtering parameters
    men = 20            # Points for padding calculation
    sgolnum = 99        # Savgol filter length
    sgolply = 2         # Savgol polynomial order
    padlen = 1000       # Padding length

    # Step 1: Normalize and process the track-level data
    tracks, metrics_all, vegmast = norm_zero_vxyz(station, vxyz, remoutli, acc_rhdrift,
                                                  baseperc, zphival, ampvarday, ampvarlimit)

    # Step 2: Apply vegetation filter to compute soil moisture
    final_mjd, final_vwc, final_binstarts = apply_vegetation_model(station, vxyz, metrics_all, tracks,
                                                  sgolnum, sgolply, padlen, pltit,
                                                  fr, bin_hours, bin_offset, subdir, minvalperbin, save_tracks)

    if len(final_mjd) == 0:
        print('No vegetation-corrected soil moisture estimates could be computed')
        return {
            'mjd': [],
            'vwc': [],
            'datetime': [],
            'bin_starts': []
        }

    # Convert MJD to datetime for plotting
    datetime_array = sd.mjd_to_obstimes(np.array(final_mjd))

    print(f'Advanced vegetation model (model 2) completed for {station}')

    # Return data structure for caller to handle leveling and file writing
    return {
        'mjd': final_mjd,
        'vwc': final_vwc,  # Percentage units, not yet leveled
        'datetime': datetime_array.tolist(),
        'bin_starts': final_binstarts
    }


def norm_zero_vxyz(station, vxyz, remoutli, acc_rhdrift, baseperc, zphival, 
                   ampvarday, ampvarlimit):
    """
    Normalize metrics and remove outliers from vxyz data
    
    This processes the full track-level data from vwc to prepare it for the KNN lookup.
    
    Parameters
    ----------
    station : str
        Station name
    vxyz : numpy array
        Full track data (16 columns)
    remoutli : int
        Remove outliers flag
    acc_rhdrift : int
        Apply RH drift correction
    baseperc : float
        Percentage for amplitude normalization  
    zphival : float
        Fraction for phase zeroing
    ampvarday : int
        Days for variance calculation
    ampvarlimit : float
        Amplitude variance threshold
        
    Returns
    -------
    tracks : numpy array
        Unique satellite/quadrant combinations
    metrics_all : numpy array
        Normalized metrics [D_amplsp, D_amp, D_phi, D_RH]
    vegmast : numpy array
        Vegetation mask
    """
    
    print('=== Normalizing track data ===')
    
    phivarlimit = 150  # Phase variance limit
    
    # Extract columns from vxyz array
    # vxyz columns: [year, doy, phase, azim, sat, rh, norm_ampLSP, norm_ampLS, hour, 
    #                ampLSP, ampLS, ap_rh, quad, delRH, vegMask, mjd]
    year = vxyz[:, 0]
    doy = vxyz[:, 1]
    phi = vxyz[:, 2]        # Phase
    azimuth = vxyz[:, 3]    # Azimuth
    smat = vxyz[:, 4]       # PRN satellite
    rh = vxyz[:, 5]         # Reflector height
    # Skip normalized values (columns 6,7) - we'll recompute
    hour = vxyz[:, 8]       # Hour
    ampLSP = vxyz[:, 9]     # LSP amplitude
    amp2 = vxyz[:, 10]      # LS amplitude
    apriori = vxyz[:, 11]   # Apriori RH
    qmat = vxyz[:, 12]      # Quadrants
    delRH = vxyz[:, 13]     # Delta RH (pre-computed)
    # vegMask in column 14
    mjd = vxyz[:, 15]       # Modified Julian Day
    
    # Get unique satellite/quadrant tracks
    sqmat = vxyz[:, [4, 12]]  # [satellite, quadrant]
    tracks = np.unique(sqmat, axis=0)
    numtracks, nn = tracks.shape
    
    print(f'Found {numtracks} unique satellite/quadrant tracks')
    
    # Initialize output arrays
    N = len(doy)
    D_amplsp = np.zeros((N, 1))
    D_RH = np.zeros((N, 1))
    D_amp = np.zeros((N, 1))
    D_phi = np.zeros((N, 1))
    vegmast = np.ones((N, 1))  # Vegetation mask
    
    # Process each track
    for i in range(numtracks):
        thequad = int(tracks[i, 1])
        thesat = int(tracks[i, 0])
        
        # Get indices for this satellite/quadrant combination
        ii = (qmat == thequad) & (smat == thesat)
        Nvals = len(rh[ii])
        
        if Nvals < 10:  # Skip tracks with too few points
            continue

        # Extract data for this track
        s_refhgt = rh[ii].copy()
        aprioris = apriori[ii]
        amps = amp2[ii].copy()
        amplsp = ampLSP[ii].copy()
        phis = phi[ii].copy()
        doys = doy[ii]

        # ===== Reflector Height Processing =====
        # Remove outliers in RH (> 15cm from apriori)
        bad = np.abs(aprioris - s_refhgt) >= 0.15
        good = np.abs(aprioris - s_refhgt) < 0.15

        if np.any(bad) and np.any(good):
            s_refhgt[bad] = np.interp(doys[bad], doys[good], s_refhgt[good])

        # Calculate delta RH
        s_refhgt = s_refhgt.reshape(Nvals, 1)
        D_RH[ii] = aprioris.reshape(Nvals, 1) - s_refhgt

        # Apply RH drift correction
        medrh = np.mean(aprioris) - np.median(s_refhgt.flatten())
        if acc_rhdrift == 1:
            smrh = np.zeros((Nvals, 1)) + medrh
            D_RH[ii] = D_RH[ii] - smrh

        # Print quality metrics for this track
        Ngood = np.sum(good)
        Nbad = np.sum(bad)
        offs = np.round(np.mean(aprioris) - np.mean(s_refhgt.flatten()), 3)
        print(f'quad {thequad} sat {thesat}  Offset {offs:6.3f} m  good {Ngood:4d}  bad {Nbad:4d}')
        
        # ===== LSP Amplitude Processing =====
        # Find outliers using rolling variance
        if len(amplsp) >= ampvarday:
            rollingV = np.var(rolling_window(amplsp, ampvarday), axis=-1)
            bad = rollingV >= ampvarlimit
            good = rollingV < ampvarlimit
            
            # Interpolate across bad points
            if np.any(bad) and np.any(good):
                amplsp[bad] = np.interp(doys[bad], doys[good], amplsp[good])
        
        # Normalize LSP amplitude
        Namp = len(amplsp)
        numx = int(np.round(Namp * baseperc))
        kk = np.argsort(amplsp)
        ascending = amplsp[kk]
        driestlsp = np.mean(ascending[(Namp-numx):Namp])  # Top 20% average
        
        if driestlsp > 0:
            delamplsp = amplsp / driestlsp
            delamplsp[delamplsp > 1] = 1  # Cap at 1
            D_amplsp[ii] = delamplsp.reshape(Namp, 1)
        
        # ===== LS Amplitude Processing =====
        # Find outliers using rolling variance
        if len(amps) >= ampvarday:
            rollingV = np.var(rolling_window(amps, ampvarday), axis=-1)
            bad = rollingV >= ampvarlimit
            good = rollingV < ampvarlimit
            
            # Interpolate across bad points
            if np.any(bad) and np.any(good):
                amps[bad] = np.interp(doys[bad], doys[good], amps[good])
        
        # Normalize LS amplitude
        kk = np.argsort(amps)
        ascending = amps[kk]
        driestamp = np.mean(ascending[(Namp-numx):Namp])  # Top 20% average
        
        if driestamp > 0:
            delamp = amps / driestamp
            delamp[delamp > 1] = 1  # Cap at 1
            D_amp[ii] = delamp.reshape(Namp, 1)
        
        # ===== Phase Processing =====
        s_phi = phis.copy()
        
        # Zero phase relative to minimum values
        numvals = int(np.ceil(zphival * Namp))
        ss_phi = np.sort(s_phi)
        minphi = np.median(ss_phi[0:numvals])
        
        delphi = s_phi.reshape(Namp, 1) - minphi
        D_phi[ii] = delphi
    
    # Combine results
    metrics_all = np.hstack((D_amplsp, D_amp, D_phi, D_RH))
    
    return tracks, metrics_all, vegmast


def apply_vegetation_model(station, vxyz, normmet, tracks, sgolnum, sgolply,
                          padlen, pltit, fr, bin_hours, bin_offset, subdir, minvalperbin, save_tracks=False):
    """
    Apply Clara's vegetation filter to compute soil moisture

    Parameters
    ----------
    station : str
        Station name
    vxyz : numpy array
        Original vwc data
    normmet : numpy array
        Normalized metrics from norm_zero_vxyz
    tracks : numpy array
        Satellite/quadrant combinations
    sgolnum : int
        Savgol filter length
    sgolply : int
        Savgol polynomial order
    padlen : int
        Padding length
    pltit : bool
        Show plots
    fr : int
        Frequency code
    bin_hours : int
        Time bin size in hours
    bin_offset : int
        Bin timing offset in hours
    subdir : str
        Subdirectory for output
    minvalperbin : int
        Minimum values required per time bin
    save_tracks : bool
        Save individual track VWC data to files

    Returns
    -------
    final_mjd : list
        MJD values for time-binned averages
    final_vwc : list
        VWC values for time-binned averages (percentage units, not leveled)
    final_binstarts : list
        Bin start hours for subdaily data (empty for daily)
    """
    
    print('=== Applying vegetation model ===')
    
    # Extract normalized metrics
    D_amplsp = normmet[:, 0]
    D_amp = normmet[:, 1] 
    D_phi = normmet[:, 2]
    D_RH = normmet[:, 3]
    
    # Extract original data
    year = vxyz[:, 0]
    doy = vxyz[:, 1]
    azim = vxyz[:, 3]
    hour = vxyz[:, 8]
    q = vxyz[:, 12]
    sat = vxyz[:, 4]
    mjd = vxyz[:, 15]
    
    Nobs = len(vxyz)
    svwc = np.zeros((Nobs, 1))  # Soil moisture output
    
    # Load Clara's model
    amp_lsp_model, amp_dsnr_model, delta_heff_model, veg_correction_model, slopes_model = load_clara_model()
    ref_points = np.column_stack([amp_lsp_model, amp_dsnr_model, delta_heff_model])

    # Build KD-tree once for all tracks for efficient KNN search
    print(f'Building KD-tree for {len(ref_points)} model points...')
    kdtree = scipy.spatial.cKDTree(ref_points)

    min_number_points = 90  # Minimum points per track
    men = 20    # Points for padding calculation

    Nt, nc = tracks.shape
    tracks_processed = 0  # Counter for tracks that meet minimum threshold

    # Process each track
    for i in range(Nt):
        thissat = int(tracks[i, 0])
        thisquad = int(tracks[i, 1])
        ii = (thissat == sat) & (thisquad == q)
        Ntrack = len(sat[ii])

        if Ntrack > min_number_points:
            tracks_processed += 1

            # Pad and smooth the metrics
            paddedAmplsp = padClara(D_amplsp[ii], Ntrack, men, padlen)
            paddedAmp = padClara(D_amp[ii], Ntrack, men, padlen)
            paddedRH = padClara(D_RH[ii], Ntrack, men, padlen)

            # Apply Savgol smoothing
            s1 = scipy.signal.savgol_filter(paddedAmplsp.flatten(), sgolnum, sgolply)
            s2 = scipy.signal.savgol_filter(paddedAmp.flatten(), sgolnum, sgolply)
            s3 = scipy.signal.savgol_filter(paddedRH.flatten(), sgolnum, sgolply)

            # Combine smoothed metrics for model lookup
            mypts = np.column_stack([s1, s2, s3])

            # Find nearest neighbors in Clara's model using KD-tree
            _, indices = kdtree.query(mypts, k=1)
            
            # Get vegetation phase correction
            uns_phi = veg_correction_model[indices]
            wei = uns_phi > 0  # Remove unphysical models
            uns_phi[wei] = 0
            
            # Smooth the phase prediction
            phipred2 = scipy.signal.savgol_filter(uns_phi.flatten(), sgolnum, sgolply)
            
            # Get slope correction
            slopepred2 = scipy.signal.savgol_filter(slopes_model[indices].flatten(), sgolnum, sgolply)
            
            # Remove padding
            Nlong = 2 * padlen + Ntrack
            phipred2np = np.reshape(phipred2, (Nlong, 1))
            phipred2 = phipred2np[padlen:(padlen + Ntrack), 0]
            
            slopepred2np = np.reshape(slopepred2, (Nlong, 1))
            slopepred2 = slopepred2np[padlen:(padlen + Ntrack), 0]
            
            # Calculate soil moisture
            avgf = D_phi[ii] - phipred2
            newslope = 1.48 - slopepred2  # 1.48 is default bare soil slope
            avgf = np.reshape(avgf, (Ntrack, 1))

            # Convert to VWC (percentage units, not yet leveled)
            # Note: tmin offset will be applied during leveling in original vwc function
            svwc[ii] = newslope.reshape(Ntrack, 1) * avgf

            # Apply bounds checking (in percentage units)
            bad_indices = (svwc[ii] > 60) | (svwc[ii] < -10)
            svwc[ii][bad_indices] = np.nan

            # Save individual track data if requested
            if save_tracks:
                save_individual_track_data(station, int(year[ii][0]), thissat, thisquad, 
                                         year[ii], doy[ii], hour[ii], mjd[ii], azim[ii],
                                         D_phi[ii], D_amplsp[ii], D_amp[ii], D_RH[ii],
                                         s1[padlen:padlen+Ntrack], s2[padlen:padlen+Ntrack], s3[padlen:padlen+Ntrack],
                                         phipred2, slopepred2, newslope,
                                         avgf.flatten(), svwc[ii].flatten(), 
                                         subdir, fr)
            
            # Plot individual tracks only if specifically requested (could add a separate flag for this)
            # For now, commenting out to avoid too many plots
            # if pltit:
            #     obst = sd.mjd_to_obstimes(mjd[ii])
            #     fig = plt.figure(figsize=(10, 4))
            #     plt.plot(obst, D_phi[ii], 'r-', label='raw phase')
            #     plt.plot(obst, avgf, 'b-', label='w/model')
            #     plt.grid()
            #     plt.title(f'{station} sat {thissat}/quadrant {thisquad}')
            #     fig.autofmt_xdate()
            #     plt.legend(loc="best")
            #     plt.show()

    print(f'Processed {tracks_processed}/{Nt} tracks (minimum {min_number_points} points required)')

    # Generate time bins from vxyz data
    if bin_hours < 24:
        print(f'Computing {bin_hours}-hour averaged VWC estimates...')
    else:
        print('Computing daily averaged VWC estimates...')

    finalx = []
    finaly = []
    final_binstarts = []  # Track bin start hours for subdaily output

    # Get unique year/doy combinations
    unique_days = np.unique(vxyz[:, [0, 1]], axis=0)
    print(f'Processing {len(unique_days)} unique days from vxyz data')

    # Process each unique day
    for year_val, doy_val in unique_days:
        year_val = int(year_val)
        doy_val = int(doy_val)

        if bin_hours < 24:
            # Subdaily: loop through time bins for this day
            bins_per_day = 24 // bin_hours
            for bin_idx in range(bins_per_day):
                bin_start = (bin_idx * bin_hours + bin_offset) % 24
                bin_end = (bin_start + bin_hours) % 24

                # Match individual tracks to this time bin
                if bin_end <= bin_start:  # crosses midnight
                    time_mask = ((year == year_val) & (doy == doy_val) & (hour >= bin_start)) | \
                               ((year == year_val) & (doy == doy_val + 1) & (hour < bin_end))
                else:
                    time_mask = (year == year_val) & (doy == doy_val) & \
                               (hour >= bin_start) & (hour < bin_end)

                # Get VWC values for tracks in this time bin
                bin_vwc_raw = svwc[time_mask].flatten()
                # Filter out zeros (unprocessed tracks)
                bin_vwc = bin_vwc_raw[bin_vwc_raw != 0]

                if len(bin_vwc) >= minvalperbin:
                    # Store time bin average
                    finalx.append(g.ydoy2mjd(year_val, doy_val))
                    finaly.append(np.mean(bin_vwc))
                    final_binstarts.append(bin_start)
        else:
            # Daily: match by year/doy only
            time_mask = (year == year_val) & (doy == doy_val)

            # Get VWC values for tracks in this day
            bin_vwc_raw = svwc[time_mask].flatten()
            # Filter out zeros (unprocessed tracks)
            bin_vwc = bin_vwc_raw[bin_vwc_raw != 0]

            if len(bin_vwc) >= minvalperbin:
                # Store daily average (no bin_start for daily data)
                finalx.append(g.ydoy2mjd(year_val, doy_val))
                finaly.append(np.mean(bin_vwc))
                # Don't append to final_binstarts for daily data
    
    if len(finalx) == 0:
        if bin_hours < 24:
            print(f'No {bin_hours}-hour averages could be computed')
        else:
            print('No daily averages could be computed')
        return [], [], []

    # Return VWC values in percentage units (not leveled - vwc function will handle leveling)
    fy = finaly  # Keep as list

    return finalx, fy, final_binstarts


def load_clara_model():
    """
    Load Clara's model from the organized model_data directory
    
    Returns
    -------
    amp_lsp : numpy array
        LSP amplitude features
    amp_dsnr : numpy array  
        DSNR amplitude features
    delta_heff : numpy array
        Change in effective reflector height
    veg_correction : numpy array
        Vegetation phase corrections
    slope_correction : numpy array
        Slope sensitivity corrections
    """
    
    model_file = Path(__file__).parent / 'vegetation_models' / 'clara_high_model.txt'
    
    if not model_file.exists():
        print(f"Clara's model file not found: {model_file}")
        print("Please run the mat file conversion script first.")
        sys.exit()
    
    print(f'Loading Clara model from: {model_file}')
    data = np.loadtxt(model_file, comments='%')

    amp_lsp = data[:, 0]        # LSP amplitude features
    amp_dsnr = data[:, 1]       # DSNR amplitude features  
    delta_heff = data[:, 2]     # Change in effective reflector height
    veg_correction = data[:, 3] # Vegetation phase corrections
    slope_correction = data[:, 4] # Slope sensitivity corrections

    return amp_lsp, amp_dsnr, delta_heff, veg_correction, slope_correction


def padClara(obs, Ntrack, men, padlen):
    """
    Pad arrays before smoothing (Clara's method)
    
    Parameters
    ----------
    obs : numpy array
        Observations to pad
    Ntrack : int
        Number of values in array
    men : int
        Number of values to use for calculating mean at each end
    padlen : int
        Padding length on each end
        
    Returns
    -------
    padded_obs : numpy array
        Padded version of obs
    """
    
    m1 = np.mean(obs[0:men])
    m2 = np.mean(obs[(Ntrack-men):Ntrack])
    p = np.zeros((padlen, 1))
    interim = np.vstack((p + m1, obs.reshape(Ntrack, 1)))
    padded_obs = np.vstack((interim, p + m2))
    
    return padded_obs


def rolling_window(a, window):
    """
    Create rolling window view of array for variance calculation
    
    From: https://stackoverflow.com/questions/6811183/rolling-window-for-1d-arrays-in-numpy
    """
    
    pad = np.ones(len(a.shape), dtype=np.int32)
    pad[-1] = window - 1
    pad = list(zip(pad, np.zeros(len(a.shape), dtype=np.int32)))
    a = np.pad(a, pad, mode='reflect')
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)



def save_individual_track_data(station, track_year, sat_num, quad_num,
                             years, doys, hours, mjds, azimuths,
                             phase_orig, amp_lsp_orig, amp_ls_orig, delta_rh,
                             amp_lsp_smooth, amp_ls_smooth, delta_rh_smooth,
                             phase_veg_corr, slope_corr, slope_final,
                             phase_corrected, vwc_values,
                             subdir, fr):
    """
    Save individual track VWC data for efficient re-binning and analysis
    
    This function saves the complete processing chain from raw observations through
    Clara's vegetation model corrections to final VWC estimates.
    
    Parameters
    ----------
    station : str
        4-character station name
    track_year : int
        Year for the track analysis 
    sat_num : int
        Satellite number
    quad_num : int
        Quadrant number (1-4)
    years : numpy.ndarray
        Year values for each observation
    doys : numpy.ndarray
        Day of year values for each observation
    hours : numpy.ndarray
        Hour values for each observation (UTC)
    mjds : numpy.ndarray
        Modified Julian Date values for each observation
    azimuths : numpy.ndarray
        Azimuth angles for each observation (degrees)
    phase_orig : numpy.ndarray
        Original unwrapped phase observations (degrees)
    amp_lsp_orig : numpy.ndarray
        Original LSP amplitude values
    amp_ls_orig : numpy.ndarray
        Original LS amplitude values
    delta_rh : numpy.ndarray
        Delta RH (apriori - measured, meters)
    amp_lsp_smooth : numpy.ndarray
        Smoothed LSP amplitudes used for model lookup
    amp_ls_smooth : numpy.ndarray
        Smoothed LS amplitudes used for model lookup
    delta_rh_smooth : numpy.ndarray
        Smoothed delta RH used for model lookup (meters)
    phase_veg_corr : numpy.ndarray
        Vegetation phase corrections from Clara's model (degrees)
    slope_corr : numpy.ndarray
        Slope sensitivity corrections from Clara's model
    slope_final : numpy.ndarray
        Final corrected slope values (1.48 - slope_corr)
    phase_corrected : numpy.ndarray
        Vegetation-corrected phase (phase_orig - phase_veg_corr)
    vwc_values : numpy.ndarray
        Final volumetric water content estimates (%)
    subdir : str
        Subdirectory for output files
    fr : int
        Frequency code (20 for L2C, etc.)
        
    File Format
    -----------
    Output columns (17 total):
    Year DOY Hour MJD Az PhaseOrig AmpLSPOrig AmpLSOrig DeltaRHOrig
    AmpLSPSmooth AmpLSSmooth DeltaRHSmooth PhaseVegCorr SlopeCorr SlopeFinal
    PhaseCorrected VWC

    """

    xdir = os.environ['REFL_CODE']
    if subdir:
        track_dir = f'{xdir}/Files/{subdir}/individual_tracks'
    else:
        track_dir = f'{xdir}/Files/{station}/individual_tracks'
    
    os.makedirs(track_dir, exist_ok=True)

    freq_suffix = qp.get_temporal_suffix(fr)
    track_file = f'{track_dir}/{station}_track_sat{sat_num:02d}_quad{quad_num}_{track_year}{freq_suffix}.txt'

    header_lines = [
        f"% Individual Track Data for Station {station}",
        f"% Satellite: {sat_num}, Quadrant: {quad_num}, Year: {track_year}",
        f"% Frequency: {'L2C' if fr == 20 else 'L1' if fr == 1 else 'L5' if fr == 5 else f'L{fr}'}",
        f"% Generated by Advanced Vegetation Model (model 2)",

        f"% Year DOY Hour   MJD   Az  PhaseOrig AmpLSPOrig AmpLSOrig DeltaRHOrig AmpLSPSmooth AmpLSSmooth DeltaRHSmooth PhaseVegCorr SlopeCorr SlopeFinal PhaseCorrected   VWC",
        f"% (1)  (2)  (3)   (4)  (5)    (6)       (7)        (8)     (9)       (10)         (11)       (12)        (13)      (14)       (15)         (16)       (17)"
    ]

    with open(track_file, 'w') as f:
        for line in header_lines:
            f.write(line + '\n')
        
        # Write individual track observations
        for i in range(len(years)):
            f.write(f'{int(years[i]):4d} {int(doys[i]):3d} {hours[i]:6.2f} {mjds[i]:8.0f} {azimuths[i]:6.1f} '
                   f'{phase_orig[i]:9.3f} {amp_lsp_orig[i]:10.6f} {amp_ls_orig[i]:9.6f} {delta_rh[i]:6.3f} '
                   f'{amp_lsp_smooth[i]:12.6f} {amp_ls_smooth[i]:11.6f} {delta_rh_smooth[i]:8.3f} '
                   f'{phase_veg_corr[i]:12.6f} {slope_corr[i]:9.6f} {slope_final[i]:10.6f} '
                   f'{phase_corrected[i]:14.6f} {vwc_values[i]:7.3f}\n')
    
    print(f'  Saved {len(years)} comprehensive track observations to {track_file}')




