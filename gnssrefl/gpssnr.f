C FILE: GPSSNR.F 
      SUBROUTINE FOO(rawf,outf,broadf,snrtype,decfac,errf) 
      implicit none
      character*132 rawfilename, outfilename, broadfile
      character*2 snrtype, decfac
      character*132 rawf,outf,broadf,mess,errf
Cf2py intent(in) rawf
Cf2py intent(in) outf
Cf2py intent(in) broadf
Cf2py intent(in) snrtype
Cf2py intent(in) decfac
Cf2py intent(in) errf

c change to 132 characters for inputs

      integer maxsat, maxeph, maxob
      parameter (maxsat = 150)
      parameter (maxeph = 50)
      parameter (maxob = 20)
      real*8 c
      parameter (c = 0.299792458D+09)     

      integer stderr,iuseful,k
      parameter (stderr=6)
      character*80 inline
      character*4 station
      character*2  prn_pickc
      character*1 satID(maxsat)
      integer  nobs, itime(5), prn(maxsat), numsat, flag, sec,
     +   msec, lli(maxob,maxsat), iprn, ios, itrack,  i, 
     .   iobs(maxsat), gpsweek, the_hour, prn_pick, current_hour,npts,
     .  fileIN, fileOUT,iymd(3),errid, rinex_year, rinex_doy, 
     .  nav_doy, nav_year, idec,itod
      real*8  obs(maxob,maxsat),  tod,North(3), East(3), 
     .   Up(3), azimuth, elev, staXYZ(3), tod_save, 
     .   s1,s2,xrec, yrec, zrec, tc, Lat,Long,Ht,
     .   bele(maxeph, maxsat, 28),s5
      logical eof, bad_point, keep_point
      logical debugging, decimate
c     Kristine M. Larson
c     version 2.0 new version - uses subroutines, fixed bug in az-el
c     verison 2.1 fixes bug in selection 77 (reading the LLI value)
c     version 2.2 fixed bug in reading the comment lines, 15sep07
c     version 2.3 added S5
c     version 2.5 distribution on gitHub
c     version 2.6 added moving site velocities, station marker name
c     version 2.7 fixed bug for reading files with < 5 observations
c     version 2.8 changed minimum observables from 10 to 15
c     version 2.9 19mar01 - allow up to 20 observables, changed code
c       to read the header and the data block
c     version 2.10 check dates on input files to make sure they are
c           in agreement
c
c     version 3.0 removed moving sites, blockIIRM (snr77) feature 
c     etc to streamline for use in python.  added decimation factor

c     common block for the GPS broadcast ephemeris

      real*8 naode,ncrs, ndeltan, nem0, ncuc,ne, ncus,
     .  nroota,ntoe,ncic, nomega0,
     .  ncis, nxi0, ncrc, nper0,nomegad,ntoc, nxclk,
     .  nsclk, nridot,nistano
c    change dimension to place for ephemeris each hour
      common/new_borbit/naode(24,maxsat),ncrs(24,maxsat),
     .  ndeltan(24,maxsat), nem0(24,maxsat), ncuc(24,maxsat),
     .  ne(24,maxsat),ncus(24,maxsat),nroota(24,maxsat),
     .  ntoe(24,maxsat),ncic(24,maxsat),nomega0(24,maxsat),
     .  ncis(24,maxsat),nxi0(24,maxsat),
     .  ncrc(24,maxsat),nper0(24,maxsat),
     .  nomegad(24,maxsat),ntoc(24,maxsat),
     .  nxclk(24,maxsat,3),nsclk(24,maxsat,3),
     .  nridot(24,maxsat), nistano(24,maxsat)

c     was not sure about inputs - so use short names there
      mess = 'message'
      errid = 53
      fileIN = 12
      fileOUT = 55

      broadfile = broadf
      rawfilename = rawf
      outfilename = outf
c     open a file so you can write out status messages 
      open(errid,file=errf,status='unknown',iostat=ios)
      write(errid,*) 'Broadcast:',broadf
      write(errid,*) 'RINEX file:',rawf
      write(errid,*) 'Output file:',outf
      write(errid,*) 'Selection:',snrtype

c     set some defaults - used for input and output file IDs
      READ (decfac, '(I2)') idec 
      write(errid,*) 'Decimation',decfac, idec
      decimate = .true.
      if (idec .eq. 0) then
          decimate = .false.
      endif
      debugging = .false.
      tod_save = 0.0
      npts = 0
      bad_point = .false.
c     prn_pickc = '99'
      prn_pickc = snrtype

c
c     figure out which option is being requested
      READ (prn_pickc, '(I2)') prn_pick

c     Check to see if broadcast file exists
      open(22,file=broadfile, status='old',iostat=ios)
      if (ios.ne.0) then
        write(errid,*)'ERROR:Problem opening navigation file'
        write(errid,*)'broadfile'
        close(22)
        return
      endif
      close(22)


c     read the header of the RINEX file, returning station coordinates
c     19mar01 - change to 20 observables
      call read_header_20obs(fileIN,rawfilename, xrec,yrec,zrec, 
     .  iobs,nobs,iymd,station,errid)
      write(errid,*) 'Coords',xrec, yrec, zrec
      write(errid,*) mess

      call name2ydoy(rawfilename,rinex_year, rinex_doy)

      call name2ydoy(broadfile,nav_year, nav_doy)

c     write(stderr,*)'The year in your filename : ', rinex_year
c     write(stderr,*)'The day of year in your filename: ', rinex_doy


c removed subroutine moving_sites bevacuse life is short
      if ((xrec+yrec+zrec) .eq.0) then
        mess='FATAL ERROR:No (useful) apriori coordinates - exiting'
        write(errid,*)mess
        mess='Fix the a priori coordinates in your header. '
        write(errid,*)mess
        return
      endif
      iuseful = 0
      do k = 6, 11
         if (iobs(k) .gt. 0) then
            iuseful = iuseful + 1
         endif
      enddo
      if (iuseful .eq. 0) then
        mess='FATAL ERROR:no SNR data were found in your file. This '
        write(errid,*)mess
        mess='usually this means you need to remake the RINEX file.'
        write(errid,*)mess
        mess='Please contact your local RINEX expert for help.'
        write(errid,*)mess

        return
      endif

c     if (iobs(6) .eq. 0) then
c       return
c     endif
      if (nobs .gt. 20) then
        mess = 'ERROR: this code only works for <= 20 obs types'
        write(errid,*)mess
        mess = 'try using -strip T when running rinex2snr'
        write(errid,*)mess
        return
      endif
      close(53)


c     read the broadcast ephemeris information
      call read_broadcast4 (broadfile, bele,iymd)
      call rearrange_bele(bele)

      call envTrans(xrec,yrec,zrec,staXYZ,Lat,Long,Ht,North,East,Up)
c     open output file
      open(fileOUT,file=outfilename, status='unknown')
      eof = .false.
      current_hour = 0
c     print*, 'S1 location:', iobs(6)
c     print*, 'S2 location:', iobs(7)
c     print*, 'S5 location:', iobs(8)
c     start reading the observation records
      do while (.not.eof) 
        inline = ' '
        read(fileIN,'(A80)', iostat=ios) inline
        if (ios.ne.0) goto 99 
        read(inline(1:32),'(5I3,X,I2,X,I3,4X,2I3)')
     +     (itime(i), i=1,5), sec, msec, flag, numsat
        if (itime(4) .ne.current_hour) then
          current_hour = itime(4)
        endif
c       seconds in the day
        tod = itime(4)*3600.0 + 60.0*itime(5) + sec
        itod = int(tod)
        if (tod.lt.tod_save) then
c         print*,'Time is going backwards or standing still'
c         print*,'Ignoring this record'
          bad_point = .true.
          tod_save = tod
        else
          bad_point = .false.
          tod_save = tod
        endif
        if (debugging) then
          print*, 'reading block ' 
          print*, inline(1:60)
        endif
c      19mar01 - expanding number of observables allowed
        call read_block_gps(fileIN, flag,inline,numsat,nobs,satID, 
     .    prn,obs,lli)
c       if flag has value 4, that means there were comment
c       lines, and those were skipped
c       print*, itod, itime(4),itime(5), sec 
        keep_point = .true.
        if (decimate) then
          if (mod(itod,idec) .ne.0) then
              keep_point = .false.
          endif
        endif
        if (keep_point) then
        if (flag .ne. 4) then
          call convert_time(itime,sec, msec, gpsweek, tc)
          do itrack = 1, numsat
c           only uses GPS satellites currently, skips over other
c           constellations
            if ((satID(itrack).eq.'G').or.(satID(itrack).eq.' ')) then
              the_hour = 1+nint(1.d0*itime(4) + itime(5)/60)
              if (the_hour > 24) the_hour = 24
              iprn = prn(itrack)
c             get azimuth and elevation angle
              call get_azel(tc, iprn, staXYZ,East,North,Up, 
     .          azimuth,elev,the_hour)
c             you can modify this to also pick up pseudoranges
c             these can be modfiied to store phas data. currently 0
              s1 = obs(iobs(6),itrack)
              s2 = obs(iobs(7),itrack)
c             check for S5
              if (iobs(8).ne.0) then
                s5 = obs(iobs(8),itrack)
              else
                s5=0
              endif
              if (s1.eq.0.d0 .and. s2.eq.0.d0) then
c                 no data, SNR so do not print it
              else
                call write_to_file(fileOUT, prn_pick, iprn, 
     .           elev,azimuth, tod, s1,s2, s5)
                 
                npts = npts + 1
              endif
            else
c             print*, 'skipping non-GPS satellite'
            endif
          enddo
        endif
        endif
      enddo
99    continue
      if (npts.eq.0) then
        write(stderr,*) 
     .   'You have been misled. There are no S1/S2 data in this file'
      endif
c     close input and output files
      close(fileIN)
      close(fileOUT)
      end

      subroutine write_to_file(outID, prn_pick, prn, elev, 
     . azimuth, tod, s1,s2, s5)
      implicit none

      integer maxsat, maxeph, maxob
      parameter (maxsat = 150)
      parameter (maxeph = 50)
      parameter (maxob = 20)
      real*8 c
      parameter (c = 0.299792458D+09)      

      real*8 s1, s2, tod, elev, azimuth, x,y, s5
      integer prn_pick, outID, prn
c     author: Kristine Larson
c     2020aug17 check for large (nonsense) SNR values
c
c     16jul15 added s5
c     this supports old option that printed out L1 and L2 phase
c     removed optino 77
c     no longer writing out reflection point. columns 5 and 6 are zero
      x = 0.d0
      y = 0.d0
c     make sure that you do not have huge SNR values which overrun the
c     fortran write statement
      call checkForNonsense(s1,s2,s5)

      if (prn_pick.eq.99.and.(elev.gt.5
     .  .and.elev.lt.30)) then
          write(outID,'(i3,  2f10.4, f10.0, 2f7.2, 3f7.2)' )
     .    prn, elev, azimuth, tod, x,y, s1, s2, s5
      elseif ( prn_pick.eq.50 .and.  elev.lt.10 ) then
        write(outID,'(i3,  2f10.4, f10.0, 2f7.2, 2f7.2)' )
     .    prn, elev, azimuth, tod, 0.d0,0.d0, s1, s2
c     all data above 5 degrees
      elseif ( prn_pick.eq.88 .and.  elev.gt.0 ) then
        write(outID,'(i3,  2f10.4, f10.0, 2f7.2, 3f7.2)' )
     .    prn, elev, azimuth, tod, x,y, s1, s2,s5
c     everything < 30
      elseif (  prn_pick.eq.66 .and. elev.lt.30 ) then
        write(outID,'(i3,  2f10.4, f10.0, 2f7.2, 3f7.2)' )
     .    prn, elev, azimuth, tod, 0.d0, 0.d0, s1, s2, s5
c       L2C data only - LLI indicator has to be a zero
c       assumes if no phase data, then it is not a good snr value
      elseif (prn.eq.prn_pick)  then
        write(outID,'(i3,  2f10.4, f10.0, 2f7.2, 3f7.2)' )
     .    prn, elev, azimuth, tod, x,y, s1, s2, s5
      endif
      end

      subroutine checkForNonsense(s1,s2,s5)
c     this should take care of nonsense values that overrun
c     the fortran write statements
c     2020 august 19
      real*8 s1,s2,s5

      if ((s1.gt.999).or.(s1.lt.0)) then
        s1=0
      endif
      if ((s2.gt.999).or.(s2.lt.0)) then
        s2=0
      endif
      if ((s5.gt.999).or.(s5.lt.0)) then
        s5=0
      endif
      end

      subroutine read_block_gps(fileID, flag,inline,numsat,nobs,satID,
     .  prn,obs,lli)
c     19mar01 KL
c     this was originally read_block_gnss.f
c     I transfered it over from the GNSS code - hopefully to save time
      implicit none

      integer maxsat, maxeph, maxob
      parameter (maxsat = 150)
      parameter (maxeph = 50)
      parameter (maxob = 20)
      real*8 c
      parameter (c = 0.299792458D+09)      

      character*1 char, satID(maxsat)
      integer fileID, i, itrack, flag, nobs, numsat
      integer prn(maxsat), ios
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
        if (numsat > 72) then
          print*, 'I cannot read more than 72 satellites'
          print*, 'Please stop launching them!'
          return
        endif
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
c           5 or fewer observable types
            else
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

      subroutine get_azel(tc, prn, stationXYZ,East,North,
     .  localv, azimuth,elev,ihr)
      implicit none
      integer jj, ierr,prn, ihr
      real*8 tc, SatPos(3), toffset, omeg, ghadot,
     . xnew, ynew, localv(3),grange, c,
     . azimuth, elev, North(3), East(3), stationXYZ(3), range2 

c     removed inc file since it only sent speed of light (m/sec
      c = 0.299792458D+09       
c     starting value for transmission offset in seconds
      toffset = 0.07
c     Earth Rotation
      ghadot = 7.2921151467d-5 ! rad/sec, using same one as ICD200
c do not need this many iterations - change to 3
      do jj = 1, 3
        call bcephX(tc-toffset, prn,SatPos,ierr,ihr)
        if (ierr.ne.0) then
          print*, 'orbit error'
        endif
        omeg = -ghadot*toffset
        xnew = SatPos(1)*dcos(omeg) - SatPos(2)*dsin(omeg)
        ynew = SatPos(1)*dsin(omeg) + SatPos(2)*dcos(omeg)
        range2= (xnew - stationXYZ(1))**2 + (ynew 
     . - stationXYZ(2))**2 + (SatPos(3)-stationXYZ(3))**2
        toffset = dsqrt(range2)/c
       enddo
       SatPos(1) =  xnew
       SatPos(2) =  ynew
       grange = dsqrt(range2)
       call azel(azimuth, elev, stationXYZ, East, North,
     .        localv, SatPos)
       end

      subroutine read_header_20obs(fileID,rawf,xrec,yrec,zrec,
     .  iobs,nobs,iymd,station,fid)
c     new version (19mar01) taken from my GNSS code
c     kristine larson
c     allows 20 observables
c     allow error message to be returned to main program
c     march 2021 change filename to 132 characters
      implicit none

      integer maxsat, maxeph, maxob
      parameter (maxsat = 150)
      parameter (maxeph = 50)
      parameter (maxob = 20)
      real*8 c
      parameter (c = 0.299792458D+09)       

      integer  i, fileID,fid
      character*132 rawf, mess
      character*80 line, dynfmt,errf
      logical  endofheader
      integer nobs,iobs(maxsat), iymd(3), ios
      character*2 key(maxsat)
      character*4 station
      real*8 xrec, yrec, zrec
c     returns receiver coordinates
c     station name is empty to start with
c     returned to main code
c     asssume station is at center of eaerth so as 
c     to trigger error if it is not found in the file
      xrec = 0
      yrec = 0
      zrec = 0
      station = '    '
      endofheader = .false.

      open(fileID,file=rawf, status='old',iostat=ios)
      if (ios.ne.0) then
        mess = 'ERROR:problem opening RINEX file'
        write(fid,*)mess
        return
      endif
      do while (.not.endofheader)
c     KL 18mar05, fixed bug on nobs
        read (fileID,'(a80)') line
        if (line(61:80).eq.'# / TYPES OF OBSERV') then
          read(line, fmt='(I6)') nobs
c         exit if more than 20 observables
          if (nobs.gt.20) then
             mess ='ERROR:this code only supports <=20 observ types'
             write(fid,*) mess
             write(fid,*) nobs 
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
          write(fid,*)'NUMBER OF OBSERVABLES ', nobs
        else if (line(61:80).eq.'APPROX POSITION XYZ') then
          read(line, fmt= '(3f14.4)') xrec, yrec, zrec
          if (xrec.eq.0) then
            mess = 'ERROR:receiver coordinates required'
            write(fid,*)mess
            return
          endif
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
      write(fid,*)'FOUND END OF HEADER'
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

       subroutine azel(azimuth, elev, StaXYZ, East, North,
     .                  Staup, SatPos)
        implicit none
c      author: kristine larson
c      returns azimuth and elevation angle in degrees
c      StaXYZ is the cartesian coordinates of station (meters)
c      SatPos is X, Y, Z satellite coordinates (meters)
c ----------------------------------------------------
      double precision elev, azimuth,pi
      double precision StaXYZ(3),  East(3),
     . North(3), Staup(3), sta2sat(3), Mstation, Msat,
     . sta2sat_N, sta2sat_E, UdotS, zenith,SatPos(3)

c ----------------------------------------------------

c ... find azimuth/elevation of satellite relative
c ... to the reference station (station(3))
        pi = 4.0*datan(1.d0)
        sta2sat(1) = SatPos(1) - StaXYZ(1)
        sta2sat(2) = SatPos(2) - StaXYZ(2)
        sta2sat(3) = SatPos(3) - StaXYZ(3)

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

      subroutine bcephX(tc,isv,recf,ierr,hr)
c     broadcast ephemeris evaluation routine
c     taken from icd-gps-200, table 20-iv
c     "elements of coordinate systems"
c     all angular values must be converted to radians
c
c     returns satellite coordinates in METERS
      implicit real*8 (a-h,o-z)
      save
      integer maxsat
      parameter (maxsat=150)
      dimension recf(3)
      integer hr, izh

      real*8 naode,ncrs, ndeltan, nem0, ncuc,ne, ncus,
     .  nroota,ntoe,ncic, nomega0,
     .  ncis, nxi0, ncrc, nper0,nomegad,ntoc, nxclk,
     .  nsclk, nridot,nistano
c    change dimension to place for ephemeris each hour
      common/new_borbit/naode(24,maxsat),ncrs(24,maxsat),
     .  ndeltan(24,maxsat), nem0(24,maxsat), ncuc(24,maxsat),
     .  ne(24,maxsat),ncus(24,maxsat),nroota(24,maxsat),
     .  ntoe(24,maxsat),ncic(24,maxsat),nomega0(24,maxsat),
     .  ncis(24,maxsat),nxi0(24,maxsat),
     .  ncrc(24,maxsat),nper0(24,maxsat),
     .  nomegad(24,maxsat),ntoc(24,maxsat),
     .  nxclk(24,maxsat,3),nsclk(24,maxsat,3),
     .  nridot(24,maxsat), nistano(24,maxsat)
c     include 'new_orbit.inc'
      xmu = 3.986005d+14
      ghadot = 7.2921151467d-5
      izh = 1
      pi = 3.1415926535898d0
      twopi=pi+pi
      ierr=0
c     isv and j are the PRN numbers
      j=isv
      if(j.eq.0)then
        ierr=1
        return
      end if
      a=nroota(hr,j)**2
      en0=dsqrt(xmu/a**3)
      tk=tc-ntoe(hr,j)
      if(tk.gt.302400.d0)tk=tk-604800.d0
      if(tk.lt.-302400.d0)tk=tk+604800.d0
      en=en0+ndeltan(hr,j)
      emk=nem0(hr,j)+en*tk
      emk=dmod(emk,twopi)
      emk=dmod(emk+twopi,twopi)
      ek=emk
      ekdot=en
c
c   solve kepler's equation
c
      small = 0.00000000000001
      do 100 i=1,100
         sine=dsin(ek)
         cose=dcos(ek)
         ek=emk+ne(hr,j)*sine
         if (dabs(ek-saveek).lt.small) goto 101
         ekdot=en+ne(hr,j)*cose*ekdot
         saveek = ek
100   continue

101   continue
      roote=dsqrt(1.d0-ne(hr,j)**2)
      truea=datan2(roote*sine,cose-ne(hr,j))
      dlat=truea+nper0(hr,j)
      twolat=dmod(dlat+dlat,twopi)
      sin2p=dsin(twolat)
      cos2p=dcos(twolat)
      corlat=izh*(ncuc(hr,j)*cos2p+ncus(hr,j)*sin2p)
      corr=  izh*(ncrc(hr,j)*cos2p+ncrs(hr,j)*sin2p)
      cori=  izh*(ncic(hr,j)*cos2p+ncis(hr,j)*sin2p)
      dlat=dmod(dlat+corlat,twopi)
      rk=a*(1.d0-ne(hr,j)*cose) + corr
      xik=nxi0(hr,j) + cori + nridot(hr,j)*tk
      coslat=dcos(dlat)
      sinlat=dsin(dlat)
      xk=rk*coslat
      yk=rk*sinlat
      omegak=dmod(nomega0(hr,j)+ 
     .  (nomegad(hr,j)-ghadot)*tk-ghadot*
     .  ntoe(hr,j),twopi)
      coso=dcos(omegak)
      sino=dsin(omegak)
      cosi=dcos(xik)
      sini=dsin(xik)
c ecef coordinates of satellite in meters
      recf(1)=xk*coso-yk*cosi*sino
      recf(2)=xk*sino+yk*cosi*coso
      recf(3)=yk*sini
c     end bcxyz
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
      implicit none 
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
      subroutine read_broadcast4(filename, bele,iymd)
      implicit none
c     not sure if this is read but i am having 
c     filename be up to 132 characters

      integer maxsat, maxeph, maxob
      parameter (maxsat = 150)
      parameter (maxeph = 50)
      parameter (maxob = 20)
      real*8 c
      parameter (c = 0.299792458D+09)      

      character*80 temp
      character*132 filename, mess
      real*8 bele (maxeph,maxsat,28), rt1, rt2, rt3, rt4
      integer i, j, k, k1, iymd(3),year4ch,
     .  iprn, file(maxsat), it1, it2, it3, it4, it5, iversion, ios
      do i = 1, maxsat
        file(i) = 0
        do j=1,maxeph 
          bele(j, i, 28) = 99
        enddo
      enddo

      open (44, file = filename, status='old',iostat=ios ) 
      if (ios.eq.0) then
      else
        mess= 'ERROR:problems with navfile'
        return
      endif 
      read(44, '(i6)') iversion 
      if (iversion.eq.2.or.iversion.eq.1) then
102     read(44, '(60x, a20)') temp
        if (temp(1:13).eq.'END OF HEADER'.or.
     .   temp(1:8).eq.'        ') then
        else
          goto 102
        endif
      else
        mess= 'ERROR can only read version 1 or 2'
        return
      endif
12    read( 44, '(i2, 5i3, f5.1, 3d19.12)',err=14,iostat=ios) iprn, it1,
     .  it2, it3, it4, it5, rt1, rt2, rt3, rt4
      if (ios.ne.0) goto 14
      file(iprn) = file(iprn) + 1
      if (file(iprn).gt.maxeph) then 
        print*, 'MORE THAN 50 ephemeris for PRN', iprn
        goto 14
      endif
      do j = 1, 6
        k1 = 4*(j-1) + 1
        read( 44, '(3x, 4d19.12)', err=14, iostat=ios) 
     .       ( bele(file(iprn), iprn , k), k = k1, k1+3)
        if (ios.ne.0) goto 14
      enddo
      if (iversion.eq.2) read(44,'(a60)') temp
c     put decimal hour into the space in broadcast 
c     element 28, i.e. hour plus minute/60
c     if the year month and day are NOT the same as the observation
c     file, put a 99 in this space
      if (it1 .lt. 80) then
        year4ch = it1 + 2000
      else
        year4ch = it1 + 1900
      endif
      if (iymd(1) .eq. year4ch .and. (iymd(2) .eq. it2 .and. 
     .   iymd(3) .eq.it3)) then
        bele(file(iprn), iprn, 28) = it4 + it5/60
      else
c       this is common, so do not print it out. but basically
c       we are going to ignore broadcast messages on the next day
c       print*, 'Ephemeris message on the wrong day' 
c       print*, it1, it2, it3, it4, it5, 'PRN ', iprn
      endif
      goto 12
14    continue
      return
      end
      subroutine rearrange_bele(bele)
      implicit none

      integer maxsat, maxeph, maxob
      parameter (maxsat = 150)
      parameter (maxeph = 50)
      parameter (maxob = 20)
      real*8 c
      parameter (c = 0.299792458D+09)       

      integer j, ihr, k, isat

      real*8 naode,ncrs, ndeltan, nem0, ncuc,ne, ncus,
     .  nroota,ntoe,ncic, nomega0,
     .  ncis, nxi0, ncrc, nper0,nomegad,ntoc, nxclk,
     .  nsclk, nridot,nistano
c    change dimension to place for ephemeris each hour
      common/new_borbit/naode(24,maxsat),ncrs(24,maxsat),
     .  ndeltan(24,maxsat), nem0(24,maxsat), ncuc(24,maxsat),
     .  ne(24,maxsat),ncus(24,maxsat),nroota(24,maxsat),
     .  ntoe(24,maxsat),ncic(24,maxsat),nomega0(24,maxsat),
     .  ncis(24,maxsat),nxi0(24,maxsat),
     .  ncrc(24,maxsat),nper0(24,maxsat),
     .  nomegad(24,maxsat),ntoc(24,maxsat),
     .  nxclk(24,maxsat,3),nsclk(24,maxsat,3),
     .  nridot(24,maxsat), nistano(24,maxsat)

c     include 'new_orbit.inc'
      real*8 bele(maxeph, maxsat, 28)
      do isat = 1, maxsat
        do j=1,24
c         subtract one hour because ephem 1 goes to hour 0
          ihr = j-1
          call closest_eph(ihr, bele, isat,  k)
          naode(j,isat)=   bele(k, isat, 1)
          ncrs(j,isat)=    bele(k, isat, 2)
          ndeltan(j,isat)= bele(k, isat, 3)
          nem0(j,isat)=    bele(k, isat, 4)
          ncuc(j,isat)=    bele(k, isat, 5)
          ne(j,isat)=      bele(k, isat, 6)
          ncus(j,isat)=    bele(k, isat, 7)
          nroota(j,isat)=  bele(k, isat, 8)
          ntoe(j,isat)=    bele(k, isat, 9)
          ncic(j,isat)=    bele(k, isat, 10)
          nomega0(j,isat)= bele(k, isat, 11)
          ncis(j,isat)=    bele(k, isat, 12)
          nxi0(j,isat)=    bele(k, isat, 13)
          ncrc(j,isat)=    bele(k, isat, 14)
          nper0(j,isat)=   bele(k, isat, 15)
          nomegad(j,isat)= bele(k, isat, 16)
          nridot(j,isat)=  bele(k, isat, 17)
        enddo
      enddo
      end
      subroutine closest_eph(ihr, bele, isat, whichEphem)
      implicit none

      integer maxsat, maxeph, maxob
      parameter (maxsat = 150)
      parameter (maxeph = 50)
      parameter (maxob = 20)
      real*8 c
      parameter (c = 0.299792458D+09)       

      integer  itest, ihr, j,whichEphem, minval, mv,isat
      real*8 bele(maxeph, maxsat, 28)
c     want ephemeris closest to ihr
      minval = 15
      whichEphem = 1
      do j=1, maxeph
         itest = int(bele(j,isat,28))
         if (itest .ge.0 .or. itest .lt. 24) then
           mv =  abs(itest -ihr) 
           if (mv .lt. minval) then 
             minval = mv 
             whichEphem = j
           endif
         endif
      enddo  
      end



      subroutine envTrans(xrec,yrec,zrec,stationXYZ, Lat,Long, 
     .  Height, North, East,Up)
c     all in meters
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
c     returns tc, which is time in gps seconds (real*8)
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

      subroutine name2ydoy(rawfilename,year,doy)
      character*132 rawfilename
      integer ts, k1, k2,year,doy
      ts = index(rawfilename,' ')
      k1 = ts-13 + 5
      k2 = k1 +2
      read (rawfilename(k1:k2),'(I3)') doy
      read (rawfilename(k1+5:k1+6),'(I2)') year
c      in the case that you hae ancient data from the 1990s
      if (year .lt. 74) then
        year = year + 2000
      else
        year = year + 1900
      endif

      end

C END OF FILE GPSSNR.F
