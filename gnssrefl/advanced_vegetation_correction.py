import scipy
import scipy.signal
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from pathlib import Path
from datetime import datetime

import gnssrefl.sd_libs as sd
import gnssrefl.gps as g
import gnssrefl.phase_functions as qp

def clara_high_vegetation_filter(station, year, vxyz, tv, tmin, tmax, subdir='', 
                                bin_hours=24, bin_offset=0, pltit=True, fr=20):
    """
    Clara's high vegetation model
    
    This function applies Clara's high vegetation correction directly to 
    the vwc workflow data structures, replacing the simple vegetation model.
    
    Parameters
    ----------
    station : str
        4-char GNSS station name
    year : int 
        Calendar year
    vxyz : numpy array
        Full track-level data from vwc (16 columns):
        [year, doy, phase, azim, sat, rh, norm_ampLSP, norm_ampLS, hour, 
         ampLSP, ampLS, ap_rh, quad, delRH, vegMask, mjd]
    tv : numpy array
        Averaged phase data from write_avg_phase
    tmin : float
        Min soil moisture value based on soil texture
    tmax : float 
        Max soil moisture value based on soil texture
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
    
    Returns
    -------
    None (writes VWC output file directly)
    """
    
    print('>>>>>>>>>>> Clara Chew High Vegetation Model <<<<<<<<<<<<')
    print(f'Processing {len(vxyz)} track observations for station {station}')
    
    # Warn about untested frequencies  
    if fr != 20:
        freq_name = {1: "L1", 2: "L2C", 5: "L5"}.get(fr, f"frequency {fr}")
        print(f"\nWarning: Clara's vegetation model was developed and tested only with L2C data.")
        print(f"Using {freq_name} is experimental and results may not be reliable.")
        print(f"For best results, use frequency 20 (L2C) with this vegetation model.\n")
    
    # Clara's default parameters (from original code)
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
    print('Step 1: Normalizing metrics and removing outliers...')
    tracks, metrics_all, vegmast = norm_zero_vxyz(station, vxyz, remoutli, acc_rhdrift, 
                                                  baseperc, zphival, ampvarday, ampvarlimit)
    
    # Step 2: Apply vegetation filter to compute soil moisture
    print('Step 2: Applying vegetation model...')
    final_mjd, final_vwc = apply_vegetation_model(station, vxyz, metrics_all, tracks, 
                                                  sgolnum, sgolply, padlen, tmin, pltit, 
                                                  fr, bin_hours, bin_offset, subdir)
    
    if len(final_mjd) == 0:
        print('No vegetation-corrected soil moisture estimates could be computed')
        return
    
    # Step 3: Write output in standard gnssrefl VWC format
    print('Step 3: Writing VWC output...')
    write_vwc_output(station, final_mjd, final_vwc, year, subdir, bin_hours, bin_offset, fr)
    
    # Step 4: Generate standard VWC plot if requested
    if pltit and len(final_mjd) > 0:
        # Use the existing gnssrefl vwc_plot function for consistency
        xdir = os.environ['REFL_CODE']
        suffix = qp.get_temporal_suffix(fr, bin_hours, bin_offset)
        plot_suffix = suffix.replace('.txt', '.png')
        
        if subdir:
            plot_path = f'{xdir}/Files/{subdir}/{station}_vol_soil_moisture{plot_suffix}'
        else:
            plot_path = f'{xdir}/Files/{station}_vol_soil_moisture{plot_suffix}'
        
        # Convert MJD to datetime for plotting
        datetime_array = sd.mjd_to_obstimes(np.array(final_mjd))
        
        # Use the standard vwc_plot function
        qp.vwc_plot(station, datetime_array, np.array(final_vwc), plot_path, circles=False, plt2screen=pltit)
    
    print(f'Clara high vegetation model completed for {station}')


def norm_zero_vxyz(station, vxyz, remoutli, acc_rhdrift, baseperc, zphival, 
                   ampvarday, ampvarlimit):
    """
    Normalize metrics and remove outliers from vxyz data
    
    This processes the full track-level data from vwc to prepare it for
    Clara's vegetation model.
    
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
    
    print('>>>>>>>>>>> Normalizing track data <<<<<<<<<<<<')
    
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
            
        print(f'Processing track {i+1}/{numtracks}: sat {thesat}, quad {thequad}, {Nvals} points')
        
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
    
    print(f'Completed normalization for {numtracks} tracks')
    return tracks, metrics_all, vegmast


def apply_vegetation_model(station, vxyz, normmet, tracks, sgolnum, sgolply, 
                          padlen, tmin, pltit, fr, bin_hours, bin_offset, subdir):
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
    tmin : float
        Minimum soil texture
    pltit : bool
        Show plots
        
    Returns
    -------
    final_mjd : list
        MJD values for daily averages
    final_vwc : list
        VWC values for daily averages
    """
    
    print('>>>>>>>>>>> Applying vegetation model <<<<<<<<<<<<')
    
    # Extract normalized metrics
    D_amplsp = normmet[:, 0]
    D_amp = normmet[:, 1] 
    D_phi = normmet[:, 2]
    D_RH = normmet[:, 3]
    
    # Extract original data
    year = vxyz[:, 0]
    doy = vxyz[:, 1]
    hour = vxyz[:, 8]
    q = vxyz[:, 12]
    sat = vxyz[:, 4]
    mjd = vxyz[:, 15]
    
    Nobs = len(vxyz)
    svwc = np.zeros((Nobs, 1))  # Soil moisture output
    
    # Load Clara's model
    amp_lsp_model, amp_dsnr_model, delta_heff_model, veg_correction_model, slopes_model = load_clara_model()
    ref_points = np.column_stack([amp_lsp_model, amp_dsnr_model, delta_heff_model])
    
    min_number_points = 90  # Minimum points per track
    men = 20    # Points for padding calculation
    
    Nt, nc = tracks.shape
    
    # Process each track
    for i in range(Nt):
        thissat = int(tracks[i, 0])
        thisquad = int(tracks[i, 1])
        ii = (thissat == sat) & (thisquad == q)
        Ntrack = len(sat[ii])
        
        if Ntrack > min_number_points:
            print(f'Processing track {i+1}/{Nt}: sat {thissat}/quad {thisquad}, {Ntrack} points')
            
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
            
            # Find nearest neighbors in Clara's model
            indices = numpy_1nn_v2(mypts, ref_points)
            
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
            
            # Convert to volumetric water content
            svwc[ii] = 100 * tmin + newslope.reshape(Ntrack, 1) * avgf
            
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
    
    # Compute daily averages
    print('Computing daily averages...')
    finalx = []
    finaly = []
    unique_mjd = np.unique(mjd)
    
    for i in range(len(unique_mjd)):
        umjd = int(unique_mjd[i])
        jj = (mjd == umjd)
        if len(svwc[jj]) >= 4:  # Minimum 4 tracks per day
            finalx.append(umjd)
            finaly.append(np.mean(svwc[jj]))
    
    if len(finalx) == 0:
        print('No daily averages could be computed')
        return [], []
        
    # Apply leveling (Clara's approach)
    fy = np.asarray(finaly)
    fsorted = np.sort(fy)
    lowest25 = np.mean(fsorted[0:min(25, len(fsorted))])
    
    # Level the data
    fy = (100 * tmin + (fy - lowest25)) / 100
    
    
    return finalx, fy.tolist()


def write_vwc_output(station, mjd_list, vwc_list, year, subdir, bin_hours, bin_offset, fr):
    """Write VWC output file in standard gnssrefl format"""
    
    xdir = os.environ['REFL_CODE']
    
    # Use standard gnssrefl naming convention with proper frequency and temporal suffix
    suffix = qp.get_temporal_suffix(fr, bin_hours, bin_offset)
    
    if subdir:
        outfile = f'{xdir}/Files/{subdir}/{station}_vwc{suffix}'
    else:
        outfile = f'{xdir}/Files/{station}_vwc{suffix}'
    
    # Convert MJD to datetime
    datetime_array = sd.mjd_to_obstimes(np.array(mjd_list))
    
    with open(outfile, 'w') as f:
        # Header matching gnssrefl VWC format
        freq_name = {1: "L1", 2: "L2C", 20: "L2C", 5: "L5"}.get(fr, f"Frequency {fr}")
        f.write(f'% Soil Moisture Results for GNSS Station {station.upper()}\n')
        f.write(f'% Frequency used: {freq_name}\n')
        f.write(f'% Vegetation model used: clara_high\n')
        f.write('% https://github.com/kristinemlarson/gnssrefl\n')
        
        if bin_hours < 24:
            f.write(f'% Subdaily VWC with {bin_hours}-hour bins (offset: {bin_offset}h)\n')
            f.write('% FracYr    Year   DOY   VWC Month Day BinStart\n')
        else:
            f.write('% FracYr    Year   DOY   VWC Month Day\n')
        
        # Write data
        for i, dt in enumerate(datetime_array):
            year_val = dt.year
            fracyr = year_val + (dt.timetuple().tm_yday - 1) / 365.25
            doy = dt.timetuple().tm_yday
            month = dt.month
            day = dt.day
            
            if bin_hours < 24:
                # Future subdaily format - for now just write 0 for BinStart
                bin_start = 0
                f.write(f' {fracyr:8.4f} {year_val:4d} {doy:4d} {vwc_list[i]:8.3f} {month:4d} {day:4d} {bin_start:4d}\n')
            else:
                # Daily format
                f.write(f' {fracyr:8.4f} {year_val:4d} {doy:4d} {vwc_list[i]:8.3f} {month:4d} {day:4d}\n')
    
    print(f'Wrote {len(mjd_list)} vegetation-corrected soil moisture estimates to {outfile}')


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
    
    # Extract columns with descriptive variable names
    amp_lsp = data[:, 0]        # LSP amplitude features
    amp_dsnr = data[:, 1]       # DSNR amplitude features  
    delta_heff = data[:, 2]     # Change in effective reflector height
    veg_correction = data[:, 3] # Vegetation phase corrections
    slope_correction = data[:, 4] # Slope sensitivity corrections
    
    print(f'Loaded model with {len(data)} data points')
    
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


def numpy_1nn_v2(query_points, reference_points):
    """
    Pure numpy 1-nearest neighbor search
    
    Parameters
    ----------
    query_points : numpy array (N, 3)
        Points to find neighbors for
    reference_points : numpy array (M, 3)
        Reference points to search in
        
    Returns
    -------
    indices : numpy array
        Indices of nearest neighbors
    """
    
    # Compute all pairwise Euclidean distances
    diff = query_points[:, np.newaxis, :] - reference_points[np.newaxis, :, :]
    distances = np.sqrt(np.sum(diff**2, axis=2))
    
    # Find nearest neighbor
    indices = np.argmin(distances, axis=1, keepdims=True).flatten()
    
    return indices


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


