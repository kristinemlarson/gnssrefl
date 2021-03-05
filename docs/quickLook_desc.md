### Description of Quick Look Analysis

The four subplots show the GNSS-IR analysis from the different regions surrounding the GNSS 
antenna (northwest, northeast, southwest, southeast). 

Within each plot, each color represents the results of a frequency analysis for 
a different satellite arc. The periodogram has been computed so that the x-axis 
is the reflector height (RH, in meters) and the y-axis is the spectral amplitude
in converted SNR units (volts/volts).  If you see a strong peak in the periodogram,
that means you will have a good estimate of the RH for that satellite arc. The data
represented in gray are "failed" periodograms. 

This example is bare soil at an airport. The surface is very uniform and thus the periodograms 
are particularly repeatable.

<img src="p038_L2C.png" width=400>

This example is on an ice sheet. There is some spread in reflector height peaks:

<img src="lorg_L5.png" width=400>

This example is taken from a site where the surface of interest is water. You will only
see useful reflections in certain directions (and thus certain quadrants). And you will
notice that the peaks in the periodograms are spread out because the system is sensing 
**tides**. This means the reflector heights are varying with time, and that is what it 
should be doing.

<img src=http://gnss-reflections.org/static/images/examples/sc02100f1.png width=400>


[Additional discussion of the GNSS-IR method, with example periodogram links.](https://gnss-reflections.org/overview)

