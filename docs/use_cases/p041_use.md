### Marshall Field, Colorado

I will use a site in Boulder, Colorado (p041) to show you some of the features of the code and the data.
The p041 antenna is ~2 meters tall. The site is relatively planar and free of obstructions.
Since October 2018 the site has operated a Septentrio receiver. It has multi-GNSS signals in the 
default RINEX file and is archived at UNAVCO.

<img src="https://gnss-reflections.org/static/images/P041.jpg" width="500">

I have made a web tool to give you an idea of the [reflection zones for a site that is 2 meters tall.](https://gnss-reflections.org/rzones)
You should only need to enter the station name and the reflector height (2 meters).

First you need to make a SNR file. I will use the defaults, which only translates the GPS signals. 

*rinex2snr p041 2020 132*

If this does not work, you can try to override the default:

*rinex2snr p041 2020 132 -translator python*

Lets look at the spectral characteristics of the SNR data for the default L1 settings:

*quickLook p041 2020 132* 

<img src="../_static/p041-l1.png" width="500">

The four subplots show you different regions around the antenna. The x-axis tells you 
reflector height (RH) and the y-axis gives you the spectral amplitude of the SNR data.
The multiple colors are used to depict different satellites that rise or set over that
section (quadrant) of the field at P041. Which colors go to which satelliets is not super important.
The goal of this exercise is to notice that the peaks of those periodograms are lining up
around an x value of 2 meters. You also see some skinnier gray data - and those are **failed periodograms.**
This means that the code doesn't believe the results are relevant.  I did not originally plot failed
periodograms, but people asked for them, and I do think it is useful to see that there is some
quality control being used in this code.

I will also point out that these are the data from an excellent receiver, a Septentrio.
Not all receivers produce L1 data that are as nice as these. Now try L2C:

*quickLook p041 2020 132 -fr 20* 

<img src="../_static/p041-l2c.png" width="500">

One thing you can notice here is that there are more colors in the L1 plots than in the L2C 
plots. That is simply the result of the fact that there are more L1 satellites than L2C satellites.

Homework: try L5. 

You can try different things to test the code. For example, you can change the reflector height restrictions:

*quickLook p041 2020 132 -h1 0.5 -h2 10* 


If you want to look at Glonass and Galileo signals, you need to create SNR files using the -orb gnss flag.

*rinex2snr p041 2020 132 -orb gnss*

I believe Beidou signals are tracked at this site, but the data are not available in the RINEX 2.11 file.

**quickLook** is meant to be a visual assessment of the spectral characteristics. However, 
it does print out the answers to a file called *rh.txt*. For routine analyses for reflector height you need to 
use **gnssir**



