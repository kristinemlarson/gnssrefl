# rinex2snr  

The goal of this code is to extract SNR data from a GNSS RINEX data file.
A RINEX file has extraneous information in it (which we will throw out) - and it  
does not provide some of the information needed for reflectometry (e.g. elevation and azimuth angles). 
For the latter step, we need an **orbit** file. The code will pick that up for you.

- [Information on file formats](https://gnssrefl.readthedocs.io/en/latest/pages/file_structure.html)

- [Information on specific rinex2snr inputs](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.rinex2snr_cl.html)


<code>rinex2snr</code> assumes the files are in the RINEX 2.11 format at one of the global archives. 
The four character station name, year, and day of year must be specified.

Example:

<code>rinex2snr p041 2020 132</code>

The default archives checked are sopac and unavco. The default orbit file is GPS only.
For up to date listings of approved archives and orbit sources, 
[please see here](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.rinex2snr_cl.html)

To analyze your own data, i.e. you have the RINEX file in your default directory, p0411320.20o

<code>rinex2snr p041 2020 132 -nolook T</code>


If you want to specify the archive:

<code>rinex2snr tgho 2020 132 -archive nz</code>

Example for the Japanese GNSS archive:

<code> rinex2snr 940050 2021 31 -archive jp </code>


Example for multi-day translation

<code>rinex2snr tgho 2019 1  -archive nz -doy_end 365</code>
 
Multi-GNSS: 

<code>rinex2snr mchl00aus 2022 55 -archive ga -orb gnss</code>

RINEX 3 Example calls:

<code>rinex2snr onsa00swe 2020 298</code>

<code>rinex2snr pots00deu 2020 298 -archive bkg -stream R</code>

<code>rinex2snr mchl00aus 2022 55 -archive ga</code>


**Frequently used options:**

**What if you have high-rate (e.g. 1 sec) RINEX files, but you want 5 sec data?** <code>-dec 5</code>

**What if you want to use high-rate data?**  <code>-rate high</code>


[For more information on file formats, signals, conventions](https://gnssrefl.readthedocs.io/en/latest/pages/file_structure.html)


