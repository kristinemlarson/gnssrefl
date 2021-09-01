## Homework 0

**goal:** to make sure you have properly installed <code>gnssrefl</code> 

[You are strongly encouraged to read the documentation.](https://github.com/kristinemlarson/gnssrefl)

There are two versions of this homework:  A Jupyter Notebook version, and a gnssrefl command line version.  
Pick the method that you prefer to do your analysis in the course, or experiment with both.

## **Jupyter Notebook version:**

run the HW0 notebook from the notebook directory

there are two versions: 

* a [jupyter notebook docker container](https://hub.docker.com/r/unavdocker/gnssrefl_jupyter)

or  

* [jupyter notebook repository to clone and run locally on your machine](https://www.unavco.org/gitlab/gnss_reflectometry/gnssrefl_jupyter).  Use the version you intend to use for the course, and/or experiment with both. \

Skip the rest of the steps below here-- they will be covered in the notebook version of HW0.

## **Command line version setup:**

### Runs locally on linux or macOS using code from GitHub


* git clone https://github.com/kristinemlarson/gnssrefl
* cd into that directory, set up a virtual environment, a la python3 -m venv env
* activate your virtual environment
* pip install .

### Docker gnssrefl command line container option

[docker image run commands](https://www.unavco.org/gitlab/gnss_reflectometry/gnssrefl_docker#repo-for-gnssrefl-command-line-docker-image)

(run in directory location that you wish to store processed results)

<code>docker run -it -v $(pwd)/REFL_CODE:/home/jovyan/gnssir/gnssrefl/REFL_CODE/ -v $(pwd)/REFL_CODE/Files:/home/jovyan/gnssir/gnssrefl/REFL_CODE/Files unavdocker/gnssrefl:latest /bin/bash</code>

cd into gnssrefl directory

*NB:* if you use the <code>quicklook</code> function, the figures generated will **not** plot to the screen but will be available in the mounted REFL_CODE/Files volume mounted locally.


---

## **Command line version homework:**
### 1. Check environment variables are set:

<code>echo $EXE</code> \
<code>echo $ORBITS</code> \
<code>echo $REFL_CODE</code>

If you don't get a response, these probably aren't set correctly.  If you're running the docker gnssrefl,
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

#### a. simple use case that requires hatanaka decompression and broadcast orbits:

<code>rinex2snr p042 2018 150</code>


If you get:

*SUCCESS: SNR file was created: ...*

you've successfully run the rinex2snr program that:
* downloaded and uncompressed [hatanaka](https://www.unavco.org/data/gps-gnss/hatanaka/hatanaka.html) rinex for a single station (p042) for a single day (doy 150 in 2018)
* downloaded GPS broadcast orbits
* calculated azimuth and elevation for each satellite at each epoch given these orbits
* wrote this az/el, signal, time and CN0 information to a formatted snr output file
for future analysis.
Reminder, the .66 file name suffix refers to the
[elevation masking options](https://github.com/kristinemlarson/gnssrefl#iv-rinex2snr---extracting-snr-data-from-rinex-files-).

If the file is not created - check the logs directory for additional information.

#### b. simple use case that requires CRX2RNX and SP3 orbits:
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

#### c. (optional but encouraged) RINEX 3 simple use case that requires gfzrnx
**If** you are interested in using RINEX version 3 data, please run this test: \
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
