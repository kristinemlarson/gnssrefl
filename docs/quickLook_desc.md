### Description of Quick Look Analysis

The four subplots show the GNSS-IR analysis from the different regions surrounding the GNSS 
antenna (northwest, northeast, southwest, southeast). 

Within each plot, each color represents the results of a frequency analysis for 
a different satellite arc. The periodogram has been computed so that the x-axis 
is the reflector height (RH, in meters) and the y-axis is the spectral amplitude
in converted SNR units (volts/volts).  If you see a strong peak in the periodogram,
that means you will have a good estimate of the RH for that satellite arc. The data
represented in gray are "failed" periodograms. 

This example is bare soil measured at an airport in New Mexico. The surface is **very uniform** and thus the periodograms 
are particularly repeatable.

<img src="p038_L2C.png" width=500>

This example is on an ice sheet. There is some spread in reflector height peaks as well as in its amplitudes:

<img src="lorg_L5.png" width=500>

This example is taken from a site where the surface of interest is water. You will only
see useful reflections in certain directions (and thus certain quadrants). And you will
notice that the peaks in the periodograms are spread out because the system is sensing 
**tides**. This means the reflector heights are varying with time, and that is what it 
should be doing. The peak amplitudes in the periodograms are also smaller than in the ice reflection examples and 
that is because a water surface reflects differently than ice/snow surfaces.

<img src=http://gnss-reflections.org/static/images/examples/sc02100f1.png width=500>


[Additional discussion of the GNSS-IR method, with example periodogram links.](https://gnss-reflections.org/overview)

If you would like to investigate the physical surroundings of a site, and it is a well-known geodetic site,
you can try entering the 4 character ID at [this site.](http://gnss-reflections.org/geoid). If it is not a 
currently operating GNSS site (or not recognized by the University of Nevada Reno), you can enter the latitude, longitude,
and height. A photograph is only returned by this webapp if a photograph is available at the UNAVCO archive.

