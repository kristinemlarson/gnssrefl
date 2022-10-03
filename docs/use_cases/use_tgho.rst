.. role:: raw-html-m2r(raw)
   :format: html


Lake Taupo
==========

:raw-html-m2r:`<p align="center">`
:raw-html-m2r:`<img src="tgho_barker.jpg" width="500">`\ :raw-html-m2r:`<BR>`
Photo credit: Simon Barker
</P>

.. image:: tgho_barker.jpg
   :target: tgho_barker.jpg
   :alt: 


**Station Name:** tgho 

**Location:** North Island, New Zealand

**Archive:** `Geonet <https://www.geonet.org.nz/>`_

**DOI:**    N/A

**Ellipsoidal Coordinates:**


* 
  Latitude: -38.813

* 
  Longitude: 175.996

* 
  Height: -38.813 m

`Station Page at Geonet <https://www.geonet.org.nz/data/network/mark/TGHO>`_

`Station Page at Nevada Geodetic Laboratory <http://geodesy.unr.edu/NGLStationPages/stations/TGHO.sta>`_

`Google Map Link <https://goo.gl/maps/1zmgi6rRHPVPDAfV8>`_

Data Summary
------------

Station tgho is operated by `GNS <https://www.gns.cri.nz>`_. The GNSS site is located 
on a platform in Lake Taupo. It records standard GPS and Glonass signals at a low sample rate (30 sec).
The site could be significantly improved with a newer receiver that tracks modern signals at a higher sample rate.

Take a Quick Look at the Data
-----------------------------

Begin by making an SNR file. Use both GPS and Glonass and set the archive to nz:

:raw-html-m2r:`<code>rinex2snr tgho 2020 300 -orb gnss -archive nz</code>`

:raw-html-m2r:`<code>quickLook tgho 2020 300 -e1 5 -e2 15</code>`

:raw-html-m2r:`<img src="tgho-default.png" width="600">`


.. image:: tgho-default.png
   :target: tgho-default.png
   :alt: 


The clutter near the monument produces noise at the small RH values.  A better result 
can be found if those values are eliminated by setting h1 to 2. We also extend h2 to 8.

:raw-html-m2r:`<code>quickLook tgho 2020 300 -e1 5 -e2 15 -h1 2 -h2 8</code>`

:raw-html-m2r:`<img src="tgho-better.png" width="600">`


.. image:: tgho-better.png
   :target: tgho-better.png
   :alt: 


Now try looking at the periodogram for L2:

:raw-html-m2r:`<code>quickLook tgho 2020 300 -e1 5 -e2 15 -h1 2 -h2 8 -fr 2</code>`

:raw-html-m2r:`<img src="tgho-l2.png" width="600"/>`


.. image:: tgho-l2.png
   :target: tgho-l2.png
   :alt: 


These results are not very compelling for a variety of reasons. The GPS L2 data 
will not be used in subsequent analysis. Next, check the two Glonass frequencies:

:raw-html-m2r:`<CODE>`\ quickLook tgho 2020 300 -e1 5 -e2 15 -h1 2 -h2 8 -fr 101</code>

:raw-html-m2r:`<img src="tgho-glonass-l1.png" width="600"/>`


.. image:: tgho-glonass-l1.png
   :target: tgho-glonass-l1.png
   :alt: 


:raw-html-m2r:`<code>quickLook tgho 2020 300 -e1 5 -e2 15 -h1 2 -h2 8 -fr 102</code>`

:raw-html-m2r:`<img src="tgho-glonass-l2.png" width="600"/>`


.. image:: tgho-glonass-l2.png
   :target: tgho-glonass-l2.png
   :alt: 


The QC metrics from Glonass 101 are helpful for setting the azimuth mask:

:raw-html-m2r:`<img src=tgho-glonss-qc.png width="600">`


.. image:: tgho-glonss-qc.png
   :target: tgho-glonss-qc.png
   :alt: 


We will exclude 135-225 degrees in azimuth. We will require an amplitude of 9 and a peak to noise ratio of 3.0.

Analyze the Data
----------------

Use :raw-html-m2r:`<code>make_json_input</code>` to set up the analysis parameters. Set the elevation and reflector heights as in :raw-html-m2r:`<code>quickLook</code>`. The peak to noise ratio and required amplitude can be set on the command line. 

:raw-html-m2r:`<code>make_json_input tgho -38.8130   175.9960  385.990 -h1 2 -h2 8 -e1 5 -e2 15 -peak2noise 3 -ampl 9</code>`

The azimuth mask has to be set by hand to exclude empty regions and azimiths with poor retrievals. 
Glonass signals (frequencies 101 and 102) were added and GPS L2/L5 were removed.\ `Sample json <tgho.json>`_

Then make SNR files for ~six months:

:raw-html-m2r:`<code>rinex2snr tgho 2020 130 -archive nz -doy_end 319 -orb gnss</code>`

The output SNR files are stored in $REFL_CODE/2020/snr/tgho.

Now run :raw-html-m2r:`<code>gnssir</code>` for these same dates:

:raw-html-m2r:`<code>gnssir tgho 2020 130 -doy_end 319 </code>`

To look at daily averages, use the utility :raw-html-m2r:`<code>daily_avg</code>`. The median filter is set to allow values within 0.25 meters of the 
median, and the minimum number of tracks required to calculate the average is set to 50 tracks.  

:raw-html-m2r:`<CODE>`\ daily_avg tgho .25 50 </code>

The number of retrievals each day is show here:

:raw-html-m2r:`<img src="tgho-numvals.png" width="600">`


.. image:: tgho-numvals.png
   :target: tgho-numvals.png
   :alt: 


All retrievals are shown here:

:raw-html-m2r:`<img src="tgho-all.png" width="600">`


.. image:: tgho-all.png
   :target: tgho-all.png
   :alt: 


Note in particular that there are quite a few data outages in this series, which means the RINEX files were missing 
from the NZ archive.

Finally, the average RH plot:

:raw-html-m2r:`<img src="tgho-rhavg.png" width="600">`


.. image:: tgho-rhavg.png
   :target: tgho-rhavg.png
   :alt: 


`Sample RH file <tgho_dailyRH.txt>`_

Although Taupo is in a volcanic caldera, lake levels are determined by seasonal processes such 
as evaporation, precipitation, input from local drainages, and outflow. The Waikoto 
River is sole river draining the lake, and river flow is regulated by a series of hydroelectric dams.
