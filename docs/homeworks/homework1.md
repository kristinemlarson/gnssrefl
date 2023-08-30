
## Homework 1

**Prerequisite:** You need to make
sure the software has been properly installed and you have successfully completed the "homework 0" assignment.

**Purpose:** Practice setting your azimuth and elevation angle mask  

The purpose of this homework is to get you to better understand 
how to properly run <code>gnssrefl</code>. Each GNSS station is different and you will have to 
decide which areas around the antenna you want to measure. This is sometimes called setting the 
azimuth and elevation angle mask. 
The <a href=https://gnss-reflections.org target="_blank">gnss-reflections.org</a> webapp has 
some tools to help you determine this mask.

## Example 1

Let us start with station **at01** in St. Michael, Alaska. 
It is operated by [UNAVCO](https://www.unavco.org). The data from
this GNSS site will be used to measure sea level, so the relevant reflecting surface is 
the ocean. Use the geoid tab on the webapp and enter the station name.
You can see the general location of the antenna with respect to the coast. 
Make a note of its height with respect to mean sea level. 

Next use the ReflZones tab of the webapp to try out different elevation angle 
and azimuth angle masks. Make a note of the angles that you think will give you a 
good reflection off the water.

Next you will test how well you set your mask. 

First make an SNR file for station 
at01 for the year 2020 and day of year 109 and the unavco archive.  If you are not 
sure how to do this, see the [rinex2snr documentation](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.rinex2snr_cl.html).

Once the SNR file has been created, use <code>quicklook</code> with the default settings.
Looking at the plots that were generated, what went wrong? If you would like to better understand the plots,
look back to the [quickLook](https://gnssrefl.readthedocs.io/en/latest/pages/quickLook.html)

Now use your <code>quickLook</code> knowledge of the site's height above the reflector to properly window 
the reflector height and using the azimuth and elevation angle mask you picked out
earlier. Do you think the retrievals are better now? Should your azimuth mask be modified?


## Example 2

**tgho** is a station in New Zealand operated by [GNS](https://www.gns.cri.nz). The GNSS site is located
on a platform in Lake Taupo. It records standard GPS and Glonass signals at a low sample rate (30 sec).
We can tell that just by looking at the google maps from the webapp that it won't be as easy to figure out the 
azimuth range (or elevation angle) range. Its height above mean sea level is given, but that is not the distance
to the water shown in the photo. We will instead use <code>quicklook</code> for some feedback.

- Make a SNR file for tgho, year 2020, day of year 300. 

- Now run <code>quickLook</code>

- What do you think the vertical distance is between the antenna and the water? 

- Using the default elevation angles is likely combining water and pier reflections. 
Try retricting the close reflections (from the pier) by using a larger 
lower bound. Also compare the defaults with 5-15 degrees elevation angles to see if this improves the retrievals. 

Refer to this [publication](https://www.kristinelarson.net/wp-content/uploads/2021/05/Holden-May2021.pdf) on 
Lake Taupo for more information on this site.

## Extra Credit

* Try to find a station website for TGHO at GNS.

* Try to find a station website for AT01 at UNAVCO.
