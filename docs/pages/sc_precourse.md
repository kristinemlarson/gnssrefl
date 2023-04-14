# Pre-course Activities

While it is possible to simply listen to the lecturers in the short 
course, we think that this is a far better learning experience if 
you are able to follow along with the examples. And for this we recommend the following:

## Software Installation
1. **Please sign up for an Earthscope account**

https://data-idm.unavco.org/user/profile/login


2. **Check out the slack channel**

This will be the main avenue used for asking questions.

3. **Please install the software.**

We have instructions here for three different ways to access our code. 

- The github or pypi install requires you are running linux and 
have python 3.8+ on your system and feel comfortable
installing python packages.  

- Dockers. PC users should use this path, but it is also a good way for mac and linux users that don't want to manage dependencies or environment variables.

- Jupyter notebooks. This is a great way for people that are unfamiliar 
with python to access the code. The examples are given as tutorials.

[Installation Instructions](https://gnssrefl.readthedocs.io/en/latest/pages/README_install.html)

***

At this point, if you are using the jupyter notebook installation, follow the [pre-course notebook](#todo Kelly add precourse notebook link) included in this repository.

### For command line users (Github/pypi/Docker):

4. **Check your environment variables**

Direct installers (github/pypi) need to set environment variables. In a terminal window, you should
check that they are active by typing these commands:

<code>printenv REFL_CODE</code>

<code>printenv EXE</code>

If nothing comes back, you haven't set them. **They have to be set every time you run the code.**
That is why we recommend you put them in your .bashrc file.

The inputs are outputs of your code will be stored in the REFL_CODE directories. Executables 
from external sources are in EXE, orbits are stored in ORBITS. The ORBITS and REFL_CODE environment 
variables can be set to the same physical location.

5. **Translate a Single GNSS File**

For github, pypi, and docker users:

<code>rinex2snr p038 2022 90 -orb rapid</code>

On my machine this returns:

<pre>
SUCCESS: SNR file was created: /Users/kristine/Documents/Research/2023/snr/p038/p0380900.23.snr66
</pre>

This file was created using defaults:

- a rapid GNSS orbit at GFZ
- GNSS data from EarthScope

If you have any trouble with this command, please try:

<code>rinex2snr p038 2022 90 -orb rapid -archive sopac</code>

6. **Look at the reflection data for a single GNSS station**

<code>quickLook p038 2022 90</code>

This creates two png files. If you are using a direct install, they will come to the screen.

<img src="../_static/p038-1.png">
<img src="../_static/p038-2.png">

If you are using a docker, the png files will **not** print to the screen but will be stored in the directory you ran the docker run command for you to open on the host machine outside the docker container.

For example:
On a linux machine you could view the image from a browser. My 
machine said the file was saved here:

/etc/gnssrefl/refl_code/Files/p038/quickLook_lsp.png

But I was running the docker from /Users/kristine/docker_friday.  So the correct
path for viewing it in a browser is:

/Users/kristine/docker_friday/refl_code/Files/p038/quickLook_lsp.png

If you are able to download and translate a GNSS file and run <code>quickLook</code>, you are doing great.
The main issue now is understanding these plots and what they are telling you.

## Understanding
You should read [the overview documentation](https://gnssrefl.readthedocs.io/en/latest/pages/understand.html)

And then the [quickLook documentation](https://gnssrefl.readthedocs.io/en/latest/pages/quickLook.html).

What do we mean when we say "reflector height"? You need to know that before the next section.
What happens when you change the inputs to quickLook? (h1, h2, e1, e2). Try using different frequencies.

**What is a Reflection Zone**

[Watch this video](https://www.youtube.com/watch?v=sygZMeCHHDg&t=23s)

Use the [refl_zones web site](https://gnss-reflections.org/rzones) to try and pick 
reflection zones for station [ross](http://gnss-reflections.org/geoid?station=ross) 
that was used in the examples. Should you use the default
sea level reflector height or should you pick one? And if so, what value?
From the picture, what value do you think is reasonable?


Try to pick reflection zones for station [sc02](http://gnss-reflections.org/geoid?station=sc02). For this site 
is it reasonable to use the mean sea level RH option in https://gnss-reflections.org/rzones ?

**If you have time and would like to do more**

The main module for estimating reflector height is called [gnssir](https://gnssrefl.readthedocs.io/en/latest/pages/gnssir.html).
Before trying out one of [our examples](https://gnssrefl.readthedocs.io/en/latest/pages/first_drivethru.html), 
you should read that documentation.

If you are interested in water levels, you should start with a lake. 

If you are interested in snow accumulation, you should start with an ice sheet.  

