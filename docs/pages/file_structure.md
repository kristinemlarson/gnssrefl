# **Files and File Formats**

*GPS/GNSS Data*

Input observation formats: the code only recognizes RINEX 2.11, RINEX 3+ and NMEA input files.

*We require that you use lower case filenames.* These are the standard at global archives.


Warning: while we allow RINEX 3+, we do not read the file itself - we rely on the <code>gfzrnx</code> 
utility developed by Thomas Nischan at GFZ to translate from RINEX 3+ to RINEX 2.11

Input orbit files: we have tried our best to make the orbit files relatively invisible to users.
But for the sake of completeness, we are either using broadcast navigation files in the RINEX 2.11 format
or precise orbits in the sp3 format.   


**File structure for station abcd in the year YYYY (last two characters YY), doy DDD:**

- REFL_CODE/input/abcd.json - instructions for gnssir analysis, refraction files

- REFL_CODE/YYYY/snr/abcd/abcdDDD0.YY.snr66  - SNR files 

- REFL_CODE/YYYY/results/abcd/DDD.txt  Lomb Scargle analysis 

- REFL_CODE/YYYY/phase/abcd/DDD.txt  phase analysis 

- REFL_CODE/Files/ - various output files and plots will be placed here

- ORBITS/YYYY/nav/autoDDD0.YYn - GPS broadcast orbit file 

- ORBITS/YYYY/sp3/ - sp3 files of orbits - these use names from the archives.

RINEX files are not stored by this code. In fact, quite the opposite. If they are being translated, 
they are deleted. Do not keep your only copy of RINEX files in your default directory.


You do not need precise orbits to do GNSS-IR. We only use them as a convenience.
Generally we use multi-GNSS sp3 files. that are defined as:

**Details about the SNR data format:**

The snr options are mostly based on the need to remove the "direct" signal. This is
not related to a specific site mask and that is why the most frequently used
options (99 and 66) have a maximum elevation angle of 30 degrees. The
azimuth-specific mask is decided later when you run **gnssir**.  The SNR choices are:

- 66 is elevation angles less than 30 degrees (**this is the default**)
- 99 is elevation angles of 5-30 degrees
- 88 is elevation angles of 5-90 degrees
- 50 is elevation angles less than 10 degrees (good for very tall sites, high-rate applications)

66,99, etc are not good names for files. And for this I apologize. It is too late to change them now.

The columns in the SNR data are defined as:

<PRE>
1. Satellite number (remember 100 is added for Glonass, etc)
2. Elevation angle, degrees
3. Azimuth angle, degrees
4. Seconds of the day, GPS time
5. elevation angle rate of change, degrees/sec.
6.  S6 SNR on L6
7.  S1 SNR on L1
8.  S2 SNR on L2
9.  S5 SNR on L5
10. S7 SNR on L7
11. S8 SNR on L8
</PRE>

The unit for all SNR data is dB-Hz.

**Our names for the GNSS frequencies**

- 1,2,20, and 5 are GPS L1, L2, L2C, and L5 

L2 and L2C are the same frequency - but we use different numbers in this code so that
one can *only* use L2C satellites if desired. 

- 101,102 are Glonass L1 and L2

- 201, 205, 206, 207, 208: Galileo frequencies, which are
set as 1575.420, 1176.450, 1278.70, 1207.140, 1191.795 MHz

- 302, 306, 307 : Beidou frequencies, defined as 1561.098, 1207.14, 1268.52 MHz

