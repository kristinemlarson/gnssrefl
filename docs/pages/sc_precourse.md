# Pre-course Activities

While it is possible to simply listen to the lecturers in the short 
course, we think that this is a far better learning experience if 
you are able to follow along with the examples. And for this we recommend the following:

**Please sign up for an Earthscope account**

Tim and Kelly to provide this information

**Please install the software.**

We have instructions here for three different ways to access our code. 

- The github or pypi install requires you are running linux and 
have python 3.8+ on your system and feel comfortable
installing python packages.  

- Dockers. PC users should use this path.

- Jupyter notebooks. This is a great way for people that are unfamiliar 
with python to access the code. The examples are given as tutorials.

[Installation Instructions](https://gnssrefl.readthedocs.io/en/latest/pages/README_install.html)

**Check your environment variables**

Direct installers (github/pypi) need to set environment variables. In a terminal window, you should
check that they are active (here we only check two):

<code>printenv REFL_CODE</code>

<code>printenv EXE</code>

If nothing comes back, you haven't set them. **They have to be set every time you run the code.**
That is why we recommend you put them in your .bashrc file.

The inputs are outputs of your code will be stored in the REFL_CODE diretories. Executables 
from external sources are in EXE, orbits are stored in ORBITS.  

**Translate a Single GNSS File**

For github, pypi, and docker users:

<code>rinex2snr p038 2022 90 -orb rapid</code>

This should return:

<pre>
SUCCESS: SNR file was created: /Users/kristine/Documents/Research/2023/snr/p038/p0380900.23.snr66
</pre>

This file was created using defaults:

- a rapid GNSS orbit at GFZ
- GNSS data from EarthScope

If you have any trouble with this command, please try:


<code>rinex2snr p038 2022 90 -orb rapid -archive sopac</code>


**Look at the reflection data for Single GNSS station**

<code>quickLook p038 2022 90</code>

This creates two png files. If you are using a direct install, they will come to the screen.
If the docker, the locations are printed to the screen.  Please take a look. 

If you are able to download and translate a file and run quickLook, you are doing great.
The main issue now is understanding these plots and what they are telling you.


You should read [the overview documentation](https://gnssrefl.readthedocs.io/en/latest/pages/understand.html)

And then the [quickLook documentation](https://gnssrefl.readthedocs.io/en/latest/pages/quickLook.html).

What do we mean when we say "reflector height"? You need to know that before the next section.


**What is a Reflection Zone**

[Watch this video](https://www.youtube.com/watch?v=sygZMeCHHDg&t=23s)

Use the [refl_zones web site](https://gnss-reflections.org/rzones) to try and pick 
reflection zones for station [ross](http://gnss-reflections.org/geoid?station=ross) 
that was used in the examples. Should you use the default
sea level reflector height or should you pick one? And if so, what value?
From the picture, what value do you think is reasonable?


Try to pick reflection zones for station [sc02](http://gnss-reflections.org/geoid?station=sc02). For this site 
is it reasonable to use the mean sea level RH option in https://gnss-reflections.org/rzones ?

**If you have time**

If you are interested in water levels, you should start with a lake. 

If you are interested in snow accumulation, you should start with an ice sheet.  
