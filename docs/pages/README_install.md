# Installation

You can access this package via Jupyter notebooks, Docker containers, or traditional
github/pypi package installation. **If you are using Windows, you must use dockers.** I believe
you can also use a linux emulator and follow instructions for linux.

## Jupyter Notebooks 

[Install Instructions](https://gnssrefl.readthedocs.io/en/latest/pages/jupyter_notebook_instructions.html)

[Notebook Area for Use Case Examples](https://github.com/kristinemlarson/gnssrefl/tree/master/notebooks/use-cases)

## Docker Container

[Install Instructions](https://gnssrefl.readthedocs.io/en/latest/pages/docker_cl_instructions.html)

## Local Python Install for Linux/MacOS

As of gnssrefl version 3.9.0 you are allowed to run any python version >= 3.9.
To allow this we had to change how the package is built; we now use meson. If you have problems 
with the install, please let us know by posting a github Issue.

For installation with github/pypi, the setup requires a few system dependencies: gcc and gfortran.
To check please type:

<code>apt-get install -y gcc</code>

and 

<code>apt-get install -y gfortran</code> 

in your terminal (or <code>yum install -y gcc-gfortran</code>).

**If you are using a MacOS** then you will need to install <code>xcode</code>. First, in your
terminal, check first to see if you already have it:

<code>xcode-select -p</code>

If it is installed, it should return a path. If it is not installed then run

<code>xcode-select --install</code>

This should install gcc. You can check if you have gcc by typing

<code>gcc --version</code>

You can check to see if you have gfortran by typing

<code>gfortran --version</code>

If you do not have gfortran, then you can use homebrew to install (<code>brew install gfortran</code>).

### Environment Variables

You should define three environment variables:

* EXE = where various executables will live. These are mostly related to manipulating RINEX files.

* REFL_CODE = where the reflection code inputs (SNR files and instructions) and outputs (RH)
will be stored (see below). Both snr files and results will be saved here in year subdirectories.

* ORBITS = where the GPS/GNSS orbits will be stored. They will be listed under directories by
year and sp3 or nav depending on the orbit format. If you prefer, ORBITS and REFL_CODE can be pointing
to the same directory.

If you are running in a bash environment, you should save these environment variables in
the .bashrc file that is run whenever you log on.

If you don't define these environment variables, the code *should* assume
your local working directory (where you installed the code) is where
you want everything to be (to be honest, I have not tested this in a while).
The orbits, SNR files, and periodogram results are stored in
directories in year, followed by type, i.e. snr, results, sp3, nav, and then by station name.

### Direct Python Install

If you are using the version from gitHub:

* You may want to install the python3-venv package <code>apt-get install python3-venv</code>
* <code>apt-get install git</code>
* <code>git clone https://github.com/kristinemlarson/gnssrefl </code>
* cd into that directory, set up a virtual environment, a la <code>python3 -m venv env </code> **make sure you are running 
the correction of python, as discussed at the top of the page** You can have two versions of python on
your machine. To have it run 3.9 instead of 3.11 (for example), type <code>python3.9 -m venv env</code>
* activate your virtual environment <code>source env/bin/activate </code>
* <code>pip install .</code> **Make sure you are using pip3 - either directoyr or linked to pip**
* so please read below or type <code>installexe -h</code> 

### PyPi Install 

* make a directory, cd into that directory, set up a virtual environment, a la <code>python3 -m venv env </code>
**Make sure you are running the correct version of python as discussed at the top of the page**
* activate the virtual environment, <code>source env/bin/activate </code>
* <code>pip install gnssrefl</code> **Make sure you are using pip3 - either directly or linked to pip**
* Please read below or type <code>installexe -h</code> 

### Non-Python Code

<code>installexe</code> should download and install two key utilities used in the GNSS 
community: CRX2RNX and gfzrnx. It currently works for linux, macos and mac-newchip options. If you are using 
docker or Jupyter notebooks **you do not need to run this.**

We no longer encourage people to use **teqc** as it is not supported by EarthScope/UNAVCO. We try to install it 
in case you would like to use it on old files.

### Homework 0: Test installation.
For some of the shortcourses, we compiled a [**Homework 0**](https://gnssrefl.readthedocs.io/en/latest/homeworks/homework0.html) that walks a new user through a few simple tests for validating successful gnssrefl installation.  
