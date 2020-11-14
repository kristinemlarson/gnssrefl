# First drivethru This is a test case for GNSS interferometric reflectometry. 
It does not explain everything about the technique, the code, or 
the site we will be using, but it will provide some tests you can use 
to make sure you have properly installed the code. For details about the technique, 
you should start with reading [Roesler and Larson, 2018](https://link.springer.com/article/10.1007/s10291-018-0744-8), 
which was published open option.  

# Install the gnssrefl code 

Read the [gnssrefl documentation](https://github.com/kristinemlarson/gnssrefl). 

Install either the github or the pypi version of gnssrefl

Make the requested environment variables. 

Strongly urged: put CRXRNX in the EXE are area. Make sure it is executable

There are use cases in the gnssrefl documentation that you can try.

If you know how to compile Fortran code, I strongly urge you to download/compile the requested
codes and install those executables in the correct place.

# Test the code for p041

I will use a site in Boulder, Colorado (p041) using the bare bones code (mostly with defaults)

Start with [a photo of P041](https://gnss-reflections.org/static/images/P041.jpg)

This antenna is ~2 meters tall. 

[Get an idea of the reflection zones for a site that is 2 meters tall.](https://gnss-reflections.org/rzones)


Make a SNR file using the defaults: 

*rinex2snr p041 2020 132*

Lets look at the spectral characteristics of the SNR data for the default L1 settings:

*quickLook p041 2020 132* [png](p041-l1.png)

Now try L2C:

*quickLook p041 2020 132 -fr 20* [png](p041-l2c.png)

Now try L5:
*quickLook p041 2020 132 -fr 5* 


# Test the code on ice

Now use lorg.  The data are archived at UNAVCO.  Get some coordinates for the site, either lat,long,ht
or XYZ. The coordinates do not have to be super precise (within 100 meters is fine).

**Exercise for the reader:** get a photograph of lorg from UNAVCO. If you cannot find it at their site,
email them and ask them to provide it.

You can try out lorg here, though Google Maps does not have imagery. https://gnss-reflections.org/rzones



Just in general, what do you think the azimuth mask should be?  Based on your reading, Elevation angle mask?

Make SNR files for station lorg, year 2019, doy 1 through 233

Do a quickLook for one file using the defaults. What frequency is displayed?  Compare frequencies 1,2 and 5.  Note the differences. Now run frequency 20.  How is that different than frequency 2?
Make a json input for station lorg. Use defaults. (Why is that reasonable?)
Run gnssir for all the SNR data.
Try out daily_avg using median filter of 0.25 meters and ReqTrack of 50. It should let you use different frequencies.  Try that out.  
Figure out how to save the output of daily_avg - both to a text file and to a plot.  


