C FILE: GNSSSNRBIGGER.F 
      SUBROUTINE FOO(rawf,outf,sp3file,snrtype,decfac,errf) 
      implicit none
      character*128 rawfilename, outfilename, sp3file,
     . rawf,outf,errf
      character*2 snrtype, decfac
Cf2py intent(in) rawf
Cf2py intent(in) outf
Cf2py intent(in) broadf
Cf2py intent(in) snrtype
Cf2py intent(in) decfac
Cf2py intent(in) errf
c     Kristine Larson 15jul27
c     version updated on 18jan08
c     uses sp3 file to compute azimuth and elevation angle
c     all satellite signals
c     17oct15 added orbit pointer
c     18may14 checked to make sure sp3 file doesn't have data
c     from two different days
c      
c     18oct01 added S6,S7,S8, currently storing S6 in column 6
c     and S7 and S8 are in new columns: 10 and 11
c     This is mostly for Galileo
c     column 5 is still edot
c     column 9 is still S5
c     column 7 and 8 are S1 and S2 
c 
c     18oct16 increased number of satellites allowed at any epoch to 48
c     this allows multiple constellations without having to make separate files
c     19feb04
c     allow sp3 files that are longer than 23 hr 45 minutes
c     21feb22 port to python f2py so it can be used in gnssrefl

      integer maxsat, maxob, maxGNSS, np
      parameter (maxsat = 200)
      parameter (maxob = 25)
      parameter (maxGNSS = 400)
      parameter (np= 576)
      real*8 c 
      parameter (c = 0.299792458D+09)      

      integer stderr
      parameter (stderr=6)
      character*80 inline 
      character*4 station
c     character*2  key(maxsat) 
      character*2 prn_pickc
      character*1 satID(maxsat)
      integer  nobs, itime(5), prn(maxsat), numsat, flag, sec,
     +   msec, lli(maxob,maxsat), iprn,
     .   ios, itrack, i, iobs(maxsat), 
     .  gpsweek, prn_pick, fileIN, fileOUT,
     .  iymd(3), nepochs, FirstWeek, idec
      real*8  obs(maxob,maxsat), tod,North(3),
     .   East(3), Up(3), azimuth, elev, staXYZ(3), tod_save,
     .   pi,s1,s2,s5,xrec, yrec, zrec, tc, 
     .   edot,elev2, s6, s7, s8,rt,
     .   rt_lastEpoch, FirstSecond, tod2, Lat,Long,Ht
      logical eof, bad_point,simon,keep_point,decimate
      integer sp3_gps_weeks(np),sp3_nsat,sp3_satnames(maxsat)
      real*8 sp3_XYZ(maxsat,np,3), sp3_gps_seconds(np),
     .  t9(9), x9(9), y9(9), z9(9), sp3_rel_secs(np)
      integer ipointer(maxGNSS),errid,itod
      logical haveorbit(maxGNSS), debug
      debug = .false.
c      file id for error log
      errid = 53
c     set some defaults
c     if you want edot, set this to true
      simon = .true.
      fileIN = 12
      fileOUT = 55
      tod_save = 0.0
      bad_point = .false.
      pi = 4.0*datan(1.d0)
c     shorter filenames
      rawfilename = rawf
      outfilename = outf
      open(errid,file=errf,status='unknown',iostat=ios)
      write(errid,*) 'sp3file :',sp3file
      write(errid,*) 'RINEX file:',rawf
      write(errid,*) 'Output file:',outf
      write(errid,*) 'Selection:',snrtype
      write(errid,*) 'dec factor :',decfac

      READ (decfac, '(I2)') idec
      decimate = .true.
      if (idec .eq. 0) then
          decimate = .false.
      endif

      prn_pickc = snrtype
c
c     comment out for now
c     figure out which option is being requested
      READ (prn_pickc, '(I2)')  prn_pick
      write(errid, *) 'Selection ', prn_pick
c     read in the sp3file
      call read_sp3_200sats(sp3file, sp3_gps_weeks, sp3_gps_seconds,
     .   sp3_nsat, sp3_satnames, sp3_XYZ,haveorbit,
     .   ipointer,nepochs,sp3_rel_secs,errid)
      FirstWeek = sp3_gps_weeks(1)
      FirstSecond = sp3_gps_seconds(1)
      write(errid,*) 'first and last',FirstWeek, FirstSecond
c     print*, sp3_gps_weeks(nepochs), sp3_gps_seconds(nepochs)
c     figure out the time tag of the last sp3 point.  this way you don't
c     interpolate (much) beyond your last point
      write(errid,*)'Last epoch, rel sense', sp3_rel_secs(nepochs)
      rt_lastEpoch = sp3_rel_secs(nepochs)
      if (sp3_nsat .eq. 0) then
        write(errid,*) 'problem reading sp3file, so exiting'
        return
      endif
c     read the header of the RINEX file, returning station coordinates
c     and an observable array and nobs, number of observables
      xrec = 0.d0
      yrec = 0.d0
      zrec = 0.d0

      call read_header_25obs(fileIN,rawfilename, xrec,yrec,zrec,
     .  iobs,nobs,iymd, station,errid)
      if (xrec.eq.0.d0) then
        write(errid,*) 'you need real station coords '
        return
      endif
      if (zrec.eq.0.d0) then
        write(errid,*) 'you need real station coords '
        return
      endif
c     print*,'number of obs main code', nobs
c     moving sites has been removed
      if (nobs .gt. 25 .or. nobs .eq. 0) then
        write(errid,*) 'Only obs types <= 25 allowed. You'
        write(errid,*) 'can try using teqc to remove'
        write(errid,*) 'unneeded observables'
        return
      endif


      call envTrans(xrec,yrec,zrec,staXYZ,Lat,Long,Ht,North,East,Up)
c     open output file
      open(fileOUT,file=outfilename, status='unknown')
      eof = .false.
      do while (.not.eof)
        inline = ' '
        read(fileIN,'(A80)', iostat=ios) inline
        if (ios.ne.0) goto 99
        read(inline(1:32),'(5I3,X,I2,X,I3,4X,2I3)')
     +         (itime(i), i=1,5), sec, msec, flag, numsat
c       seconds in the day
        tod = itime(4)*3600.0 + 60.0*itime(5) + sec
c       print*, tod, tod_save
        tod2 = tod + msec/1000.d0
c print*, 'Time is going backwards.' LOL
        if (tod.lt.tod_save) then
          bad_point = .true.
        else
          bad_point = .false.
        endif
        tod_save = tod
c       read the observation block
        call read_block_gnss(fileIN, flag,inline,numsat,nobs,satID,
     .    prn,obs,lli)
c       flag 4 means it is a comment block, so that gets skipped
c       added that the point is good
        itod = int(tod)
        keep_point = .true.
        if (decimate) then
          if (mod(itod,idec) .ne.0) then
c             write(errid,*) tod ,' begone'
              keep_point = .false.
          endif
        endif

        if (keep_point) then 
        if (flag .ne.4.and..not.bad_point) then
c         find out gpsweek and gpsseconds (tc)
          call convert_time(itime,sec, msec, gpsweek, tc)
c         then convert it to relative time to first sp3 point 
          call rel_time(gpsweek, tc, FirstWeek,FirstSecond, rt)
202       format(a10,i6,f10.0)
c         check that it is within 20 minutes of the first and last sp3 points
          if ( rt.gt. (rt_lastEpoch+20*60) .or. 
     .          (rt.lt. -20*60))  then
             write(errid,202) 'Your epoch', gpsweek, tc
             write(errid,202) 'First  sp3',FirstWeek,FirstSecond
             write(errid,202) 'Last   sp3',sp3_gps_weeks(nepochs), 
     .           sp3_gps_seconds(nepochs)
             write(errid,*) 'Your epoch is beyond a reasonable'
             write(errid,*) 'sp3 point, so I am exiting now.'
             return
          endif
          do itrack = 1, numsat
            iprn = prn(itrack)
c           400 is for satellites that I do not recognize
c            haveorbit is for whether we have a sp3 orbit for that satellite
            if (iprn .ne. 400 .and. haveorbit(iprn) ) then
c             x9,y9,z9 are in meters
              edot = 0.0
c             pick 9 points closest to observation time
c             need to use the pointer
c             print*, gpsweek,tc,rt
              call pick_9points(sp3_nsat, sp3_satnames, sp3_gps_weeks,
     .          sp3_gps_seconds, sp3_XYZ, iprn, gpsweek,tc,itime(4),
     .          t9,x9, y9,z9,ipointer,nepochs,sp3_rel_secs,rt)
               
              if ( nint(  (x9(1)/1000))  .eq. 1000000) then
c               print*,iprn,' bad orbit'
              else
                if (simon) then
                  call get_azel_sp3(rt+0.5, iprn, staXYZ,East,North,Up,
     .             azimuth,elev2,t9,x9,y9,z9)
                endif
                call get_azel_sp3(rt, iprn, staXYZ,East,North,Up,
     .              azimuth,elev,t9,x9,y9,z9)
                if (simon) then
c                   since i did time values 0.5 seconds apart, multiply by 2
                    edot =  2.d0*(elev2-elev)
                endif
c               assign the SNR values to variables
                call pickup_snr(obs, iobs, itrack, s1, s2, s5,s6,s7,s8)
c                 write out to a file
                call write_gnss_to_file(fileOUT, iprn, tod,
     .          s1,s2,s5,azimuth, elev,edot,prn_pick,s6,s7,s8,tod2)
              endif
            endif
          enddo
        endif
        endif
      enddo
99    continue
c     close the log file
      close(errid)
c     close input and output files
      close(fileIN)
      close(fileOUT)
      end

      subroutine read_sp3_200sats(inputfile, gps_weeks, 
     .  gps_seconds, nsat, satnames, XYZ,haveorbit,
     .  ipointer,nepochs,relTime,errid)
      implicit none
c     kristine larson, september 15,2015
c     the input is a 15 minute sp3file name
c     17nov02 tried to extend to 5 minute spfiles
c     KL 19feb01, allow sp3 files that are longer than 23 hours and 45 minute
c     times will now be in gps seconds but a second day will no longer go back to 
c     zero on a day for new week.  this will make it easier to interpolate using a 
c     common time frame, which will be called relTime
c     previous behavior assumed all data were from the same day
c
c     returns satellite names, 
c     gps weeks and 
c     gps seconds of the week, XYZ (in km) 
c     17oct12, KL
c     changed to allow multiple GNSS and 200 satellites
c     INPUT 
c     inputfile is sp3 filename
c     OUTPUT
c     gps_weeks and gps_seconds are arrays? of times on the sp3file
c     nsat - number of satellites
c     satnames - integers
c     1-99 for GPS
c     101-199 for GLONASS
c     201-299 for GALILEO
c     301-399 for BDS
c     default nsat value of 0
c     added pointer array for orbits
c
c     17nov03 returns number of time epochs now
c     18may14 read the header date and ensure that only
c     data from that date are used (sp3 files from CODE had
c     had two midnites in them).
c     19mar25 changed filename of sp3 to be really really long

      integer maxsat, maxob, maxGNSS, np
      parameter (maxsat = 200)
      parameter (maxob = 25)
      parameter (maxGNSS = 400)
      parameter (np= 576)
      real*8 c 
      parameter (c = 0.299792458D+09)      

      character*128 inputfile
      character*80 line 
      integer satnames(maxsat),nsat, gpsweek, prn, i, j, k, 
     .  time, itime(5), gps_weeks(np), msec, sec, ios,newname,
     .  hdr_yy, hdr_mm, hdr_dd, hdr_hour, hdr_minute, FirstWeek
      real*8 x,y,z, XYZ(maxsat,np,3), gps_seconds(np), gpssecond,
     .  FirstSecond, relTime(np), rt
c     character*1 duh/'+'/
      character*1 satID(maxsat), constell
      logical haveorbit(maxGNSS) 
      integer ipointer(maxGNSS), nepochs, s1, s2,errid
c     print*, 'Enter sp3 file reading code'
      nsat = 0
      do i=1,maxGNSS
        haveorbit(i) = .false.
        ipointer(i) = 0
      enddo
      do i=1,maxsat
        satnames(i) = 0
      enddo
c     define everything as zero to start 
      do i=1,np
        gps_seconds(i) = 0
        gps_weeks(i) = 0
        do j=1,maxsat
          do k=1,3
            XYZ(j,i,k) = 0.d0
          enddo
        enddo
      enddo
      sec= 0
      msec = 0
c     open the sp3file
c
      open(12, file=inputfile,status='old',iostat=ios)    
      if (ios .ne. 0) then
        write(errid,*) 'the sp3 file does not exist '
        write(errid,*) inputfile(1:80)
        return
      endif
c     #cP2015 12 30  0  0  0.00000000      97 d+D   IGb08 FIT AIUB
c     skip first two lines of the header-  
c     now save the month and day of the file
      read(12,'(a80)') line
      write(errid,*) 'First epoch of SP3 file ', line
      write(errid,*) 'Number of epochs', line(37:39)
c     removed the commas that are not compliant with new fortran?
      READ (line(37:39), '(I3)') nepochs
      if (nepochs.gt.np) then 
        write(errid,*)'there are more epochs in this file' 
        write(errid,*)'than the code was originally dimensioned'
        write(errid,*)'for. Life is short - skip the point '
      endif
      READ (line(6:7), '(I2)') hdr_yy 
      READ (line(9:10), '(I2)') hdr_mm 
      READ (line(12:13), '(I2)') hdr_dd 
      READ (line(15:16), '(I2)') hdr_hour 
      READ (line(18:19), '(I2)') hdr_minute
      write(errid,*) 'num epochs in header', nepochs  
      write(errid,*) 'header time:', hdr_yy, hdr_mm, 
     .   hdr_dd,hdr_hour,hdr_minute
      itime(1) = hdr_yy
      itime(2) = hdr_mm
      itime(3) = hdr_dd 
      itime(4) = hdr_hour
      itime(5) = hdr_minute
      sec = 0
      msec = 0
      call convert_time(itime,sec, msec, FirstWeek, FirstSecond)
      write(errid,*) 'first week/sec', FirstWeek, FirstSecond

      read(12,'(a80)') line
      read(12,'(1x,i5,3x, 17(a1,i2) )')nsat, 
     .     (satID(i), satnames(i), i=1,17)
      read(12,'(9x, 17(a1,i2))')(satID(i),satnames(i), i=18,34)
      read(12,'(9x, 17(a1,i2))')(satID(i),satnames(i), i=35,51)
      read(12,'(9x, 17(a1,i2))')(satID(i),satnames(i), i=52,68)
      read(12,'(9x, 17(a1,i2))')(satID(i),satnames(i), i=69,85)
      s1 = 86
      s2 = 102
113   read(12,'(a80)') line
c     print*, line
      if (line(1:2) .eq. '+ ') then
c       print*,'found another sat line'
        read(line,'(9x, 17(a1,i2))')(satID(i),satnames(i), i=s1,s2)
c       increment the counters.  this has only been tested up to 102
        s1 = s1 +17
        s2 = s2 + 17
      else if (line(1:2) .eq. '/*') then 
c       print*,'comment line i think'
      else if (line(1:2) .eq. '++') then 
c       print*,'qual flag'
      endif

      if (line(1:1).ne.'*') goto 113

      call fill_pointer(nsat,satID,satnames,haveorbit,ipointer)
c      start your counter for number of epochs
c     I think this also means you have read the header
      time = 1
15    continue
      if (line(1:1).eq.'*') then
c       decode your time tag
        read(line(6:7), '(i2)') itime(1)
        read(line(9:10), '(i2)') itime(2)
        read(line(12:13), '(i2)') itime(3)
        read(line(15:16), '(i2)') itime(4)
        read(line(18:19), '(i2)') itime(5)
c       trying to read two day sp3 file, so changes wrt previous file
        if (.true.) then
          call convert_time(itime,sec, msec, gpsweek, gpssecond)
c         now need to read nsat lines to get the coordinates of the satellite
          do i=1,nsat
            read(12,'(a80)') line
            read(line(2:2),'(a1)') constell
            read(line(3:46),*)prn,x,y,z
c           change prn to new system
            call newSat(constell,prn,newname)
            prn = newname
c           now using index i instead of PRN number to store data
            XYZ(i,time,1) = x
            XYZ(i,time,2) = y
            XYZ(i,time,3) = z 
            gps_weeks(time) = gpsweek
            gps_seconds(time) = gpssecond
            call rel_time(gpsweek, gpssecond, 
     .           FirstWeek, FirstSecond,rt)
c           save seconds since first epoch
            relTime(time) = rt
c           print*, gpsweek,gpssecond, rt
          enddo
          time = time + 1
        endif
c       read the next line - it should be a time tag
        read(12,'(a80)') line
c       increment the time variable
        if (line(1:3).eq.'EOF') goto 55
        if (time >np) then
          write(errid,*)'your sp3 file > max number ', np, ' values'
c         print*,'this is bad - exiting the subroutine'
          goto 55
        endif
      endif
      goto 15
55    continue
c     subtract one because of the CODE midnite issue
      nepochs = time - 1
      write(errid,*) 'RETURNING epochs: ', nepochs
c     you are done reading the file
      close(12)
      write(errid,*)'exiting the sp3 reading code'
56    continue
      end
      subroutine newSat(constell, satnum,nsatnum)
      implicit none
c     takes constellation ID and satellite number
c     and returns a new satellite number, offset by
c     100 for glonass, 200 for galileo etc
c     unknown satellites are all assigned to 400
c     author: kristine larson 17oct15
c     old rinex files do not use a G for GPS
c     so allow blank
c     17nov05 added Q satellites 381, 382, etc
      integer satnum,nsatnum
      character constell
      if (constell .eq. 'G') then
         nsatnum = satnum
      elseif (constell .eq. ' ') then
         nsatnum = satnum
      elseif (constell .eq. 'R') then
         nsatnum = 100+satnum
      elseif (constell .eq. 'E') then
         nsatnum = 200+satnum
      elseif (constell .eq. 'C') then
         nsatnum = 300+satnum
      elseif (constell .eq. 'J') then
c       Japanese satellites
         nsatnum = 380+satnum
      else
         nsatnum = 400
      endif

      end
      subroutine fill_pointer(nsat,satID,satnames,haveorbit,ipointer)
c     author: kristine larson 17nov03
c     purpose: change the satellite names to integers from R??, E??, etc
c     and fill the pointer array
c     inputs: nsat is number of satellites, satID is one character constellation ID
c     outputs: satnames uses our 100,200,300 convention for naming satellites
c             ipointer tells you where it is in the sp3 file
      implicit none

      integer maxsat, maxob, maxGNSS, np
      parameter (maxsat = 200)
      parameter (maxob = 25)
      parameter (maxGNSS = 400)
      parameter (np= 576)
      real*8 c 
      parameter (c = 0.299792458D+09)      

      integer satnames(maxsat), ipointer(maxGNSS), i, nsat, newname
      character*1 satID(maxsat)
      logical haveorbit(maxGNSS)
      do i =1, nsat
        call newSat(satID(i), satnames(i),newname)
c       was mostly for debugging
c       write(6,'(a1, i2, 1x, i3)') satID(i), satnames(i), newname
        satnames(i) = newname
        haveorbit(newname) = .true.
        ipointer(newname) = i
      enddo
      end

      subroutine rel_time(gps_week,gps_second,epochWeek,epochSec,rt)
c     send times (week,secs) and epoch times (epochWeek,epochSec)
c     return relative time, rt
      integer gps_week, epochWeek
      real*8 gps_second, epochSec, rt
      if (gps_week.eq.epochWeek) then
        rt = gps_second - epochSec
      else
c       add a week of seconds
        rt = 7*86400 + gps_second - epochSec
      endif
c     print*, gps_second, rt
      end
      subroutine read_header_25obs(fileID,rawf,xrec,yrec,zrec,
     .  iobs,nobs,iymd,station,fid)
      implicit none

      integer maxsat, maxob,maxGNSS,np
      parameter (maxsat = 200)
      parameter (maxob = 25)
      parameter (maxGNSS = 400)
      parameter (np= 576)
      real*8 c 
      parameter (c = 0.299792458D+09)      

      integer  i, fileID,fid
      character*80 rawf
      character*80 line, dynfmt 
      logical  endofheader 
      integer nobs,iobs(maxsat), iymd(3), ios
      character*2 key(maxsat)
      character*4 station
      real*8 xrec, yrec, zrec
c     send file ID (fid) for error messages ans the like
c     returns receiver coordinates
c     station name is empty to start with
c     returned to main code
      station = '    ' 
      endofheader = .false.

      open(fileID,file=rawf, status='old',iostat=ios)
      if (ios.ne.0) then
        write(fid,*) 'problem opening RINEX file' 
        write(fid,*) 'name:', rawf
        return
      endif
      do while (.not.endofheader)
c     KL 18mar05, fixed bug on nobs
        read (fileID,'(a80)') line
        if (line(61:80).eq.'# / TYPES OF OBSERV') then
          read(line, fmt='(I6)') nobs
c         exit if more than 20 observables
          if (nobs.gt.25) then
             write(fid,*)'this code only supports <=25 observ types'
             write(fid,*)'If your file has more, reduce using teqc '
             write(fid,*)'teqc -O.obs S1+S2+S5+S6+S8 should work' 
             return
          endif
c   KL 19jan09 allowing more lines of OBS types
c         first line has up to 9 OBS types
          if (nobs .lt. 10) then
            write(dynfmt, fmt='(A, I3.3, A)')
     +                      "(6X,", nobs, "(4X,A2))"
            read(line, fmt=dynfmt) (key(i), i=1,nobs)
c         between 10-18 OBS types
          elseif (nobs.gt.9.and.nobs.le.18) then
            write(dynfmt, fmt='(A, I3.3, A)')
     +                      "(6X,", 9, "(4X,A2))"
            read(line, fmt=dynfmt) (key(i), i=1,9)
c           read the next line
            read (fileID,'(a80)') line
            write(dynfmt, fmt='(A, I3.3, A)')
     +                      "(6X,", nobs-9, "(4X,A2))"
            read(line, fmt=dynfmt) (key(i), i=10,nobs)
c           this is more than 18 OBS types
          else
c           first line
            write(dynfmt, fmt='(A, I3.3, A)')
     +                      "(6X,", 9, "(4X,A2))"
            read(line, fmt=dynfmt) (key(i), i=1,9)

c           read the next line
            read (fileID,'(a80)') line
c           reassign this second line
            write(dynfmt, fmt='(A, I3.3, A)')
     +                      "(6X,", 9, "(4X,A2))"
            read(line, fmt=dynfmt) (key(i), i=10,18)

c           read the third line
            read (fileID,'(a80)') line
            write(dynfmt, fmt='(A, I3.3, A)')
     +                      "(6X,", nobs-18, "(4X,A2))"
            read(line, fmt=dynfmt) (key(i), i=19,nobs)

          endif
          write(fid,*) 'NUMBER OF OBSERVABLES ', nobs
        else if (line(61:80).eq.'APPROX POSITION XYZ') then
          read(line, fmt= '(3f14.4)') xrec, yrec, zrec
           write(fid,*) 'XYZ coordinates ', xrec, yrec, zrec
        else if (line(61:77).eq.'TIME OF FIRST OBS') then
          read(line, fmt= '(3i6)') iymd(1), iymd(2), iymd(3)
          write(fid,*) 'Time of first Obs: ', iymd
        else if (line(61:71).eq.'MARKER NAME') then
          read(line(1:4), fmt= '(a4)')  station
c         print*, 'Station name ', station
        endif
        if (line(61:73).eq.'END OF HEADER'.or.
     +       line(61:73).eq.'end of header'.or.
     +       line(61:73).eq.' ') endofheader = .true.
      enddo
      write(fid,*) 'FOUND END OF HEADER'
      do i = 1,maxsat
          iobs(i) = 0
      enddo
      do i = 1, nobs
          if (key(i).eq.'l1' .or. key(i).eq.'L1') iobs(1) = i
          if (key(i).eq.'l2' .or. key(i).eq.'L2') iobs(2) = i
          if (key(i).eq.'c1' .or. key(i).eq.'C1') iobs(3) = i
          if (key(i).eq.'p1' .or. key(i).eq.'P1') iobs(4) = i
          if (key(i).eq.'p2' .or. key(i).eq.'P2') iobs(5) = i
          if (key(i).eq.'s1' .or. key(i).eq.'S1') iobs(6) = i
          if (key(i).eq.'s2' .or. key(i).eq.'S2') iobs(7) = i
          if (key(i).eq.'s5' .or. key(i).eq.'S5') iobs(8) = i
          if (key(i).eq.'s6' .or. key(i).eq.'S6') iobs(9) = i
          if (key(i).eq.'s7' .or. key(i).eq.'S7') iobs(10) = i
          if (key(i).eq.'s8' .or. key(i).eq.'S8') iobs(11) = i
      enddo
      end
      subroutine pick_9points(sp3_nsat, sp3_satnames, sp3_gps_weeks,
     . sp3_gps_seconds, sp3_XYZ, ichoice, gpsweek,gpstime,ihr,
     . t9,x9,y9,z9,ipointer,nepochs,sp3_rel_seconds,relTime)
c    Author: kristine m. larson originally
c    added pointer for orbits october 2017
c    17nov03
c    sent nepochs to the code
c    changed 96 to 288 values -but now some of this doesn't quite work ... hmmm.
c    KL, 19feb04
c    sent time relative to sp3 epoch time. this allows the code to use sp3 files
c    that cross midnite, i.e. have more than one day in them.
c    this means that the relative time is sent as well for the epoch you are 
c    considering.
c
c    inputs: 
c      sp3 - entire sp3 file contents, with names, weeks, etc
c      ichoice is the satellite number (?) you want 
c      gpsweek and gpstime is the time (week and seconds of the week) you want 
c      ihr is hour of the day - I do not know why this is sent as it is not used.
c      ipointer is something telling you which satellite you are choosing.. do not remember
c      the details
c
c      nepochs is how many sp3 time blocks there are
c      sp3_rel_seconds are seconds with respect to the sp3 epoch time.  used instead
c      of GPS seconds so that you can interpolate over a GPS week change.
c      relTime is the epoch time in time relative to sp3 epoch time.
c    outputs:
c      t9,x9,y9,z9 are the time and cartesian coordinates for the 9 points 
c      you will use for doing the fit for the satellite position.  units are 
c      seconds (relative to sp3 first epoch) and position in meters
c
c
c    19feb04 - I am assuming we should use sp3_rel_seconds and relTime now
      implicit none

      integer maxsat, maxob, maxGNSS, np
      parameter (maxsat = 200)
      parameter (maxob = 25)
      parameter (maxGNSS = 400)
      parameter (np= 576)
      real*8 c 
      parameter (c = 0.299792458D+09)      

      integer sp3_gps_weeks(np), sp3_nsat, sp3_satnames(maxsat),gpsweek,
     .  ihr,i,isat,iv,k, i1,i2, trigpt,ivnew
      real*8 sp3_XYZ(maxsat,np,3), sp3_gps_seconds(np), gpstime, t9(9), 
     .  x9(9), y9(9), z9(9), firstGPS, sp3_rel_seconds(np), relTime,
     .  delta
      integer ipointer(maxGNSS), ichoice, nepochs
c     returns x9,y9,z9 in meters for glonass satellites
c     as of 19feb04, t9 is in seconds relative to sp3 epoch time
c
c     set output arrays to zero
      do i=1,9
        t9(i) = 0
        x9(i) = 0
        y9(i) = 0
        z9(i) = 0
      enddo
c     17oct15 need to change isat to the  pointer value
      isat = ipointer(ichoice)
c     so isat will be a smaller number than ichoice, typically 
c     assume for now that the gpsweek is right (hah!)
c     firstGPS = sp3_gps_seconds(1)
c     change the logic to 9 closest, period.  used to hardwire
c     midnite time periods for 15 minute sp3 files

      delta = sp3_rel_seconds(2) - sp3_rel_seconds(1)
      ivnew = 1 + relTime /delta
c     this is the old way of picking indices
c       pick nine closest
c     if (nepochs.eq.96) then
c        iv = 1 + (gpstime - firstGPS)/(15*60)
c     elseif (nepochs.eq.288) then
c        iv = 1 + (gpstime - firstGPS)/(5*60)
c     endif
c     try using ivnew instead of iv (previous logic was for hardwired
c     sp3 files
      trigpt = nepochs -5
      iv = ivnew
      if (iv.lt.5) then
c       use first 9
        i1 = 1
        i2 = 9
      elseif (iv.gt.trigpt) then
c       use last 9
        i1=nepochs-8
        i2=nepochs
      else
        i1 = iv-4 
        i2 = iv+4 
      endif
      k=0
c 105   format(a15,f10.0, i3, i5, i5,i5,i5)
c     for debugging
c     write(17,105) 'T H i1 i2 iv N ', gpstime, ihr, i1, 
c    . i2, ivnew, nepochs
      do i=i1, i2
        k=k+1
c       change to gpstime to relative seconds
        t9(k) = sp3_rel_seconds(i)
c       t9(k) = sp3_gps_seconds(i)
        x9(k) = sp3_XYZ(isat,i,1)*1000
        y9(k) = sp3_XYZ(isat,i,2)*1000
        z9(k) = sp3_XYZ(isat,i,3)*1000
      enddo
      end
      SUBROUTINE polint(xa,ya,n,x,y,dy)
      INTEGER n,NMAX
      DOUBLE PRECISION dy,x,y,xa(n),ya(n)
      PARAMETER (NMAX=10)
      INTEGER i,m,ns
      DOUBLE PRECISION den,dif,dift,ho,hp,w,c(NMAX),d(NMAX)
      ns=1
      dif=abs(x-xa(1))
      do 11 i=1,n
        dift=abs(x-xa(i))
        if (dift.lt.dif) then
          ns=i
          dif=dift
        endif
        c(i)=ya(i)
        d(i)=ya(i)
11    continue
      y=ya(ns)
      ns=ns-1
      do 13 m=1,n-1
        do 12 i=1,n-m
          ho=xa(i)-x
          hp=xa(i+m)-x
          w=c(i+1)-d(i)
          den=ho-hp
          if(den.eq.0.d0) then
            print*, 'failure in polint'
          endif
          den=w/den
          d(i)=hp*den
          c(i)=ho*den
12      continue
        if (2*ns.lt.n-m)then
          dy=c(ns+1)
        else
          dy=d(ns)
          ns=ns-1
        endif
        y=y+dy
13    continue
      return
      END
C  (C) Copr. 1986-92 Numerical Recipes Software *1(."i5..
      subroutine get_azel_sp3(tc, prn, stationXYZ,East,North,Up,
     .  azimuth,elev,t9,x9,y9,z9)
      implicit none
c     remove llh, no longer used
c     kl 2021 feb 24

      integer maxsat, maxob, maxGNSS, np
      parameter (maxsat = 200)
      parameter (maxob = 25)
      parameter (maxGNSS = 400)
      parameter (np= 576)

      real*8 c 

      integer jj, ierr,prn, ihr, t(9),polyorder
c     real*8 xrec, yrec, zrec
      real*8 tc, SatPos(3), toffset, omeg, ghadot,
     . xnew, ynew, znew,
     . azimuth, elev, North(3), East(3), Up(3),stationXYZ(3), range2,
     .  t9(9), x9(9),y9(9), z9(9), outX,outY,outZ,dy
c    this code requests the azel for a time (tc) and satellite (prn)
c    t,x9,y9,and z9 are vectors of precise Cartesian GLONASS coordinates (time in 
c     GPS seconds, xyz in meters
c     stationXYZ is in meters
c     returns azimuth and elev in radians (likely)
c     dy is a sigma from the interpolator
c     t9 is real*8 !!!!!
c
c     KL 19feb04 - need to make changes for multi-day sp3 files.
c     t9 is now relative to sp3 epoch time. which means tc should not be used,
c     but rather tc relative to sp3 epoch time

c     starting value for transmit time
      c = 0.299792458D+09      
      toffset = 0.07
c     Earth Rotation
      ghadot = 7.2921151467d-5 ! rad/sec, using same one as ICD200
      polyorder = 9
c     do this three times - should converge
      do jj = 1, 3
c       interpolate for X,Y, and Z
        call polint(t9, x9, polyorder, tc-toffset, outX, dy)
        call polint(t9, y9, polyorder, tc-toffset, outY, dy)
        call polint(t9, z9, polyorder, tc-toffset, outZ, dy)
        omeg = -ghadot*toffset
        xnew = outX*dcos(omeg) - outY*dsin(omeg)
        ynew = outX*dsin(omeg) + outY*dcos(omeg)
        znew = outZ
        range2= (xnew - stationXYZ(1))**2 + (ynew 
     . - stationXYZ(2))**2 + (znew-stationXYZ(3))**2
c       new time is the geometric range divided by the speed of light
        toffset = dsqrt(range2)/c
      enddo
      SatPos(1) =  xnew
      SatPos(2) =  ynew
      SatPos(3) =  znew
      call azel(azimuth, elev, stationXYZ, East, North, Up, SatPos)
      end

      subroutine azel(azimuth, elev, StaXYZ, East, North,
     .                  Staup, SatPos)
        implicit none
c      returns azimuth and elevation angle in degrees
c      station is cartesian coordinates of station (meters)
c      X, Y, Z is satellite coordinates (meters)
c ----------------------------------------------------
      double precision elev, azimuth
      double precision StaXYZ(3), East(3),
     . North(3), Staup(3), sta2sat(3), Mstation, Msat,
     . sta2sat_N, sta2sat_E, UdotS, zenith,SatPos(3)
      double precision pi, range
c     double precision pi, Lat,Long,Ht,range

c ----------------------------------------------------

c ... find azimuth/elevation of satellite relative
c ... to the reference station (station(3))
c       pi = 4.0*datan(1.d0)
        pi = 3.141592653589793
        sta2sat(1) = SatPos(1) - StaXYZ(1)
        sta2sat(2) = SatPos(2) - StaXYZ(2)
        sta2sat(3) = SatPos(3) - StaXYZ(3)
        range = sqrt(sta2sat(1)**2+ sta2sat(2)**2 +sta2sat(3)**2)

c    ... azimuth of satellite from station:
c  ... get components of 'sta2sat' in ENV frame:
         sta2sat_E = East(1)*sta2sat(1) + East(2)*sta2sat(2)
     .        + East(3)*sta2sat(3)
         sta2sat_N = North(1)*sta2sat(1) + North(2)*sta2sat(2)
     .        + North(3)*sta2sat(3)

c atan2(X,Y) == tan-1(X/Y)
         azimuth = datan2(sta2sat_E, sta2sat_N)*180/pi
         if (azimuth .lt. 0) then
            azimuth = 360 + azimuth
         endif

c    ... elevation angle calculation:
c         Mstation = dsqrt(Staup(1)**2 + Staup(2)**2 +
c    .          Staup(3)**2)
         Mstation = 1 
         Msat = dsqrt(sta2sat(1)**2 + sta2sat(2)**2 +
     .          sta2sat(3)**2)
         UdotS = Staup(1)*sta2sat(1) + Staup(2)*sta2sat(2) +
     .           Staup(3)*sta2sat(3)
         zenith = dacos(UdotS/(Mstation*Msat))*180/pi
         elev = 90 - zenith

       return
       end


c---------------------------------------------------------------------
      subroutine geoxyz2(alat,along,hght,x,y,z,iflag)
c
c Purpose:
c     Convert geodetic curvilinear coordinates to geocentric Cartesian
c        coordinates and vice versa
c
c Input:
c     iflag = 1  convert geodetic coordinates to cartesian coordinates
c           = 2  convert cartesian coordinates to geodetic coordinates
c
c Input/Output:
c     alat,along : geodetic latitude and longitude (radians)
c     hght       : height above the reference ellipsiod (meters)
c     x,y,z      : geocentric Cartesian coordinates (meters)
c
c Notes:
c     Currently assumes the WGS84 reference ellipsoid;
c     Clarke 1866 ellipsoid with approximate translation parameters
c        for NAD27 are commented.
c     Cartesian to geodetic conversion uses an iterative scheme
c        valid to the millimeter level.
c
      integer iflag
      real*8 alat,along,hght,x,y,z, b
      real*8 semi,finv
      real*8 twopi,f,e2,curvn,sqr,alat0,cutoff
      real*8 sinlat,coslat,sinlon,coslon

      semi = 6378137.d0
      finv = 298.257223563d0
      twopi= 8.d0*datan(1.d0)
      f= 1.d0/finv
      b = semi*(1.d0 - f)
      e2= 2.d0*f - f*f
      if( iflag.eq.1) then
         sinlat= dsin(alat)
         coslat= dcos(alat)
         sinlon= dsin(along)
         coslon= dcos(along)
         curvn= semi/(dsqrt(1.d0-e2*sinlat*sinlat))
     
         x= (curvn+hght)*coslat*coslon 
         y= (curvn+hght)*coslat*sinlon 
         z= (curvn*(1.d0-e2)+hght)*sinlat 
      else
         along= datan2(y,x)
         if( along.lt.0d0 ) along=along + twopi
c        starting value for latitude iteration
         sqr= dsqrt(x*x+y*y)
         alat0= datan2(z/sqr,1.d0-e2)
         alat= alat0
   40    sinlat= dsin(alat)
         curvn= semi/(dsqrt(1.d0-e2*sinlat*sinlat))
         alat= datan2((z+e2*curvn*sinlat),sqr)
c        iterate to millimeter level
         if( dabs(alat-alat0).lt.1.d-10) goto 30
         alat0= alat
         goto 40
   30    continue
         cutoff= 80.d0*twopi/360.d0
         if(alat.le.cutoff) then
            hght= (sqr/dcos(alat))-curvn
         else
            hght= z/dsin(alat)-curvn+e2*curvn
         endif
      endif
      return
      end
      subroutine julday (itimes, stime, utc)
c
c...coded by: j mcmillan - university of texas - july 1973
c   julday entry added by brian cuthbertson - 9/29/1979.
c
c...purpose:  to convert between calendar day and julian date (utc).
c
c...formal parameter definitions:
c
c   kalday input  (julday output):
c      utc       the julian date in (double precision) utc form.
c
c      itimes    integer array containing month, day, year, hour, minute
c      stime     floating point seconds
c
      implicit double precision (a-h,o-z)
      dimension itimes(5)
      jd = itimes(2) - 32075 +
     .     1461 * (itimes(3) + 4800 + (itimes(1)-14)/12) /4  +
     .     367 * (itimes(1) - 2 - (itimes(1)-14)/12*12) /12  -
     .     3 * ((itimes(3) + 4900 + (itimes(1)-14)/12)/100) /4
c
      utc= dfloat(jd-2400000) - 1.0d+0  +
     .     dfloat(itimes(4)) / 24.0d+0  +
     .     dfloat(itimes(5)) / 1440.0d+0  +
     .     stime / 86400.0d+0
c
      return
c
c...end kalday/julday
      end
      subroutine mjdgps(tjul,isec,nweek)
c      save
c*
cc name       : mjdgps
cc
cc      call mjdgps(tjul,second,nweek)
cc
cc purpose    : compute number of seconds past midnight of last
cc              saturday/sunday and gps week number of current
cc              date given in modified julian date
cc
cc parameters :
cc         in : tjul  : modified julian date                      r*8
cc        out : second: number of seconds past midnight of last   r*8
cc                      weekend (saturday/sunday)
cc              nweek : gps week number of current week           i*4
cc
cc sr called  : none
cc
cc author     : w. gurtner
cc              mjdgps is a member of gpslib
cc              astronomical institute, university of berne
cc              switzerland
cc##	no unit is used in this subroutine
cc
        implicit real*8 (a-h,o-z)
c
c
c  days since starting epoch of gps weeks (sunday 06-jan-80)
      deltat=tjul-44244.d0
c  current gps week
      nweek=deltat/7.d0
c  seconds past midnight of last weekend
      second=(deltat-(nweek)*7.d0)*86400.d0 
      isec = second  + 0.5d0
c
      return
      end

      subroutine envTrans(xrec,yrec,zrec,stationXYZ, Lat,Long, 
     .  Height, North, East,Up)
c     inputs are receiver coordinates in meters apprently
c     returns a 3 vector (also in meters)
c     Lat and Long are in radians, height is in meters
      implicit none
      real*8 stationXYZ(3), xrec, yrec, zrec, Lat,Long,Height
      real*8 North(3), East(3), Up(3)
      real*8 eflat, pi
      eflat = .33528919d-02
      pi = 4.0*datan(1.d0)
c     XYZ in meters
      stationXYZ(1) = xrec
      stationXYZ(2) = yrec
      stationXYZ(3) = zrec
      call geoxyz2(Lat,Long,Height,xrec,yrec,zrec,2)
c     write(6,'(2F15.9,1x,f12.4)') 180*Lat/pi,180*Long/pi,Height
      Up(1) = dcos(Lat)*dcos(Long)
      Up(2) = dcos(Lat)*dsin(Long)
      Up(3) = dsin(Lat)
c ... also define local east/north for station:
      North(1) = -dsin(Lat)*dcos(Long)
      North(2) = -dsin(Lat)*dsin(Long)
      North(3) = dcos(Lat)
      East(1) = -dsin(Long)
      East(2) = dcos(Long)
      East(3) = 0
      end

      subroutine convert_time(itime,sec, msec, gpsweek, tc)
      implicit none
c     takes as input itime (who can remember what the inputs are,
c     but i think it is RINEX, i.e. YY MM DD HH MM
c     seconds is its own
c     returns gpsweek and tc, which is time in gps seconds (real*8)
      integer itime(5), jtime(5), gpsweek, gpsseconds, msec, sec
      real*8 tjul, rho, tc
c     change 2 char to 4 char
      if (itime(1).lt.80) then
          jtime(3) = itime(1) + 2000
      else
          jtime(3) = itime(1) + 1900
      endif
c     rearrange
      jtime(1) = itime(2)
      jtime(2) = itime(3)
      jtime(4) = itime(4)
      jtime(5) = itime(5)
      rho = 1.0*sec
      call julday(jtime,rho,tjul)
      call mjdgps(tjul,gpsseconds,gpsweek)
c     gps seconds, including non integer parts
      tc = dble(gpsseconds) + msec/1000.0
      end
      subroutine pickup_snr(obs, iobs, itrack, s1, s2, s5,s6,s7,s8)
      implicit none
c     make sure SNR data exist before trying
c     to assign as index to a variable
c     send it the entire variable information
c     returns s1,s2,s5 etc

      integer maxsat, maxob, maxGNSS, np
      parameter (maxsat = 200)
      parameter (maxob = 25)
      parameter (maxGNSS = 400)
      parameter (np= 576)
      real*8 c 
      parameter (c = 0.299792458D+09)      

      real*8  obs(maxob,maxsat) 
      integer iobs(maxsat), itrack
      real*8 s1, s2, s5,s6,s7,s8
      s1 = 0
      s2 = 0
      s5 = 0
      s6 = 0
      s7 = 0
      s8 = 0
      if (iobs(6).ne.0) then
        s1 = obs(iobs(6),itrack)
      endif
      if (iobs(7).ne.0) then
        s2 = obs(iobs(7),itrack)
      endif
      if (iobs(8).ne.0) then
        s5 = obs(iobs(8),itrack)
      endif
      if (iobs(9).ne.0) then
        s6 = obs(iobs(9),itrack)
      endif
      if (iobs(10).ne.0) then
        s7 = obs(iobs(10),itrack)
      endif
      if (iobs(11).ne.0) then
        s8 = obs(iobs(11),itrack)
      endif
      end
      subroutine read_block_gnss(fileID, flag,inline,numsat,nobs,satID,
     .  prn,obs,lli)
      implicit none

      integer maxsat, maxob, maxGNSS, np
      parameter (maxsat = 200)
      parameter (maxob = 25)
      parameter (maxGNSS = 400)
      parameter (np= 576)
      real*8 c 
      parameter (c = 0.299792458D+09)      

      character*1 char, satID(maxsat)
      integer fileID, i, itrack, flag, nobs, numsat 
      integer prn(maxsat), ios, nsat
      character*80 inline, dynfmt, dynfmt2, dynfmt3,dynfmt4
      character*80 anotherline
      real*8  obs(maxob,maxsat) 
      integer lli(maxob,maxsat)
      logical debug
c     KL remove clockerr - was not using it - perhaps making blocks crash 
c     for certain compilers
c     KL - put lli and snr into integer arrays, previously misdefined
c     kl allow up to 15 observables now
c         and 36 satellites
c     kl 18oct16, allow up to 48 satellites now
      debug = .false.
      if (flag.le.1 .or. flag.eq.6) then
        read(inline(33:80),'(12(A1,I2))')
     +         (char, prn(i),i=1,12)
        anotherline = inline
        read(inline(33:80),'(12(A1,2x))') (satID(i),i=1,12) 
c       print*, 'need to read extra lines'
c       19jan09 changed to allow up to 60 satellites
        if (numsat > 12 .and. numsat < 25) then
          read(fileID,'(A80)', iostat=ios) inline
          read(inline(33:80),'(12(A1,I2))') (char, prn(i),i=13,numsat) 
          read(inline(33:80),'(12(A1,2x))') (satID(i),i=13,numsat)
        elseif (numsat > 24 .and. numsat <= 36) then
          read(fileID,'(A80)', iostat=ios) inline
          read(inline(33:80),'(12(A1,I2))') (char, prn(i),i=13,24)
          read(inline(33:80),'(12(A1,2x))') (satID(i),i=13,24)
          read(fileID,'(A80)', iostat=ios) inline
          read(inline(33:80),'(12(A1,I2))') (char, prn(i),i=25,numsat) 
          read(inline(33:80),'(12(A1,2x))') (satID(i),i=25,numsat)
        elseif (numsat > 36 .and. numsat <= 48) then
          read(fileID,'(A80)', iostat=ios) inline
          read(inline(33:80),'(12(A1,I2))') (char, prn(i),i=13,24)
          read(inline(33:80),'(12(A1,2x))') (satID(i),i=13,24)

          read(fileID,'(A80)', iostat=ios) inline
          read(inline(33:80),'(12(A1,I2))') (char, prn(i),i=25,36) 
          read(inline(33:80),'(12(A1,2x))') (satID(i),i=25,36)

          read(fileID,'(A80)', iostat=ios) inline
          read(inline(33:80),'(12(A1,I2))') (char, prn(i),i=37,numsat) 
          read(inline(33:80),'(12(A1,2x))') (satID(i),i=37,numsat)
        elseif (numsat > 48 .and. numsat <= 60) then
          read(fileID,'(A80)', iostat=ios) inline
          read(inline(33:80),'(12(A1,I2))') (char, prn(i),i=13,24)
          read(inline(33:80),'(12(A1,2x))') (satID(i),i=13,24)

          read(fileID,'(A80)', iostat=ios) inline
          read(inline(33:80),'(12(A1,I2))') (char, prn(i),i=25,36) 
          read(inline(33:80),'(12(A1,2x))') (satID(i),i=25,36)

          read(fileID,'(A80)', iostat=ios) inline
          read(inline(33:80),'(12(A1,I2))') (char, prn(i),i=37,48) 
          read(inline(33:80),'(12(A1,2x))') (satID(i),i=37,48)

          read(fileID,'(A80)', iostat=ios) inline
          read(inline(33:80),'(12(A1,I2))') (char, prn(i),i=49,numsat) 
          read(inline(33:80),'(12(A1,2x))') (satID(i),i=49,numsat)

        elseif (numsat > 60 .and. numsat <= 72) then
          read(fileID,'(A80)', iostat=ios) inline
          read(inline(33:80),'(12(A1,I2))') (char, prn(i),i=13,24)
          read(inline(33:80),'(12(A1,2x))') (satID(i),i=13,24)

          read(fileID,'(A80)', iostat=ios) inline
          read(inline(33:80),'(12(A1,I2))') (char, prn(i),i=25,36)
          read(inline(33:80),'(12(A1,2x))') (satID(i),i=25,36)

          read(fileID,'(A80)', iostat=ios) inline
          read(inline(33:80),'(12(A1,I2))') (char, prn(i),i=37,48)
          read(inline(33:80),'(12(A1,2x))') (satID(i),i=37,48)

          read(fileID,'(A80)', iostat=ios) inline
          read(inline(33:80),'(12(A1,I2))') (char, prn(i),i=49,60)
          read(inline(33:80),'(12(A1,2x))') (satID(i),i=49,60)

          read(fileID,'(A80)', iostat=ios) inline
          read(inline(33:80),'(12(A1,I2))') (char, prn(i),i=61,numsat)
          read(inline(33:80),'(12(A1,2x))') (satID(i),i=61,numsat)
        endif

        if (debug) then
c         print*, 'made it past here'
        endif
        if (numsat > 72) then
          print*, 'I cannot read more than 72 satellites'
          print*, 'Please stop launching them!'
          call exit
        endif
c       I need to rename the satellites now
        do i =1, numsat
          call newSat(satID(i), prn(i),nsat)
          prn(i) = nsat
          if (debug) then
            print*, i, nsat
          endif
        enddo
c       change to allow up to 20 observable types
        if (flag .le. 1) then
          do itrack = 1, numsat
            if (debug) then
              print*, 'track', itrack
            endif
c           for 6-10 observables
            if (nobs.gt.5 .and. nobs .le. 10) then
              write(dynfmt, fmt='(A, I3.3, A)')
     +           "(", 5, "(F14.3, I1,1x))"
              write(dynfmt2, fmt='(A, I3.3, A)')
     +           "(" , nobs-5, "(F14.3, I1,1x))"
              read(fileID, fmt=dynfmt, iostat=ios)
     +           (obs(i,itrack), lli(i,itrack), i=1,5)
              read(fileID, fmt=dynfmt2, iostat=ios)
     +             (obs(i,itrack),lli(i,itrack), i=6,nobs)
c    for more than 10 -15 observables 
            elseif (nobs.gt.10.and.nobs.le.15) then
              write(dynfmt, fmt='(A, I3.3, A)')
     +           "(", 5, "(F14.3, I1,1x))"
              write(dynfmt2, fmt='(A, I3.3, A)')
     +           "(", 5, "(F14.3, I1,1x))"
              write(dynfmt3, fmt='(A, I3.3, A)')
     +           "(" , nobs-10, "(F14.3,I1,1x))"

              read(fileID, fmt=dynfmt, iostat=ios)
     +           (obs(i,itrack),lli(i,itrack),i=1,5)
              read(fileID, fmt=dynfmt2, iostat=ios)
     +           (obs(i,itrack),lli(i,itrack),i=6,10)
              read(fileID, fmt=dynfmt3, iostat=ios)
     +           (obs(i,itrack),lli(i,itrack),i=11,nobs)
c     trying to add 15-20 observables
            elseif (nobs.gt.15.and.nobs.le.20) then
              write(dynfmt, fmt='(A, I3.3, A)')
     +           "(", 5, "(F14.3, I1,1x))"
              write(dynfmt2, fmt='(A, I3.3, A)')
     +           "(", 5, "(F14.3, I1,1x))"
              write(dynfmt3, fmt='(A, I3.3, A)')
     +           "(", 5, "(F14.3, I1,1x))"
              write(dynfmt4, fmt='(A, I3.3, A)')
     +           "(" , nobs-15, "(F14.3,I1,1x))"
              read(fileID, fmt=dynfmt, iostat=ios)
     +           (obs(i,itrack),lli(i,itrack),i=1,5)
              read(fileID, fmt=dynfmt2, iostat=ios)
     +           (obs(i,itrack),lli(i,itrack),i=6,10)
              read(fileID, fmt=dynfmt3, iostat=ios)
     +           (obs(i,itrack),lli(i,itrack),i=11,15)
              read(fileID, fmt=dynfmt4, iostat=ios)
     +           (obs(i,itrack),lli(i,itrack),i=16,nobs)
c     trying to add 21-25 observables - it might work. it might not
            elseif (nobs.gt.20.and.nobs.le.25) then
              write(dynfmt, fmt='(A, I3.3, A)')
     +           "(", 5, "(F14.3, I1,1x))"
              write(dynfmt2, fmt='(A, I3.3, A)')
     +           "(", 5, "(F14.3, I1,1x))"
              write(dynfmt3, fmt='(A, I3.3, A)')
     +           "(", 5, "(F14.3, I1,1x))"
              write(dynfmt3, fmt='(A, I3.3, A)')
     +           "(", 5, "(F14.3, I1,1x))"
              write(dynfmt4, fmt='(A, I3.3, A)')
     +           "(" , nobs-20, "(F14.3,I1,1x))"

              read(fileID, fmt=dynfmt, iostat=ios)
     +           (obs(i,itrack),lli(i,itrack),i=1,5)
              read(fileID, fmt=dynfmt2, iostat=ios)
     +           (obs(i,itrack),lli(i,itrack),i=6,10)
              read(fileID, fmt=dynfmt3, iostat=ios)
     +           (obs(i,itrack),lli(i,itrack),i=11,15)
              read(fileID, fmt=dynfmt3, iostat=ios)
     +           (obs(i,itrack),lli(i,itrack),i=16,20)
              read(fileID, fmt=dynfmt4, iostat=ios)
     +           (obs(i,itrack),lli(i,itrack),i=21,nobs)
            else
c           5 or fewer observable types
              write(dynfmt, fmt='(A, I3.3, A)')
     +           "(", nobs, "(F14.3, I1,1x))"
              read(fileID, fmt=dynfmt, iostat=ios)
     +           (obs(i,itrack),lli(i,itrack),i=1,nobs)
            endif
          enddo
        endif
      else
        do itrack = 1, numsat
          read(fileID, fmt='(A80)', iostat=ios) inline
        enddo
      endif
      end
      subroutine write_gnss_to_file(outID, prn, tod, s1,s2,s5,az,
     .   elev,edot, prn_pick,s6,s7,s8,tod2)
c     inputs fileID, prn number, time of day (seconds), 
c     s1,s2,s5, azimuth, elevation angles
c     edot, in degrees/second
c     output selection
c     18ocdt01 added galileo frequencies
c     added option 66, which is all data < 30 degrees
c     20mar02 added msec to the output, sent from main code
      implicit none

      integer maxsat, maxob, maxGNSS, np
      parameter (maxsat = 200)
      parameter (maxob = 25)
      parameter (maxGNSS = 400)
      parameter (np= 576)
      real*8 c 
      parameter (c = 0.299792458D+09)      

      real*8 s1, s2, s5, tod, az, elev, edot,tod2
      real*8 s6, s7, s8 
      integer prn_pick,outID,prn,msec
c     logical galileo
c     asked for all, but < 30 degrees elevation
c     i made 98 and 99 do the same thing so i would 
c     not interfere with my existing file structures at CU
c
c     20aug17
c     this is stupid- but gets the job done
      call checkForNonsense(s1,s2,s5,s6,s7,s8)

c     2020 mar 02
c     try to use actual time, not the integer time
c     print*, msec
      msec = 0
c      tod = tod + msec/1000.d0
c      try this ...
      tod=tod2
      if (prn_pick.eq.99.or.prn_pick.eq.98) then
        if (elev .ge.5.and.elev.le.30) then
          write(outID,112)
     .      prn, elev, az, tod, edot,s6, s1, s2,s5,s7,s8
        endif
c         asked for all data > 5
      elseif (prn_pick.eq.88) then
        if (elev.ge.0) then
          write(outID, 112)
     .        prn, elev, az, tod, edot,s6, s1, s2,s5,s7,s8
        endif
c     all data below 30
c     KL 2019Sep25 fixed bug found by YNakashima 
      elseif (prn_pick.eq.66.and.elev.le.30) then
          write(outID, 112) prn, elev, az, tod, 
     .   edot,s6, s1, s2,s5,s7,s8
c     all data < 10
      elseif (prn_pick.eq.50) then
        if (elev.le.10) then
          write(outID, 112)
     .        prn, elev, az, tod, edot,s6, s1, s2,s5,s7,s8
        endif
      endif
c this format statement gives space for edot and S5
c 111   format(i3,  2f10.4, f10.0, f10.6, f7.2, 3f7.2)
c this format allows galileo
112   format(i3,  2f10.4, f10.1, f10.6, f7.2, 5f7.2)
      end

      subroutine checkForNonsense(s1,s2,s5,s6,s7,s8)
c     this should take care of nonsense values that overrun
c     the fortran write statements
c     2020 august 19
      real*8 s1,s2,s5,s6,s7,s8

      if ((s1.gt.999).or.(s1.lt.0)) then
        s1=0
      endif
      if ((s2.gt.999).or.(s2.lt.0)) then
        s2=0
      endif
      if ((s5.gt.999).or.(s5.lt.0)) then
        s5=0
      endif
      if ((s6.gt.999).or.(s6.lt.0)) then
        s1=0
      endif
      if ((s7.gt.999).or.(s7.lt.0)) then
        s7=0
      endif
      if ((s8.gt.999).or.(s8.lt.0)) then
        s8=0
      endif
      end
C END OF FILE GNSSSNR.F
