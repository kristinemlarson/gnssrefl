# from tim
you can always build a new image if you want to test on your own.

from your gnssrefl directory (that has the Dockerfile):
docker build --no-cache -t <imagename> .
docker run -it <imagename> /bin/bash
If you want to mount volumes you could copy the -v syntax from the unavdocker/gnssrefl docker run command.

docker images tells you what is running

docker.io/library/nameofimage
tag is latest
get image number imageNu

docker run -i -t imageNu /bin/bash

# google map API

https://developers.google.com/maps/documentation/javascript/localization

# disutils - change to meson

https://numpy.org/doc/stable/reference/distutils_status_migration.html

# example of someone doing this ?
https://github.com/quarkslab/qbindiff/commit/46247bc377f806f91b53e42172c2e48f48e4da4a

will be removed as of Python 12

https://meson-python.readthedocs.io/en/stable/tutorials/introduction.html

# should get rid of flipit detritus in subdaily

compile the fortran first
f2py -c -m gnssrefl.gpssnr gnssrefl/gpssnr.f



https://stackoverflow.com/questions/7053996/how-do-i-install-imagemagick-with-homebrew

https://realpython.com/pypi-publish-python-package/#version-your-package

you'll run the init command,

then add this section into your pyproject.toml (the file_patterns section is where you will add all the places where the version is)
[tool.bumpver]
current_version = "1.0.0"
version_pattern = "MAJOR.MINOR.PATCH"
commit_message  = "Bump version {old_version} -> {new_version}"
commit          = true
tag             = true
push            = false

[tool.bumpver.file_patterns]
"pyproject.toml" = ['current_version = "{version}"', 'version = "{version}"']



# kelly provided this example of bumpver

https://gitlab.com/earthscope/public/earthscope-sdk/-/blob/main/pyproject.toml?ref_type=heads


Country codes

https://www.iban.com/country-codes

download_tides 8768094 noaa -date1 20150101 -date2 20150131
# but it will be here
https://readthedocs.org/projects/gnssrefl/downloads/

https://gnssrefl.readthedocs.io/_/downloads/en/latest/pdf/

# user guide not updated, so useless
#https://buildmedia.readthedocs.org/media/pdf/gnssrefl/latest/gnssrefl.pdf

Local notes:
f2py -c -m gnssrefl.gpssnr gnssrefl/gpssnr.f
f2py -c -m gnssrefl.gnsssnr gnssrefl/gnsssnr.f
f2py -c -m gnssrefl.gnsssnrbigger gnssrefl/gnsssnrbigger.f

docker pull unavdocker/gnssrefl to install code.


# WSV
https://github.com/bundesAPI/pegel-online-api/tree/main/python-client
## when you make a new version

Use 1.5.1 as an sample version number

- change the version number in setup.py.  

- change the version in the README.md

- change the version number in CHANGELOG.md and provide 
a description of the main changes in this new version.

- push the code to github, git push origin master

- git tag 1.5.1 

- git push --tags

The latter will tell github to make a new pypi version.

git push origin master will make a new docker.


Install a new python:

- sudo apt install python3.9

Get a list of your outdated packages

- pip list --outdated

How to update them all? The horror, the horror


$EXE/gfzrnx -finp rinex3 -fout  rinex2 -vo 2 -ot G:S1C

Where is the static executable information for gpsSNR or gnssSNR?
Cause it would be useful to know ...


git pull --rebase

##

def mjd_to_datetime(mjd):
    """
    """
    base_date=datetime(1858,11,17)
    delta=timedelta(days=mjd)
    return base_date + delta

mjd_dates = [60183 , 60184, 60185]

tv = [1, 5, 3]
datetime_objects = [mjd_to_datetime(mjd) for mjd in mjd_dates]

a suggestion for the future: https://semver.org/

Given a version number MAJOR.MINOR.PATCH, increment the:
MAJOR version when you make incompatible API changes
MINOR version when you add functionality in a backward compatible manner
PATCH version when you make backward compatible bug fixes

Things to do:

- update tropo models to include latest from Chalmers

- finish up advanced model vwc

2024 short course

Make sure people are using version 3.9
is version 3.10 ok?  for sure 3.11 is not.

How to make a new github release?

myAnimation.gif is in the EarthScopeLecture folder in Presentations.
Need to find a better place for it

# for listings of ftp sites

~/Documents/Code/Listings
