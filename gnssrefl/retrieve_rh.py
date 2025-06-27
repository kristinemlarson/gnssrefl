import matplotlib.pyplot as plt
import numpy as np
import os
import subprocess
import sys

import gnssrefl.gnssir_v2 as guts
import gnssrefl.gps as g

def retrieve_rh(station,year,doy,extension, midnite, lsp, snrD, outD, screenstats, irefr,logid,logfilename):
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

    """
    xdir = os.environ['REFL_CODE']
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

            # main satellite loop
            for satNu in satlist:
                found_midnite_cross = False

                iii = (sats == satNu)
                thissat = snrD[iii,:]

                if midnite:
                    iii = (sats_midnite == satNu)
                    ts2 = outD[iii,:]

                goahead = False

                # go find the arcs for this satellite
                if len(thissat) > 0:
                    if screenstats: 
                        logid.write('Satellite {0:3.0f} \n'.format(satNu))
                        logid.write('---------------------------------------------------------------------------------\n')

                    # allow more than one set of elevation angles

                    if len(ellist) > 0:
                        # not doing midnite option here yet ... but maybe it would not be so hard
                        arclist = np.empty(shape=[0,6])
                        for ij in range(0,len(ellist),2):
                            te1 = ellist[ij]; te2 = ellist[ij+1]; newl = [te1,te2]
                            # poorly named inputs - elev, azimuth, seconds of the day, ...
                            # te1 and te2 are the requested elevation angles I believe
                            # satNu is the requested satellite number
                            tarclist,flagm = guts.new_rise_set_again(thissat[:,1],thissat[:,2],
                                                          thissat[:,3],te1, te2,ediff,satNu,screenstats,logid,midnite=midnite)
                            arclist = np.append(arclist, tarclist,axis=0)

                    else:
                        arclist,found_midnite_cross = guts.new_rise_set_again(thissat[:,1],thissat[:,2],
                                                     thissat[:,3],e1, e2,ediff,satNu,screenstats,logid,midnite=midnite)
                        # means you want to try and find a midnite crossing in the day before data file
                        if midnite and found_midnite_cross:
                            arclist_midnite,flagm = guts.new_rise_set_again(ts2[:,1],ts2[:,2],
                                                     ts2[:,3],e1, e2,ediff,satNu,screenstats,logid,midnite=midnite)
                        else:
                            arclist_midnite = np.empty(shape=[0,6])


                    arcsum = []
                    nr,nc = arclist.shape
                    for i in range (0,nr):
                        logid.write('Regular arc {0:3s} {1:5.0f} {2:5.0f} \n'.format(str(i), arclist[i,0], arclist[i,1]))
                        arcsum.append(False)
                      
                    if midnite :
                        mnr,mnc = arclist_midnite.shape
                        if mnr > 0:
                            for i in range(0,mnr):
                                logid.write('midnite arc {0:3s} {1:5.0f} {2:5.0f} \n'.format(str(i), arclist_midnite[i,0], arclist_midnite[i,1]))
                                arcsum.append(True)
                        arclist = np.vstack((arclist, arclist_midnite))
                        nr,nc = arclist.shape

                    nr,nc = arclist.shape
                    if nr > 0:
                        goahead = True

                if goahead:
                    found_results = True
                    # instead of az bins now go through each arc 
                    for a in range(0,nr):
                        # starting and ending index
                        sind = int(arclist[a,0]) ; eind = int(arclist[a,1])

                        # create array for the requested arc
                        if arcsum[a] is True: # this means you have a midnite arc, so use ts2 instead of thissat
                            d2 = np.array(ts2[sind:eind, :], dtype=float)
                        else:
                            d2 = np.array(thissat[sind:eind, :], dtype=float)

                        # window the data - which also removes DC 
                        # this is saying that these are the min and max elev angles you should be using
                        e1 = arclist[a,4]; e2 = arclist[a,5]
                        # pele is not used, so no longer used in window_new, as of v3.6.8

                        # send it the log id now
                        x,y, Nvv, cf, meanTime,avgAzim,outFact1, Edot2, delT, secxonds = guts.window_new(d2, f, 
                                satNu,ncols,lsp['polyV'],e1,e2,azvalues,screenstats,logid)

                        #writing out arcs - try putting it later on ... 
                        if test_savearcs and (Nvv > 0):
                            newffile = guts.arc_name(sdir,satNu,f,a,avgAzim)
                            # name for the individual arc file
                            if (len(newffile) > 0) and (delT !=0):
                                file_info = [station,satNu,f,avgAzim,year,doy,meanTime,docstring]
                        Nv = Nvv # number of points
                        UTCtime = meanTime

                        # if delT  is zero, that means the arc is really not acceptable.  That is set in window_new
                        if (delT != 0):
                            MJD = g.getMJD(year,month,day, meanTime)
                            maxF, maxAmp, eminObs, emaxObs,riseSet,px,pz= g.strip_compute(x,y,cf,maxH,prec,pfitV,minH)

                            tooclose = False
                            if (maxF ==0) & (maxAmp == 0):
                                tooclose == True; Noise = 1; iAzim = 0;
                            else:
                                nij =  pz[(px > NReg[0]) & (px < NReg[1])]

                            Noise = 1
                            if (len(nij) > 0):
                                Noise = np.mean(nij)

                            iAzim = int(avgAzim)

                            if abs(maxF - minH) < 0.10: #  peak too close to min value
                                tooclose = True

                            if abs(maxF - maxH) < 0.10: #  peak too close to max value
                                tooclose = True

                            if False:
                                print(avgAzim, satNu, e1, e2)

                            if (not tooclose) & (delT < delTmax) & (maxAmp > reqAmp[ct]) & (maxAmp/Noise > PkNoise):
                            # request from a tide gauge person for Month, Day, Hour, Minute
                                # save arc and QC is good
                                if test_savearcs and (Nv > 0):
                                    newffile = guts.arc_name(sdir,satNu,f,a,avgAzim)
                            # name for the individual arc file
                                    if (len(newffile) > 0) and (delT !=0):
                                        file_info = [station,satNu,f,avgAzim,year,month,day,doy,meanTime,docstring]
                                        guts.write_out_arcs(newffile,x,y,secxonds,file_info,savearcs_format)

                                if lsp['mmdd']:
                                    ctime = g.nicerTime(UTCtime); xhr = float(ctime[0:2]); xmin = float(ctime[3:5])
                                    onelsp = [year,doy,maxF,satNu,UTCtime,avgAzim,maxAmp, eminObs,emaxObs,Nv,f,riseSet,Edot2,maxAmp/Noise,delT,MJD,irefr,month,day,xhr,xmin]

                                else:
                                    onelsp = [year,doy,maxF,satNu,UTCtime,avgAzim,maxAmp, eminObs,emaxObs,Nv,f,riseSet,Edot2,maxAmp/Noise,delT,MJD,irefr]
                                gj +=1

                                all_lsp.append(onelsp)
                                if screenstats:
                                    if UTCtime < 0:
                                        T = g.nicerTime(-UTCtime)
                                        T = '-' + T
                                    else:
                                        T = ' ' + g.nicerTime(UTCtime)
                                    logid.write('SUCCESS Azimuth {0:3.0f} Sat {1:3.0f} RH {2:7.3f} m PkNoise {3:4.1f} Amp {4:4.1f} Fr{5:3.0f} UTC {6:6s} DT {7:3.0f} \n'.format(iAzim,satNu,maxF,maxAmp/Noise,maxAmp, f,T,round(delT)))
                                if plot_screen:
                                    failed = False
                                    guts.local_update_plot(x,y,px,pz,ax1,ax2,failed)
                            else:
                                if test_savearcs and (Nv > 0):
                                    newffile = guts.arc_name(sdir+'failQC/',satNu,f,a,avgAzim)
                                    # name for the individual arc file - i think delT is redundant here
                                    if (len(newffile) > 0) and (delT !=0):
                                        file_info = [station,satNu,f,avgAzim,year,month,day,doy,meanTime,docstring]
                                        guts.write_out_arcs(newffile,x,y,secxonds,file_info,savearcs_format)
                                rj +=1
                                if screenstats:

                                    logid.write('FAILED QC for Azimuth {0:.1f} Satellite {1:2.0f} UTC {2:5.2f} RH {3:5.2f} \n'.format( iAzim,satNu,UTCtime,maxF))
                                    g.write_QC_fails(delT,lsp['delTmax'],eminObs,emaxObs,e1,e2,ediff,maxAmp, Noise,PkNoise,reqAmp[ct],tooclose,logid)
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
                ax2.set_ylabel('volts/volts') ; ax1.set_ylabel('volts/volts')
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
        if len(allL) > 0:
            head = g.lsp_header(station) # header
        # sort the results for felipe
            ii = np.argsort(allL[:,15])
            allL = allL[ii,:]

            if lsp['mmdd']:
                f = '%4.0f %3.0f %6.3f %3.0f %6.3f %6.2f %6.2f %6.2f %6.2f %4.0f  %3.0f  %2.0f %8.5f %6.2f %7.2f %12.6f %2.0f %2.0f %2.0f %2.0f %2.0f '
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
