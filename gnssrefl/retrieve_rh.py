from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
import os
import subprocess
import sys

import gnssrefl.gnssir_v2 as guts
import gnssrefl.gps as g
from gnssrefl.utils import FileManagement, check_arc_quality, format_qc_summary

def retrieve_rh(station,year,doy,extension, lsp, arcs, screenstats, irefr,logid,logfilename,dbhz):
    """
    new worker code that estimates LSP from GNSS SNR data.
    it will now live here and be called by gnssir_v2.py

    Parameters
    ----------
    station : str
        name of station
    year : int
        calendar year
    doy : int
        day of year
    extension : str
        strategy extension
    lsp : dict
        inputs to LSP analysis
    arcs : list of (metadata, data) tuples
        pre-extracted satellite arcs from extract_arcs_from_station
    screenstats : bool
        whether you want stats to the screen
    irefr: int
        which refrction model is used
    logid : file ID
        opened in earlier function
    logfilename : str
        name of the log file ...
    dbhz : bool
        keep dbhz units  (or not)

    """
    fundy = False
    if station == 'bof3':
        fundy = True

    xdir = os.environ['REFL_CODE']
    savearcs = lsp.get('savearcs', False)
    all_lsp = [] # variable to save the results so you can sort them
    d = g.doy2ymd(year,doy); month = d.month; day = d.day

    e1=lsp['e1']; e2=lsp['e2']; minH = lsp['minH']; maxH = lsp['maxH']
    NReg = lsp['NReg']
    plot_screen = lsp['plt_screen']
    PkNoise = lsp['PkNoise']; prec = lsp['desiredP']
    freqs = lsp['freqs'] ; reqAmp = lsp['reqAmp']
    reqAmp_dict = {f: reqAmp[i] for i, f in enumerate(freqs)}

    # Group pre-extracted arcs by frequency
    arcs_by_freq = defaultdict(list)
    for meta, data in arcs:
        arcs_by_freq[meta['freq']].append((meta, data))

    qc_lines = []
    # Process each frequency
    for f in freqs:
        rejected_arcs = 0
        good_arcs = 0

        freq_arcs = arcs_by_freq[f]
        if plot_screen:
            fig, (ax1, ax2) = plt.subplots(2, 1,figsize=(10,7))

        if screenstats:
            logid.write('=================================================================================\n')
            logid.write('Looking at {0:4s} {1:4.0f} {2:3.0f} frequency {3:3.0f} ReqAmp {4:7.2f} \n'.format(station, year, doy,f,reqAmp_dict[f]))
            logid.write('=================================================================================\n')

        # Process each arc
        n_total = len(freq_arcs)
        qc_counts = defaultdict(int)

        for arc_number, (meta, data) in enumerate(freq_arcs):
            arc_passed = False
            try:
                # Map extract_arcs output to expected variables
                satNu = meta['sat']
                x = data['ele']
                y = data['snr']
                seconds = data['seconds']
                cf = meta['cf']
                az_min_ele = meta['az_min_ele']
                Edot2 = meta['edot_factor']
                delT = meta['delT']
                meanTime = meta['arc_timestamp']
                Nvv = meta['num_pts']
                Nv = Nvv
                UTCtime = meanTime

                # LSP computation
                MJD = g.getMJD(year,month,day, meanTime)
                maxF, maxAmp, eminObs, emaxObs,riseSet,px,pz = g.strip_compute(x,y,cf,maxH,prec,minH)

                nij = pz[(px > NReg[0]) & (px < NReg[1])]
                Noise = np.mean(nij) if len(nij) > 0 else 0

                iAzim = int(az_min_ele)

                passed, reason = check_arc_quality(meta, maxF, maxAmp, Noise, lsp)
                if not passed:
                    qc_counts[reason] += 1
                    rejected_arcs += 1

                    if screenstats:
                        logid.write('FAILED QC for Azimuth {0:.1f} Satellite {1:2.0f} UTC {2:5.2f} RH {3:5.2f} \n'.format(iAzim,satNu,UTCtime,maxF))
                        tooclose = reason == 'tooclose'
                        g.write_QC_fails(delT,lsp['delTmax'],eminObs,emaxObs,e1,e2,lsp['ediff'],maxAmp,Noise,PkNoise,reqAmp_dict[f],tooclose,logid)
                    if plot_screen:
                        failed = True
                        guts.local_update_plot(x,y,px,pz,ax1,ax2,failed)
                    continue

                arc_passed = True
                xyear,xmonth,xday,xhr,xmin,xsec,xdoy = g.simpleTime(MJD)
                betterUTC = xhr + xmin/60 + xsec/3600

                if lsp['mmdd']:
                    onelsp = [xyear,xdoy,maxF,satNu,betterUTC,az_min_ele,maxAmp,eminObs,emaxObs,Nv,f,riseSet,Edot2,maxAmp/Noise,delT,MJD,irefr,xmonth,xday,xhr,xmin,xsec]
                else:
                    onelsp = [xyear,xdoy,maxF,satNu,betterUTC,az_min_ele,maxAmp,eminObs,emaxObs,Nv,f,riseSet,Edot2,maxAmp/Noise,delT,MJD,irefr]

                good_arcs += 1
                all_lsp.append(onelsp)

                if screenstats:
                    T = ' ' + g.nicerTime(betterUTC)
                    logid.write('SUCCESS Azimuth {0:3.0f} Sat {1:3.0f} RH {2:7.3f} m PkNoise {3:4.1f} Amp {4:4.1f} Fr{5:3.0f} UTC {6:6s} DT {7:3.0f} \n'.format(iAzim,satNu,maxF,maxAmp/Noise,maxAmp,f,T,round(delT)))

                if plot_screen:
                    failed = False
                    guts.local_update_plot(x,y,px,pz,ax1,ax2,failed)
            finally:
                if not arc_passed and savearcs:
                    from gnssrefl.extract_arcs import move_arc_to_failqc
                    move_arc_to_failqc(meta, station, year, doy, extension)

        qc_line = format_qc_summary(f, n_total, qc_counts, good_arcs)
        qc_lines.append(qc_line)

        if screenstats:
            logid.write('=================================================================================\n')
            logid.write('     Frequency  {0:3.0f}   good arcs: {1:3.0f}  rejected arcs: {2:3.0f} \n'.format( f, good_arcs, rejected_arcs))
            logid.write(qc_line + '\n')
            logid.write('=================================================================================\n')

        if good_arcs > 0 and plot_screen:
            ax1.set_xlabel('Elevation Angles (deg)')
            ax1.grid(True, linestyle='-'); ax2.grid(True, linestyle='-')
            ax1.set_title(station + ' Raw Data/Periodogram for ' + g.ftitle(f) + ' Frequency')
            ax2.set_xlabel('Reflector Height (m)');
            if dbhz:
                ax2.set_ylabel('db-Hz') ;
                ax1.set_ylabel('db-Hz')
            else:
                ax2.set_ylabel('volts/volts') ;
                ax1.set_ylabel('volts/volts')

            print('data found for this frequency: ', f)
            plotname = f'{xdir}/Files/{station}/gnssir_freq{f:03d}.png'
            print(plotname)

            g.save_plot(plotname)
            plt.show()
        else:
            if plot_screen:
                print('no data found for this frequency: ',f)

    if good_arcs > 0 and plot_screen:
        guts.plot2screen(station, f, ax1, ax2,lsp['pltname'])

    if screenstats:
        logid.close()
        print('Screen stat information printed to: ', logfilename)

    # look like someone asked me to sort the LSP results ...
    # convert to numpy array
    allL = np.asarray(all_lsp)
    longer_line = lsp['mmdd']
    if len(allL) > 0:
        head = g.lsp_header(station,longer_line=longer_line) # header
    # sort the results for felipe
        ii = np.argsort(allL[:,15])
        allL = allL[ii,:]

        if longer_line:
            f = '%4.0f %3.0f %6.3f %3.0f %6.3f %6.2f %6.2f %6.2f %6.2f %4.0f  %3.0f  %2.0f %8.5f %6.2f %7.2f %12.6f %2.0f %2.0f %2.0f %2.0f %2.0f %2.0f '
        else:
            f = '%4.0f %3.0f %6.3f %3.0f %6.3f %6.2f %6.2f %6.2f %6.2f %4.0f  %3.0f  %2.0f %8.5f %6.2f %7.2f %12.6f %2.0f'

    # this is really just overwriting what I had before. However, This will be sorted.
        testfile = FileManagement(station, 'gnssir_result', year, doy, extension=extension).get_file_path()
        print('Writing sorted LSP results to : ', testfile, '\n')
        np.savetxt(testfile, allL, fmt=f, delimiter=' ', newline='\n',header=head, comments='%')
    else:
        print('No good retrievals found so no LSP file should be created ')
        lspname = FileManagement(station, 'gnssir_result', year, doy, extension=extension).get_file_path(ensure_directory=False)
        orgexist = lspname.is_file()
        print(lspname,orgexist)
        if orgexist:
            subprocess.call(['rm', '-f', str(lspname)])

    if qc_lines:
        print('\n'.join(qc_lines))
