# Files and File Formats

You need two environment variables: REFL_CODE and ORBITS. If you are using 
the jupyter notebooks or the docker, they are defined for you. If you are working
with pypi or github install, you must define them EVERY TIME YOU USE THE CODE.
This is most easily done by setting them in your setup script, which on my machine
is called .bashrc.

## GPS/GNSS Data Formats

Input observation formats: the code only 
recognizes [RINEX 2.11](https://www.ngs.noaa.gov/CORS/RINEX211.txt), RINEX 3 and NMEA input files.

**RINEX 2.11**

*We require that you use lower case filenames.* These are the standard at global archives.
They must have SNR data in them (S1, S2, etc) and have the receiver coordinates in the header.
The files should follow these naming rules:

- all lowercase
- station name (4 characters) followed by day of year (3 characters) then 0.yyo where yy is the two character year.
- Example: algo0500.21o where station name is algo on day of year 50 from the year 2021

Example filename : onsa0500.22o

**RINEX 3**

While we allow RINEX 3 files, we do not read the file itself - we rely on the <code>gfzrnx</code> 
utility developed by Thomas Nischan at GFZ to translate from RINEX 3+ to RINEX 2.11
If you have ss second RINEX 3 files, they should be all upper case (except for the extension rnx or crx).

* station name (9 characters where the last 3 characters are the country), underscore
* capital R or capital S , with underscore on either side
* four character year
* three character day of year
* four zeroes, underscore,
* 01D, underscore
* ssS, underscore, M0.
* followed by rnx (crx if it is Hatanaka format).

01D means it is one day. Some of the other parts of the very long station file name are no
doubt useful, but they are not recognized by this code. By convention, these files may be
gzipped but not unix compressed. You cannot use rinex2snr to translate RINEX 3 file unless they
have the 01D naming convention. If you want a generic translation program, try rinex3_rinex2.

Example filename: ONSA00SWE_R_20213050000_01D_30S_MO.rnx

**NMEA**

NMEA formats can be translated to SNR using <code>nmea2snr</code>.
Inputs are similar to <code>rinex2snr</code>: 4char station name, year, and day of year
NMEA files are assumed to be stored as:

$REFL_CODE + /nmea/ABCD/2021/ABCD0030.21.A

for station ABCD in year 2021 and day of year 3.

NMEA files may be gzipped.

nmea2snr needs better in-code documentation.

**Orbit files**

We have tried our best to make the orbit files relatively invisible to users.
But for the sake of completeness, we are either using broadcast navigation files in 
the RINEX 2.11 format
or precise orbits in the sp3 format.   

## Where Files are Stored


File structure for station abcd in the year YYYY (last two characters YY), doy DDD:

- REFL_CODE/input/abcd.json - instructions for gnssir analysis, refraction files

- REFL_CODE/YYYY/snr/abcd/abcdDDD0.YY.snr66  - SNR files 

- REFL_CODE/YYYY/rinex/abcd/  - RINEX files can be stored here

- REFL_CODE/YYYY/results/abcd/DDD.txt  Lomb Scargle analysis goes here

- REFL_CODE/YYYY/phase/abcd/DDD.txt  phase analysis 

- REFL_CODE/Files/ - various output files and plots will be placed here

- ORBITS/YYYY/nav/autoDDD0.YYn - GPS broadcast orbit file 

- ORBITS/YYYY/sp3/ - sp3 files of orbits - these use names from the archives.

RINEX files downloaded from archives are not stored by this code. In fact, quite the opposite. If they are being translated, 
they are deleted. Do not keep your only copy of RINEX files in your default directory.

You do not need precise orbits to do GNSS-IR. We only use them as a convenience.
Generally we use multi-GNSS sp3 files. that are defined as:

Some of the utilities and environmental products code store files in REFL_CODE/Files
The locations of these files are always provided in the screen output.

The inputs to <code>gnssir</code> are generally stored in the REFL_CODE/input folder.
This primarily means the Lomb Scargle data analysis inputs, i.e. 
the "json" files, e.g. p041.json for station p041.
It also includes the refraction file (p041_refr.txt) that is 
created automatically. This calculation 
requires a set of parameters stored in a "pickle" format, gpt_1wA.pickle. 
It should be automatically stored for you.

I don't know why - but the station_pos.db file is stored in REFL_CODE/Files
As it is an input file, we should probably move it. This file should be required 
for the code to work, but it is a time saving if you are using a station file
that is in this database. It is based on a set of coordinates provided by the University 
of Nevada Reno.  You can query it online with <code>query_unr</code>. It is entirely 
possible that you are using a station name that is shared with another GNSS site. In 
those cases you will need to input your lat, long, and ellipsoidal height yourself.

## The SNR data format

The snr options are mostly based on the need to remove the "direct" signal. This is
not related to a specific site mask and that is why the most frequently used
options (99 and 66) have a maximum elevation angle of 30 degrees. The
azimuth-specific mask is decided later when you run **gnssir**.  The SNR choices are:

- 66 is elevation angles less than 30 degrees (**this is the default**)
- 99 is elevation angles of 5-30 degrees
- 88 is all data
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


## GNSS frequencies

- 1,2,20, and 5 are GPS L1, L2, L2C, and L5 

- 101,102 are Glonass L1 and L2

- 201, 205, 206, 207, 208: Galileo frequencies, which are
set as 1575.420, 1176.450, 1278.70, 1207.140, 1191.795 MHz

- 302, 306, 307 : Beidou frequencies, defined as 1561.098, 1207.14, 1268.52 MHz


## Additional files

- EGM96geoidDATA.mat is stored in REFL_CODE/Files
- station_pos.db is stored in REFL_CODE/Files 
- gpt_1wA.pickle is stored in REFL_CODE/input

We will be moving these to a single place after our short course!
