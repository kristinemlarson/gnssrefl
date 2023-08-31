## Homework 0

**goal:** to make sure you have properly installed <code>gnssrefl</code>

[You are strongly encouraged to read the documentation.](https://gnssrefl.readthedocs.io/en/latest/pages/README_install.html)

There are two versions of this homework: a Jupyter Notebook version and a command line version.  
Pick the method that you prefer to do your analysis in the course, or experiment with both.

To access Earthscope data, [an account is required](https://data-idm.unavco.org/user/profile/login).

## **Jupyter Notebook version:**

run the [HW0 notebook](https://www.unavco.org/gitlab/gnss_reflectometry/gnssrefl_jupyter/-/blob/master/notebooks/learn-the-code/part_0.ipynb) from the [jupyter notebook repository, either via docker or to clone and run locally on your machine](https://www.unavco.org/gitlab/gnss_reflectometry/gnssrefl_jupyter).


## **Command line version options: **

### GNSSREFL via GITHUB (local version)
[Installation instructions.](https://gnssrefl.readthedocs.io/en/latest/pages/README_install.html#local-python-install)

### GNSSREFL DOCKER (containerized version)

[Docker command line instructions](https://gnssrefl.readthedocs.io/en/latest/pages/docker_cl_instructions.html) for [Docker image](https://github.com/kristinemlarson/gnssrefl/pkgs/container/gnssrefl)

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
