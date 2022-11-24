Possible one-week short short course:

First Week - two hour max

- Installation help session, Tim and Kelly
(with hope that most people don't need this)

- Basic Theory, How to Run the Code, How to make a good site?
(the hope is that people would watch the videos, but whatever)

Second Week Only do applications ? Two hour max?

- Day 1 : Snow, ice sheets, lakes

- Day 2 : sea level (anything water with subdaily signal)

- Day 3 : soil moisture

- Day 4 : q/a session? free for all? maybe how to make a good site done here?

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
