Dates:

Geodesy for Climate Research (ICCC) March 28-30, 2023
Earthscope : March 27-29 2023
EGU 23–28 April 2023

May 1-5 ?
May 8-13 ?

May 24-26 GNSS+R

May 29-June 2 Pentecost

June seems pretty open for Eruoep - but 
very few American universities "open" 
But does that matter?

IUGG  - July 11-20


Possible one-week short short course:

First Week - two hour max

- Installation help session, Tim and Kelly

- Basic Theory (Felipe) How to Run the Code (kristine), 
(do we offer or make people watch the videos?)

Second Week Two hour max per day

- Day 1 : Snow, ice sheets, lakes (me or Felipe?)

- Day 2 : sea level (Simon)

- Day 3 : soil moisture (me)

- Day 4 : How to run your own site. good receiver (kristine) cheap sensors (Makan,Felipe,Simon)

Local notes:
f2py -c -m gnssrefl.gpssnr gnssrefl/gpssnr.f
docker pull unavdocker/gnssrefl to install code.

[Quick link to the command line homeworks used in the October 21 GNSS-IR course](https://github.com/kristinemlarson/gnssrefl/tree/master/tests/homeworks). They are numbered homework0, homework1, etc.
[Quick link to the Jupyter Notebooks](https://www.unavco.org/gitlab/gnss_reflectometry/gnssrefl_jupyter)

[Quick link to Docker](https://github.com/kristinemlarson/gnssrefl/blob/master/docs/docker_cl_instructions.md)

[Old quick link to Docker](https://hub.docker.com/r/unavdocker/gnssrefl)

cddis links:

[highrate data](https://cddis.nasa.gov/archive/gnss/data/highrate/2019/150/19d/00/)

[geodetic data rate](https://cddis.nasa.gov/archive/gnss/data/daily/2018/015/18d/)

[readme](https://cddis.nasa.gov/Data_and_Derived_Products/CDDIS_Archive_Access.html)

[how to get a listing of orbits on a given GPS week (but not multi-GNSS)...](https://cddis.nasa.gov/archive/gnss/products/2037/)

[multi-GNSS](https://cddis.nasa.gov/archive/gps/products/mgex/2037/)


**How to build your own docker image**

From your gnssrefl directory (that has the Dockerfile):

<code>docker build --no-cache -t <imagename> .</code>

<code>docker run -it <imagename> /bin/bash</code>

If you want to mount volumes you could copy the -v syntax from the unavdocker/gnssrefl docker run command.

**make a package for pypi**

export SETUPTOOLS_USE_DISTUTILS=stdlib

python setup.py sdist bdist_wheel

upload a package to pypi

twine upload dist/*

**Issues with numpy**

https://numpy.org/devdocs/reference/distutils_status_migration.html

**Versions**

1.1.5 Officially added soil moisture module

1.1.6 changed how CDDIS archive is used, from a wget subprocess call to using FTPS.

This required checking that downloaded file was not zero size.  
<PRE>
    ftps.login(user='anonymous', passwd=email)
    ftps.prot_p()
    ftps.cwd(directory)
</PRE>

1.1.7 fixed bug in invsnr that did not allow SNR files unless they were uncompressed.
added xz and gz endings

1.1.8 updated download_ioc
added refl_zones
added EGM96 to gps.py
1.1.9 added ediff to quickLook

1.1.10 fixed subdaily spline fit.  no longer cut off data at the 
beginning and end.  also output files that are interfrequency bias corrected,
relative to L1

1.1.12 subdir is pretty much the norm for output of downstream programs
(vwc, daily_avg, subdaily) and the plots for quickLook
added IF bias correction to subdaily (but csv not working)
added refl_zones utility

1.2.1 fixed bug in subdaily. the output file of the IF correction was wrong
1.2.2 had made delTmax to 45 minutes, but that is way too short for soil moisture.
put it back to 75 minutes.
