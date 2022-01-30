### invsnr

This is a utility for analyzing time-varying smooth surfaces with GNSS interferometric reflectometry.
The method was first introduced by [Joakim Strandberg](https://github.com/Ydmir) and his colleagues. This implementation of the method was written by 
[David Purnell](https://purnelldj.github.io/). It reads the inputs from the <code>gnssrefl</code> package (SNR files). 
It also does multiple frequencies and constellations.


### Inputs

**Required inputs:**

- station name (4 characters, lowercase)
- year
- day of year 
- frequency (e.g. L1, L2, L5, L1+L2, L1+L2+L5)

**Optional inputs:**

-pktnlim peak2noise ratio for QC
-constel CONSTEL (G,E, or R, which repesent GPS, Galileo, and Glonass)
-screenstats (True or False)
-tempres decimation value for your SNR file (seconds)
-polydeg polynomial degree for direct signal removal (default is 2)
-snrfit Do invsnr fit? True is the default
-doplot Send a summary plot to the screen? default is True
-doy_end day of year for multiday analysis
-lspfigs make LSP plots, default False. slow.
-snrfigs make SNR plots, default False. slow.
-knot_space value used for smoothing, in hours 

###Running the code

Follow these steps:

- make SNR files as you would normally for gnssrefl (use <code>rinex2snr</code>)

- set up a simple set of instructions for your site   



###Further reading

J. Strandberg,, T. Hobiger, and R. Haas (2016), Improving GNSS-R sea level determination through inverse modeling of SNR data, Radio Science, 51, 1286–1296
[pdf](https://publications.lib.chalmers.se/records/fulltext/241876/local_241876.pdf)

D. Purnell, N. Gomez,  et al. (2021) Precise water level measurements using low-cost GNSS antenna arrays, Earth Surf. Dynam., 9, 673–685 [pdf](https://esurf.copernicus.org/articles/9/673/2021/)

### Changes

We need to add Beidou.
