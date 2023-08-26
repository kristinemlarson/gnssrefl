# rinex2snr  

The goal of this code is to extract SNR data from a GNSS RINEX data file.
A RINEX file has extraneous information in it (which we will throw out) - and it  
does not provide some of the information needed for reflectometry (e.g. elevation and azimuth angles). 
For the latter step, we need an **orbit** file. The code will pick that up for you.

- [Information on file formats](https://gnssrefl.readthedocs.io/en/latest/pages/file_structure.html)

- [Information on specific rinex2snr inputs](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.rinex2snr_cl.html)

- [If you want to translate a NMEA file](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.nmea2snr_cl.html)


<code>rinex2snr</code> assumes the files are in the RINEX format.  We support two kinds of RINEX 
files, which we discuss separately:


**RINEX 2.11**

The four character lowercase station name, year, and day of year must be specified.

Example:

<code>rinex2snr p041 2020 132</code>

The default archives checked are sopac and unavco. 

**Changed 2023 May 20**
Before day of year 137, year 2021, the default orbit file used was GPS only.
After that date, the multi-GNSS orbit product from GFZ is used. If you would like to continue
using GPS only, you should set -orb to gps.

For up to date listings of approved archives and orbit sources, 
[please see here](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.rinex2snr_cl.html)

To analyze your own data, i.e. you should have the RINEX file in your current directory, p0411320.20o
or in $REFL_CODE/2020/rinex/p041

<code>rinex2snr p041 2020 132 -nolook T</code>

If you want to specify a non-default archive:

<code>rinex2snr tgho 2020 132 -archive nz</code>

Example for the Japanese GNSS archive:

<code> rinex2snr 940050 2021 31 -archive jp </code>

Note: Japanese stations have six characters.

Example for multi-day translation

<code>rinex2snr tgho 2019 1  -archive nz -doy_end 365</code>
 
**RINEX 3**

RINEX 3 files have 9 character station names:

<code>rinex2snr mchl00aus 2022 55 -archive ga -orb gnss</code>

The output of the code will be four characters and lowercase.
You can also specify sample rate (-srate) and the S vs R file convention (-stream).

Other examples:

<code>rinex2snr onsa00swe 2020 298</code>

<code>rinex2snr pots00deu 2020 298 -archive bkg -stream R</code>

<code>rinex2snr mchl00aus 2022 55 -archive ga</code>


**Frequently asked questions**

What is the difference between -rate and -srate? The rate input is a string that tells the 
code which folder you want to use at the archive, as the data are almost always segregated in some way.
The srate input is only for RINEX 3 files and is needed for the correct filename.

What if you have high-rate (e.g. 1 sec) RINEX files, but you want 5 sec data? <code>-dec 5</code>

What if you want to use high-rate data?**  <code>-rate high</code>

What if you have a SNR file, but want to make a new one?  <code>-overwrite T </code>

[For more information on file formats, signals, conventions](https://gnssrefl.readthedocs.io/en/latest/pages/file_structure.html)


