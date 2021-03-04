### Lower Thwaites Glacier

**Station Name:** lthw

**Location:** Thwaites Glacier, Antarctica

**Data are archived:** [UNAVCO](http://www.unavco.org)

**Ellipsoidal Coordinates:**

- Latitude: -76.458

- Longitude: -107.782

- Height: 1011.459 m

[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/LTHW)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/LTHW.sta)


<img src="http://gnss-reflections.org/static/images/LTHW.jpg" width="500"/>


## Data Summary

The receiver only tracks legacy GPS signals, so only L1 should be used for reflectometry. The pole
is set in the snow/ice and routinely (every few years) reset. Please use the [Nevada Reno site](http://geodesy.unr.edu/NGLStationPages/stations/LTHW.sta) to get a feel for when the pole has been reset.

## Setting Azimuth and Elevation Mask

Because there are no structures surrounding the site, elevation and azimuth defaults can mostly be used.
The only restriction that should be imposed is a minimum elevation angle of 7 because that is what
the field crew set as a mask at the site.


## WebApp

lthw is one of the example cases for the [GNSS-IR webapp.](https://gnss-reflections.org/fancy6?example=lthw)
The webapp analyzes data in real-time, so please wait for 5-10 seconds.

## Take a Look at the SNR data

Translate the GPS data for the year 2018

*rinex2snr lthw 2018 1 -doy_end 365 -archive unavco*

Then take a look at January 1 in 2018:

*quickLook lthw 2018 1 -e1 7*

<img src="lthw-day1-2018.png" width="500"/>

This is a bit of a mess really. If there are significant peaks, they are really 
close to the cutoff for the method (at 0.5 meters).  Now look a week later:

*quickLook lthw 2018 9 -e1 7*

<img src="lthw-day9-2018.png" width="500"/>

This is *much* better and clearly shows that a field crew reset the antenna to a little 
less than 5 meters sometime between day 1 and day 9 in the year 2018.

If you like you can compare this to the first day of 2020, first make the SNR file:

*rinex2snr lthw 2020 1 -archive unavco*

Then use quickLook:

<img src="lthw-day1-2020.png" width=500/>

Now the peaks in the RH periodograms are ~2.2 meters - so that means ~2.5 meters of surface change 
from 2018 to 2020.

## Analyze the SNR Data for the year 2018

First you need to make the list of analysis inputs:

*make_json_input lthw -76.458  -107.782 1011.0 -e1 7 -e2 25 -peak2noise 3.2*

Handedit the json file so that only L1 is used. [Example json file](lthw.json).

Analyze the data for 2018 from day 1 to day 365:

*gnssir lthw 2018 1 -doy_end 365 -screenstats False*

Compute daily averages requiring 50 satellite tracks and median filter of 0.25 meters:

*daily_avg lthw 0.25 50*

<img src="lthw-req50.png" width="500"/>

You can loosen the required track number if you want:

*daily_avg lthw 0.25 40*

<img src="lthw-req40.png" width="500"/>

