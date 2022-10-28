## Homework 0

**goal:** to make sure you have properly installed <code>gnssrefl</code>

[You are strongly encouraged to read the documentation.](https://github.com/kristinemlarson/gnssrefl)

There are two versions of this homework: a Jupyter Notebook version and a command line version.  
Pick the method that you prefer to do your analysis in the course, or experiment with both.

## **Jupyter Notebook version:**

run the HW0 notebook from the [jupyter notebook repository, either via docker or to clone and run locally on your machine](https://www.unavco.org/gitlab/gnss_reflectometry/gnssrefl_jupyter).


## **Command line version options: [gitHub](#runs-locally-on-linux-or-macos-using-code-from-github) or [Docker image](#docker-gnssrefl-command-line-container-option)**

### GNSSREFL via GITHUB (local version)

**NOTE** this setup requires system dependencies: **gcc** and **gfortran**.  To install:
* if you are using a LINUX then simply run `apt-get install -y gcc` and `apt-get install -y gfortran` in your terminal (or <code>yum install -y gcc-gfortran</code> ).
* if you are using a MacOS then you will need to install xcode. First, in your terminal, check if you have xcode by `xcode-select -p`.
If it is installed, it should return a path. If it is not installed then run `xcode-select --install`.
This should install gcc.You can check if you have gcc by `gcc --version`. Check if you have gfortran by `gfortran --version`.
If you do not have gfortran, then you can use homebrew to install, if you have it `brew install gfortran`.
If you don't have homebrew, then see [here](https://gcc.gnu.org/wiki/GFortranBinariesMacOS).

  * If you are still experiencing trouble then it is recommended you try the [docker container version](#docker-gnssrefl-command-line-container-option).

**Assign environment variables and install gnssrefl**
([here is a helpful video covering this portion](https://www.youtube.com/watch?v=tdFi2OGIQwg))
* cd to your desired working directory
* create the following directories for gnssrefl: EXE, ORBITS and REFL_CODE [hint <code>mkdir</code> ]
* set your gnssrefl [enviroment variables](https://en.wikipedia.org/wiki/Environment_variable), EXE, ORBITS and REFL_CODE to these respective paths
  * hint: to check absolute path of a directory <code>pwd</code>
  * hint: to set environment variable in shell, <code>export VARNAME=path/to/directory</code>.  [To set an environment variable everytime you open the shell](https://unix.stackexchange.com/questions/117467/how-to-permanently-set-environmental-variables), use the same export command in the the appropriate initialization file for your shell).


* git clone https://github.com/kristinemlarson/gnssrefl
* cd into that directory, set up a virtual environment, a la python3 -m venv env
* activate your virtual environment
* pip install .

Finally, if you haven't already installed required executables in $EXE (CRX2RNX, gfzrnx):
* install them using gnssrefl commandline installer
  * <code>installexe *OS_type*</code>, where *OS_type* is either {<code>macos</code>, <code>linux64</code>}

### GNSSREFL DOCKER (container version)

[docker hub image](https://hub.docker.com/repository/docker/unavdocker/gnssrefl)

* [see docker command line instructions](https://github.com/timdittmann/gnssrefl/blob/docker_instructions/docs/docker_cl_instructions.md)

*NB:* if you use the <code>quicklook</code> function, the figures generated will **not** plot to the screen but will be available in the mounted refl_code/Files volume mounted locally.


---

## **Command line version homework:**
### 1. Check environment variables are set:

<code>echo $EXE</code> \
<code>echo $ORBITS</code> \
<code>echo $REFL_CODE</code>

If you don't get a response, these probably aren't set correctly.  

You should get something like:
```console
echo $EXE
/path/to/directory/EXE
```

If you're running the docker gnssrefl,
you should get:

```console
echo $EXE
/home/jovyan/gnssir/gnssrefl/EXE
```

### 2. Check that EXE executables are present:
(these executables are case sensitive!)
```console
ls $EXE
CRX2RNX  gfzrnx  teqc
```

### 3. Check that subprocess dependencies are in path:

<code>which gunzip</code>\
<code>which unxz</code>\
<code>which uncompress</code>

If you don't get a response, these dependencies are probably not installed in your path. \
If you're running the docker image,
you should get:

```console
which gunzip
/usr/bin/gunzip
```
### 4. Run a quick test of rinex2snr:

#### a. simple use case that requires Hatanaka decompression and broadcast orbits:

<code>rinex2snr p042 2018 150</code>


If you get:

*SUCCESS: SNR file was created: ...*

you've successfully run the rinex2snr program that:
* downloaded and uncompressed [Hatanaka](https://www.unavco.org/data/gps-gnss/hatanaka/hatanaka.html) rinex for a single station (p042) for a single day (doy 150 in 2018)
* downloaded GPS broadcast orbits
* calculated azimuth and elevation for each satellite at each epoch given these orbits
* wrote this az/el, signal, time and CN0 information to a formatted snr output file
for future analysis.
Reminder, the .66 file name suffix refers to the
[elevation masking options](https://github.com/kristinemlarson/gnssrefl#iv-rinex2snr---extracting-snr-data-from-rinex-files-).

If the file is not created - check the logs directory for additional information.

#### b. simple use case that requires Hatanaka decompression and uses SP3 orbits:
<code>rinex2snr p042 2018 150 -orb gnss</code>

If you get:
*SNR file exists...*\
This is because the logic of gnssrefl checks for an snr file prior to processing.
Remember this fact if you ever want to **re**process with different orbits!  (we'll try again in part 2)

#### b-2.  simple use case that requires CRX2RNX and SP3 orbits: \
Now we will overwrite the previous SNR file to use the different orbits.

<code>rinex2snr p042 2018 150 -orb gnss -overwrite True</code>


If you get:
*SUCCESS: SNR file was created: ...*\
you've successfully:
* downloaded and uncompressed hatanaka rinex for a single station (p042)
for a single day (doy 150 in 2018)
* downloaded SP3 format GNSS orbits from the GFZ archive
* calculated azimuth and elevation for each satellite at each epoch
* wrote this az/el, signal, time and CN0 information to a formatted
snr output file for future analysis.

If you get an error, we will need to address this.
We will begin to compile a list of any additional common errors and solutions here.

#### c. (optional but encouraged) RINEX 3 simple use case that requires that you install gfzrnx

If you are interested in using RINEX version 3 data, please run this test: \
<code>rinex2snr onsa00swe 2020 1 -archive cddis -orb gnss </code>

If you get:
*SUCCESS: SNR file was created: ...* \
you've successfully:
* downloaded and uncompressed rinex 3 for a single station (onsa)
for a single day (doy 298 in 2020) from the cddis archive
* converted rinex 3 to rinex 2 using gfzrnx executable
* downloaded SP3 format GNSS orbits from the GFZ archive
* calculated azimuth and elevation for each satellite at each epoch
* wrote this az/el, signal, time and CN0 information to a formatted
snr output file for future analysis.
