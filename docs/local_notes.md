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

python setup.py sdist bdist_wheel

upload a package to pypi

twine upload dist/*


**Issues with numpy**

https://numpy.org/devdocs/reference/distutils_status_migration.html

**When making pypi version**
export SETUPTOOLS_USE_DISTUTILS=stdlib

