import matplotlib.pyplot as plt
import numpy as np
import os
import subprocess
import sys

import gnssrefl.gnssir_v2 as guts
import gnssrefl.gps as g
from gnssrefl.utils import FileManagement
from gnssrefl.extract_arcs import extract_arcs

def retrieve_rh(station,year,doy,extension, midnite, lsp, snrD, outD, screenstats, irefr,logid,logfilename,dbhz):
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
    midnite : bool
        whether you are going to allow arcs to cross midnite
    lsp : dict
        inputs to LSP analysis
    snrD : numpy array
        contents of SNR file
    outD : numpy array
        contents of SNR file including two hours before midnite
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
    docstring = 'arrays are eangles (degrees), dsnrData is SNR with/DC removed, and sec (seconds of the day),\n'

    # Use FileManagement for arcs directory with extension support
    # Only create directory if savearcs is enabled
    test_savearcs = lsp.get('savearcs', False)
    fm = FileManagement(station, "arcs_directory", year=year, doy=doy, extension=extension)
    sdir = str(fm.get_directory_path(ensure_directory=test_savearcs)) + '/'
    
    all_lsp = [] # variable to save the results so you can sort them

    d = g.doy2ymd(year,doy); month = d.month; day = d.day

    nrows,ncols=snrD.shape
    # used in previous code ... these elevation angles have been refraction corrected
    ele =  snrD[:,1]
    sats = snrD[:,0]

    if midnite:
        ele_midnite = outD[:,1] 
        sats_midnite = outD[:,0] 
        nnrows,nncols=outD.shape

    onesat = lsp['onesat']; #screenstats = lsp['screenstats']

    e1=lsp['e1']; e2=lsp['e2']; minH = lsp['minH']; maxH = lsp['maxH']
    ediff = lsp['ediff']; NReg = lsp['NReg']
    plot_screen = lsp['plt_screen']
    PkNoise = lsp['PkNoise']; prec = lsp['desiredP']; delTmax = lsp['delTmax']

    if 'ellist' in lsp.keys():
        ellist = lsp['ellist']
        if len(ellist) > 0:
            print('Using an augmented elevation angle list', ellist)
    else:
        ellist = [];

    if 'azval2' in lsp.keys():
        azval2 = lsp['azval2'];
        naz = int(len(azval2)/2)
    else:
        print('This module requires azval2 to be set in gnssir_input. This record is not present in your json.')
        return

    pele = lsp['pele'] ; pfitV = lsp['polyV']
    freqs = lsp['freqs'] ; reqAmp = lsp['reqAmp']

    # allows negative azimuth value for first pair
    azvalues = guts.rewrite_azel(azval2)
    gzip = lsp['gzip']

    if 'dec' in lsp.keys():
        dec = int(lsp['dec'])
    else:
        dec = 1 # so Jupyter notebooks do not need to be rewritten

    # no need to print to screen if default
    if (dec != 1):
        print('Using decimation value: ', dec)

    # this must have been something i was doing privately
    if 'savearcs' in lsp:
        test_savearcs = lsp['savearcs']
    else:
        test_savearcs = False

    # default will be plain txt
    if 'savearcs_format' in lsp:
        savearcs_format = lsp['savearcs_format']
    else:
        savearcs_format = 'txt'

    if True: # so we don't have to reindent everything ... 
        total_arcs = 0
        ct = 0
#       the main loop a given list of frequencies
        for f in freqs:
            found_results = False
            if plot_screen: 
                # no idea if this will work
                fig, (ax1, ax2) = plt.subplots(2, 1,figsize=(10,7))
            rj = 0
            gj = 0
            if screenstats: 
                logid.write('=================================================================================\n')
                logid.write('Looking at {0:4s} {1:4.0f} {2:3.0f} frequency {3:3.0f} ReqAmp {4:7.2f} \n'.format(station, year, doy,f,reqAmp[ct]))
                logid.write('=================================================================================\n')
                #print('**** looking at frequency ', f, ' ReqAmp', reqAmp[ct], ' doy ', doy, 'ymd', year, month, day )

#           get the list of satellites for this frequency
            if onesat == None:
                satlist = guts.find_mgnss_satlist(f,year,doy)
            else:
                # check that your requested satellite is the right frequency
                satlist = guts.onesat_freq_check(onesat,f )

            # Extract arcs using the new module
            arcs = extract_arcs(
                snrD,
                freq=f,
                e1=e1, e2=e2,
                ellist=ellist,
                azlist=azvalues,
                sat_list=satlist,
                ediff=ediff,
                polyV=lsp['polyV'],
                dbhz=dbhz,
            )

            # Process each arc
            for a, (meta, data) in enumerate(arcs):
                found_results = True

                # Map extract_arcs output to expected variables
                satNu = meta['sat']
                x = data['ele']
                y = data['snr']
                secxonds = data['seconds']
                cf = meta['cf']
                avgAzim = meta['az_init']
                Edot2 = meta['edot_factor']
                delT = meta['delT']
                meanTime = meta['time_avg']
                Nvv = meta['num_pts']
                Nv = Nvv
                UTCtime = meanTime

                # LSP computation
                MJD = g.getMJD(year,month,day, meanTime)
                maxF, maxAmp, eminObs, emaxObs,riseSet,px,pz = g.strip_compute(x,y,cf,maxH,prec,pfitV,minH)

                tooclose = False
                if (maxF == 0) & (maxAmp == 0):
                    tooclose = True
                    Noise = 1
                    iAzim = 0
                else:
                    nij = pz[(px > NReg[0]) & (px < NReg[1])]

                Noise = 1
                if len(nij) > 0:
                    Noise = np.mean(nij)

                iAzim = int(avgAzim)

                if abs(maxF - minH) < 0.10:  # peak too close to min value
                    tooclose = True

                if abs(maxF - maxH) < 0.10:  # peak too close to max value
                    tooclose = True

                if (not tooclose) & (delT < delTmax) & (maxAmp > reqAmp[ct]) & (maxAmp/Noise > PkNoise):
                    # QC passed - save arc
                    if test_savearcs and (Nv > 0):
                        newffile = guts.arc_name(sdir,satNu,f,a,avgAzim)
                        if (len(newffile) > 0) and (delT != 0):
                            file_info = [station,satNu,f,avgAzim,year,month,day,doy,meanTime,docstring]
                            guts.write_out_arcs(newffile,x,y,secxonds,file_info,savearcs_format)

                    xyear,xmonth,xday,xhr,xmin,xsec,xdoy = g.simpleTime(MJD)
                    betterUTC = xhr + xmin/60 + xsec/3600
                    if lsp['mmdd']:
                        onelsp = [xyear,xdoy,maxF,satNu,betterUTC,avgAzim,maxAmp,eminObs,emaxObs,Nv,f,riseSet,Edot2,maxAmp/Noise,delT,MJD,irefr,xmonth,xday,xhr,xmin,xsec]
                    else:
                        onelsp = [xyear,xdoy,maxF,satNu,betterUTC,avgAzim,maxAmp,eminObs,emaxObs,Nv,f,riseSet,Edot2,maxAmp/Noise,delT,MJD,irefr]

                    gj += 1
                    all_lsp.append(onelsp)

                    if screenstats:
                        T = ' ' + g.nicerTime(betterUTC)
                        logid.write('SUCCESS Azimuth {0:3.0f} Sat {1:3.0f} RH {2:7.3f} m PkNoise {3:4.1f} Amp {4:4.1f} Fr{5:3.0f} UTC {6:6s} DT {7:3.0f} \n'.format(iAzim,satNu,maxF,maxAmp/Noise,maxAmp,f,T,round(delT)))
                    if plot_screen:
                        failed = False
                        guts.local_update_plot(x,y,px,pz,ax1,ax2,failed)
                else:
                    # QC failed
                    if test_savearcs and (Nv > 0):
                        newffile = guts.arc_name(sdir+'failQC/',satNu,f,a,avgAzim)
                        if (len(newffile) > 0) and (delT != 0):
                            file_info = [station,satNu,f,avgAzim,year,month,day,doy,meanTime,docstring]
                            guts.write_out_arcs(newffile,x,y,secxonds,file_info,savearcs_format)
                    rj += 1
                    if screenstats:
                        logid.write('FAILED QC for Azimuth {0:.1f} Satellite {1:2.0f} UTC {2:5.2f} RH {3:5.2f} \n'.format(iAzim,satNu,UTCtime,maxF))
                        g.write_QC_fails(delT,lsp['delTmax'],eminObs,emaxObs,e1,e2,ediff,maxAmp,Noise,PkNoise,reqAmp[ct],tooclose,logid)
                    if plot_screen:
                        failed = True
                        guts.local_update_plot(x,y,px,pz,ax1,ax2,failed)

            if screenstats:
                logid.write('=================================================================================\n')
                logid.write('     Frequency  {0:3.0f}   good arcs: {1:3.0f}  rejected arcs: {2:3.0f} \n'.format( f, gj, rj))
                logid.write('=================================================================================\n')
            total_arcs = gj + total_arcs
# close the output files
            ct += 1
            if found_results and plot_screen:
                print('data found for this frequency: ',f)
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

                plotname = f'{xdir}/Files/{station}/gnssir_freq{f:03d}.png'
                print(plotname)
                g.save_plot(plotname)
                plt.show()
            else:
                if plot_screen: 
                    print('no data found for this frequency: ',f)

        # try moving this
        if found_results and plot_screen:
            guts.plot2screen(station, f, ax1, ax2,lsp['pltname']) 

        if screenstats:
            logid.close()
            print('Screen stat information printed to: ', logfilename)

        # look like someone asked me to sort the LSP results ... 
        # convert to numpy array
        allL = np.asarray(all_lsp)
        longer_line = lsp['mmdd']
        #print('writing out longer line ', longer_line)
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
            testfile,fe = g.LSPresult_name(station,year,doy,extension)
            print('Writing sorted LSP results to : ', testfile, '\n')
            np.savetxt(testfile, allL, fmt=f, delimiter=' ', newline='\n',header=head, comments='%')
        else:
            print('No good retrievals found so no LSP file should be created ')
            lspname,orgexist = g.LSPresult_name(station,year,doy,extension)
            print(lspname,orgexist)
            if orgexist:
                subprocess.call(['rm', '-f',lspname])
