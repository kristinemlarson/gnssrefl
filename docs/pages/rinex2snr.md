# rinex2snr  
Extracting SNR data from RINEX/NMEA files <a name="module1"></a>

The international standard for sharing GNSS data is 
called the [RINEX format](https://www.ngs.noaa.gov/CORS/RINEX211.txt). (If you are using NMEA files, please see the bottom of this section). 
A RINEX file has extraneous information in it (which we will throw out) - and it 
does not provide some of the information needed for reflectometry (e.g. elevation and azimuth angles). 
The first task you have in GNSS-IR is to translate from RINEX into what I will call 
the **SNR format**. The latter will include azimuth and elevation angles. To compute these 
angles you will need an **orbit** file. <code>rinex2snr</code> will try to get an orbit file for you. It will save
those orbit files in case you want to use them at some later date. You can override the default orbit 
choice by selections given below.

There is no reason to save ALL the RINEX data as the reflections are only useful at the lower elevation
angles. The default is to save all data with elevation lower than 30 degrees (this is called SNR format 66).
Another SNR choice is 99, which saves elevation angle data between 5 and 30.  
SNR choice 88 will save all data from 5 to 90 degrees.

You can run <code>rinex2snr</code> at the command line. The default version 
is RINEX 2.11. The required inputs are:

- station name
- year
- day of year

Examples:

<code>rinex2snr p041 2020 132</code>

For up to date listings of approved archives and orbit sources, 
[please see here](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.rinex2snr_cl.html)

To analyze your own data, set -nol True

**Example setting the archive:**

<code>rinex2snr tgho 2020 132 -archive nz</code>

**Example using the Japanese GNSS archive:**

<code> rinex2snr 940050 2021 31 -archive jp </code>

We use the last four characters as the station name.

**Run the code for all the data for any year**

<code>rinex2snr tgho 2019 1  -archive nz -doy_end 365</code>
 
**Examples using RINEX 3:**

If your station name has 9 characters (lower case please), 
the code assumes you are looking for a RINEX 3 file. 
Note: the code will store the SNR data using the normal
4 character name. *You must install the gfzrnx executable 
that translates RINEX 3 to RINEX 2.11 to use RINEX 3 files in 
this code.* If you followed the instructions for installation, this 
is already taken care of.

<code>rinex2snr</code> currently supports RINEX3 for 30 second data at :

- bev
- bkg
- bfg
- cddis
- epn
- ga
- gfz
- nrcan
- sonel
- unavco

Example calls:

<code>rinex2snr onsa00swe 2020 298</code>

<code>rinex2snr at0100usa 2020 55</code>

<code>rinex2snr pots00deu 2020 298 -archive bkg</code>

<code>rinex2snr mchl00aus 2022 55 -archive ga</code>

RINEX 3 has a file ID parameter that is a 
nuisance. If you know yours, you can set it 
with <code>-stream R</code> or <code>-stream S</code>. 
I usually look for both files without you having to set it. 

The snr options are mostly based on the need to remove the "direct" signal. This is 
not related to a specific site mask and that is why the most frequently used 
options (99 and 66) have a maximum elevation angle of 30 degrees. The
azimuth-specific mask is decided later when you run <code>gnssir</code>.  The SNR choices are:

- 66 is elevation angles less than 30 degrees (**this is the default**)
- 99 is elevation angles of 5-30 degrees  
- 88 is elevation angles of 5-90 degrees
- 50 is elevation angles less than 10 degrees (good for very tall sites, high-rate applications)

**More rinex2snr options:**

*orbit file options for general users:*

- gps : will use GPS broadcast orbits (**this is the default**)
- gps+glo : uses rapid GFZ orbits
- gnss : uses GFZ orbits, which is multi-GNSS (available in 3-4 days?)
- rapid : uses GFZ multi-GNSS rapid orbits, available in ~1 day
- ultra : since mid-2021, we can use multi-GNSS near realtime orbits from GFZ

*orbit file options for experts:*

- nav : GPS broadcast, perfectly adequate for reflectometry. 
- igs : IGS precise, GPS only
- igr : IGS rapid, GPS only
- jax : JAXA, GPS + Glonass, reliably within a few days, missing block III GPS satellites
- gbm : GFZ Potsdam, multi-GNSS, not rapid (GPS, Galileo,Glonass, Beidou)
- grg: French group, GPS, Galileo and Glonass, not rapid
- esa : ESA, multi-GNSS
- gfr : GFZ rapid, GPS, Galileo and Glonass, since May 17 2021 
- wum : Wuhan, multi-GNSS (precise+prediction, GPS,Galileo,Glonass,Beidou)
- ultra : GFZ ultra rapid (GPS, Galileo, Glonass), since May 17, 2021 

We are likely to add access to multi-GNSS broadcast 
orbits, but for now you can use the 
ultra orbit option. Although it is provided every three 
hours, we currently only download the 
file from midnite (hour 0).



**What if you have high-rate (e.g. 1 sec) RINEX files, but you want 5 sec data?** <code>-dec 5</code>

**What if you want to use high-rate data?**  <code>-rate high</code>

If you invoke this flag, you need to specify the archive. Your choices for high-rate RINEX 2.11 data are:

- unavco 
- cddis
- nrcan  

For RINEX 3 high-rate data:

- cddis
- ga 
- bkg


**Output SNR file format**

To columns are defined as:

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

The unit for all SNR data is dB-Hz.

**Our names for the GNSS frequencies**

- 1,2,20, and 5 are GPS L1, L2, L2C, and L5 (L2 and L2C are the same frequency - but we use different numbers in this code so that 
one can *only* use L2C if wished)
- 101,102 are Glonass L1 and L2
- 201, 205, 206, 207, 208: Galileo frequencies, which are 
set as 1575.420, 1176.450, 1278.70, 1207.140, 1191.795 MHz
- 302, 306, 307 : Beidou frequencies, defined as 1561.098, 1207.14, 1268.52 MHz

**What if you want to analyze your own data?**

Put your RINEX 2.11 files in the directory where you are going to run the code.

They must have SNR data in them (S1, S2, etc) and have the receiver coordinates in the header.
The files should follow these naming rules:

- all lowercase
- station name (4 characters) followed by day of year (3 characters) then 0.yyo where yy is the two character year.
- Example: algo0500.21o where station name is algo on day of year 50 from the year 2021

<code>rinex2snr algo 2021 50 -nolook True</code>

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

<code>rinex2snr onsa00swe 2021 305 -nolook True </code>

If you have something other than 30 second sampling, use <code>-samplerate</code>.

The RINEX inputs are always deleted, so do not put your only copy of the files in the working directory.
Please note: we are using the publicly available <code>gfzrnx</code> code to convert RINEX 3 files into RINEX 2.11 files. 
If you do not have <code>gfzrnx</code> installed, you will not be able to use RINEX 3 files.

It is also allowed to put your 
RINEX files into $REFL_CODE/YYYY/rinex/ssss where YYYY is the year 
and ssss is the four character station name. The advantage of doing 
this is that your RINEX files will not be deleted.

The makan option (-mk True) follows entirely different rules for file storage which I will not 
describe here. 

<HR>

NMEA formats can be translated to SNR using <code>nmea2snr</code>.
Inputs are similar to <code>rinex2snr</code>: 4char station name, year, and day of year
NMEA files are assumed to be stored as:

$REFL_CODE + /nmea/ABCD/2021/ABCD0030.21.A

for station ABCD in year 2021 and day of year 3. 

NMEA files may be gzipped.


