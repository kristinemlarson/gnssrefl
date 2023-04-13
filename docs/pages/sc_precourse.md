# Pre-course Activities

While it is possible to simply listen to the lecturers in the short 
course, we think that this is a far better learning experience if 
you are able to follow along with the examples. And for this will 
recommend the following:

**Please install the software.**

We have instructions here for three different ways to access our code. The first (the github or 
pypi install0 requires you are running linux and 
have python 3.8+ on your system and feel comfortable
installing python packages.  

The second is via dockers. This is the way PC users will access the code.

The third way is Jupyter notebooks. This is a great way for people that are unfamiliar 
with python to access the code. The examples are given as tutorials.

https://gnssrefl.readthedocs.io/en/latest/pages/README_install.html


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

