# gnssrefl

**github version: 1.9.4** [![PyPI Version](https://img.shields.io/pypi/v/gnssrefl.svg)](https://pypi.python.org/pypi/gnssrefl) [![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.5601495.svg)](http://dx.doi.org/10.5281/zenodo.5601495) [![Documentation Status](https://readthedocs.org/projects/gnssrefl/badge/?version=latest)](https://gnssrefl.readthedocs.io/en/latest/?badge=latest)

**For those of you trying to convert RINEX 3 files to RINEX 2.11, be careful. There are a lot of things going
on in that translation.  It is better to let gnssrefl to do that conversion for you.  rinex2snr allows RINEX 3
files!**

Our online documentation is available [here.](https://gnssrefl.readthedocs.io/en/latest/)
[(pdf version)](https://gnssrefl.readthedocs.io/_/downloads/en/latest/pdf/)

pktnlim in invsnr was out of synch with new definition installed last summer. Please set pk2nlim manually,
or use new version (1.9.0)

See documentation for gnssir_input for new refraction models.

A long time ago - and in a galaxy far, far away - Bob King told a group of graduate students why he 
liked GPS observation files. His answer:

*There are no leap seconds.*

I agree with Bob King. This software is meant to be used with GPS time. All files should be in GPS time.
Conversion to UTC is something you should do on your own. 

September 12, 2023: Updated nmea2snr to allow signals other than L1.

August 2, 2023: Updated azimuth outputs for gnssir and quickLook so that the azimuth of the 
rising or setting part of the arc is reported rather than the average azimuth, as was done in the older versions.

July 7, 2023: The newarcs option had a bug in it: the refraction correction was not being applied.
While the refraction correction is not very important for some applications (snow, soil moisture), using it sometimes and not
using it other times IS NOT GOOD.  You will see a bias in time series when you switched. This bug is fixed as of version 1.4.1
I will be removing all versions (1.3.16 up to 1.4.1) from pypi that have this bug. If you were 
using the newarcs option in the last month, you need to rerun gnssir and any 
downstream codes (subdaily, daily_avg etc). This bug has 
no impact on the data translation codes (rinex2snr, nmea2snr).  

How do you find out which version are you running? Type <code>pip list | grep gnssrefl</code>

If you want to sign up for the GNSS-IR email list, please contact Kristine Larson.

[Youtube videos for beginners](https://www.youtube.com/channel/UCC1NW5oS7liG7C8NBK148Bg).

If you want to access CDDIS, including orbits, you should make [an account](https://urs.earthdata.nasa.gov/users/new).

If you want to access to any Earthscope data, [an account is required](https://data-idm.unavco.org/user/profile/login).

<HR> 

GNSS-IR was developed with funding from NSF (ATM 0740515, EAR 0948957, AGS 0935725, EAR 1144221, AGS 1449554) and 
NASA (NNX12AK21G and NNX13AF43G). <code>gnssrefl</code> was initially developed 
as a fun post-retirement project, followed by support from NASA (80NSSC20K1731).


Kristine M. Larson




