# [Installing the gnssrefl docker image from the GitHub Container Registry](https://github.com/kristinemlarson/gnssrefl/pkgs/container/gnssrefl)

Please send your feedback on these instructions to Tim Dittmann at EarthScope, or better still, [submit a GitHub issue](https://github.com/kristinemlarson/gnssrefl/blob/master/.github/ISSUE_TEMPLATE/bug_report.md).

for jupyter notebook version, please see [gnssrefl_jupyter instructions](https://www.unavco.org/gitlab/gnss_reflectometry/gnssrefl_jupyter)
## Install Docker
&ensp;&ensp; Pick your system and follow instructions on the Docker website. 
* [**Mac**](https://docs.docker.com/docker-for-mac/install/) 
* [**Windows**](https://docs.docker.com/docker-for-windows/install/)
* [**Ubuntu**](https://docs.docker.com/install/linux/docker-ce/ubuntu/) 

Once installed, type `docker run hello-world` in terminal to check if installed correctly.

More information on [getting started, testing your installation, and developing.](https://docs.docker.com/get-started/) 

[Docker Desktop](https://www.docker.com/products/docker-desktop) is a useful tool.

## Run gnssrefl Docker

Reminder: If you want to process EarthScope data, you will need to create [an EarthScope profile.](https://data.unavco.org/user/profile/info).

change directory into the local directory that you wish to keep your processed results

```bash
docker run -it -v $(pwd)/refl_code:/etc/gnssrefl/refl_code/  --name gnssrefl ghcr.io/kristinemlarson/gnssrefl:latest /bin/bash
```

Description of the commands used:  

`-it` calls interactive process (bin/bash shell) 

`-v` mounts external volumes to allow the user to keep their processing results and figures 

Now you can start working with the [gnssrefl code.](https://github.com/kristinemlarson/gnssrefl#understanding)


### Kristine's Docker advice 

Here are my recommendations on how to use the code in the Docker, with special advice for using the nolook option.

Open a window. You will be using linux commands. Make sure that you hit the return key after typing a command.

Ensure that you are using the latest docker : 

`docker pull ghcr.io/kristinemlarson/gnssrefl:latest`

Make a directory where you plan to run the docker. I will call mine local, i.e. `mkdir local`

Change into that directory,  `cd local`


If you are new to linux, make sure you know the full name of this directory.  type `pwd` and see what
come back.  I will pretend that what came back is `/usr/kristine/local` for my example

If you want to use GNSS data that are stored in archives, you can stop reading and just run the relevant commands provided above.
If you want to use your own GNSS data, you have some options. For convenience, here I will only cover RINEX 2.11 users. 
The [naming conventions for RINEX files](https://gnssrefl.readthedocs.io/en/latest/pages/file_structure.html) are 
the same whether you run gnssrefl using a regular python install or the Docker. 
You first need to create the *local directory*, `mkdir refl_code` . Then you have two choices: 

1. Your RINEX files can be stored in `/usr/kristine/local/refl_code`. They will be deleted after translation, so don't 
put your only copy there.

2. Your RINEX files can be stored in a the standard gnssrefl storage areas. Your RINEX files will *not* be deleted after you translate them.
For a RINEX file from the year 2023 and with a station name of abcd, these files should be stored in the directory called `/usr/kristine/local/refl_code/2023/rinex/abcd`. This means you have to create those additional directories.  You can do that with an additional flag to the mkdir command, `mkdir -p refl_code/2023/rinex/abcd`.

The code should recognize various RINEX types - gzip, Hatanaka compression, unix compression and so on.  
Please check the [rinex2snr](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.rinex2snr_cl.html) 
documentation to see what endings are allowed or when capitalization of filenames is allowed. There is also
information there on how to store your RINEX 3 files.

Now start your docker.   

```bash
docker run -it -v $(pwd)/refl_code:/etc/gnssrefl/refl_code/  --name gnssrefl ghcr.io/kristinemlarson/gnssrefl:latest /bin/bash
```

In addition to starting the Docker, it also associates a directory 
it calls `/etc/gnssrefl/refl_code` with a physical directory on your machine called `/usr/kristine/local/refl_code`
Now that that is set up, you should be able to run differnt gnssrefl commands. Example:

`rinex2snr abcd 2023 305 -nolook T`

The SNR output will be stored in your Docker bucket in the directory it calls `/etc/gnssrefl/refl_code/2023/snr/abcd`. 
On your local machine it will live in `/usr/kristine/local/refl_code/2023/snr/abcd`

Another example:

`quickLook abcd 2023 305`

This creates two png files (`quickLook_summary.png` and `quickLook_lsp.png`) that are 
stored in `/usr/kristine/local/refl_code/Files/abcd`. The code should always print the location of 
output files so you don't have to remember all these details.

When you run `gnssir` the output txt files will be stored locally in `/usr/kristine/local/refl_code/2023/results/abcd`
while your Docker will define it as being stored in `/etc/gnssrefl/refl_code/2023/results/abcd`

You can change to different directories using either the environment variable name or the Docker names  

`cd /etc/gnssrefl/refl_code/Files/abcd`

or

`cd $REFL_CODE/Files/abcd`

I hope this helps. I have posted an issue on github to make sure this page is up to date with the current
release of the software.

### Update Docker Image to newest version <a name="Update Docker"></a>

`docker pull ghcr.io/kristinemlarson/gnssrefl:latest`

### Notes:
The first time you run this container from a specific path, the Earthscope token will be installed once in the container at `` and locally at `/localpath_of_dockerrun/refl_zones` (the volume you mounted with the `-v` command)

docker has vim for editing text files (ie .json station config file)

When running the software in the docker, plots/files will **not** print to the screen (think quickLook or daily_average utilities), but will be stored on the local machine in the directory that the docker run command was issued.

If you want to process RINEX files that are stored on your local machine, you can copy them into 
`/refl_code/` local directory that is already mounted to the container given the previous run command.  

If you have a lot of RINEX files and want to keep them organized, you should copy them 
into `refl_code/rinex/station/yyyy/`, where station is the lowercase 4char ID and yyyy is the year. 
You should then mount that directory in the docker run command as follows: 

```bash
docker run -it -v $(pwd)/refl_code:/etc/gnssrefl/refl_code/ -v $(pwd)/refl_code/rinex/station/yyyy:/etc/gnssrefl/refl_code/rinex/station/yyyy/ --name gnssrefl ghcr.io/kristinemlarson/gnssrefl:latest /bin/bash 
```

### Shutdown Docker <a name="Shutdown"></a>
To exit down the container from the terminal, type `exit`

After exiting, to re-enter this container, `docker start gnssrefl` followed by `docker exec -it gnssrefl /bin/bash`

To shut down the docker container run `docker stop gnssrefl`

If you need to see the container(s) you have running you can use `docker ps`

If you need to see all container(s) you can use `docker container ls -a`


## For WINDOWS USERS:
(thank you Paul Wu and James Monaco @ Univ. of CO for this)

1. Install [Docker for Windows](https://docs.docker.com/desktop/windows/install/)

Problem: `WSL2 Installation is incomplete`.  

* Solution: Need to download and install [from step 4](https://docs.microsoft.com/en-us/windows/wsl/install-manual#step-4---download-the-linux-kernel-update-package)

Problem: Docker stuck at initial stage

* Solution: restart the computer after docker installation

Problem: need to convert existing WSL environment into WSL 2 and associate with Docker

* Solution: follow [this documentation](https://docs.docker.com/desktop/windows/wsl/)

2. Run gnssrefl Docker

Docker run commands have slightly different syntax to accomodate windows directories in volume mounting:

Use either Windows Power Shell:

```bash
docker run -it -v ${pwd}\refl_code:/etc/gnssrefl/refl_code/ --name gnssrefl ghcr.io/kristinemlarson/gnssrefl:latest /bin/bash 
```

Or Windows Command Line:

```bash
docker run -it -v %cd%\refl_code:/etc/gnssrefl/refl_code/ --name gnssrefl ghcr.io/kristinemlarson/gnssrefl:latest /bin/bash 
```

execute docker run command (see above) in terminal window

Feedback from jupyter notebook user:

About folder permission: In the notebook environment test, the error prompted that the program could not 
write to the file.  This is remedied by changing the permissions of the folder from the command line.

Docker folder /etc/gnssrefl/refl_code will be visible in Windows under C:\Users\yourlogin\refl_code

If you modify the source code, you'll need to make the installation [editable](https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-e):
`cd /usr/src/gnssrefl; pip install -e .`

## additional references:
* [gnssrefl base image dockerfile](https://gitlab.com/gnss_reflectometry/gnssrefl_docker_base_img/-/blob/master/Dockerfile)
* [gnssrefl docker file](https://github.com/kristinemlarson/gnssrefl/blob/master/Dockerfile)


