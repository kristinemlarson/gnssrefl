# [Installing and running the gnssrefl docker image](https://github.com/kristinemlarson/gnssrefl/pkgs/container/gnssrefl)


Please send your feedback on these instructions 
by [submitting a GitHub issue](https://github.com/kristinemlarson/gnssrefl/blob/master/.github/ISSUE_TEMPLATE/bug_report.md).

## Install Docker
&ensp;&ensp; Pick your system and follow instructions on the Docker website 

- [Mac](https://docs.docker.com/docker-for-mac/install/) 
- [Windows](https://docs.docker.com/docker-for-windows/install/)
- [Ubuntu](https://docs.docker.com/install/linux/docker-ce/ubuntu/) 

Once installed, type `docker run hello-world` in the terminal to check that it installed correctly.

More information on [dockers.](https://docs.docker.com/get-started/) 

If you want to process EarthScope data, you will need to 
create an [EarthScope profile.](https://data.unavco.org/user/profile/info).

[Docker Desktop](https://www.docker.com/products/docker-desktop) is a useful tool.

Our docker has vim for editing text files.

When running the software in the Docker, plots will **not** be automatically displayed to the screen.
You need to look at these files using your preferred application (i.e. clicking twice in a finder window).

In the help section below you will be using linux commands in a terminal window. 
Make sure that you hit the return key after typing a command.

## Update the Docker <a name="Update Docker"></a>

If you have previously installed the gnssrefl Docker, it is important that you update it.

`docker pull ghcr.io/kristinemlarson/gnssrefl:latest`

You need to do this before you start the gnssrefl Docker.

## Run the gnssrefl Docker 

Open a terminal window. You need to make a folder where you plan to run 
the code.  Navigate to where you want to create that folder. As an example, here we 
will call it `local` 

`mkdir local`

Change into that directory  

`cd local`

Make another directory so that you can retain results:

`mkdir refl_code`

Start the docker container: 

```bash
docker run -it -v $(pwd)/refl_code:/etc/gnssrefl/refl_code/  --name gnssrefl ghcr.io/kristinemlarson/gnssrefl:latest /bin/bash
```
`docker run` is somewhat self-explanatory, but the other inputs can be confusing.

`--name` tells the docker where the docker image is stored - and what its local name will be. 
If you are running docker hub, gnssrefl is what will show up.

`-it` calls interactive process (bin/bash shell) 

`-v` mounts external volumes to allow the user to keep their processing results and figures 

The `-v` command associates a docker-named directory (`/etc/gnssrefl/refl_code`) with a 
physical directory on your machine (`/usr/kristine/local/refl_code`). You may notice that the command 
uses $(pwd) and not the full name. `pwd` is a linux command that returns the current working directory. You can see how
that works by typing `pwd`. When using the docker, keep in mind that there are these two naming 
conventions - one used by the docker and one used by your physical machine.

It is worth spending a little time on these directories becaues gnssrefl has specific 
rules about where files are expected to be and where new files will be written.  These are a little easier
to navigate when you are doing a regular python install, but the Docker has a lot of advantages too. 
Let's start by looking to see what folders are provided by the Docker. Type:

`ls /etc/gnssrefl/`

This returns the names of four directories:

`exe  notebooks	orbits	refl_code`

Three of those directories are pre-defined by docker (exe, orbits, and notebooks) and the 
fourth (refl_code) is specifically for the inputs/outputs of your work.

Let's try a command that downloads a RINEX file **and** translates it. The required inputs are station name
(sc02), year(2023) and day of year (150). We also use an optional input for archive (sopac) so we can
avoid setting up an EarthScope account:

`rinex2snr sc02 2023 150 -archive sopac`

**rinex2snr** needs to download two files:  the RINEX file (from sopac) and 
an orbit file (in this example the orbit file will come from GFZ). 
We don't need to keep the RINEX file, so it will be deleted after it is used. We might 
want to use the orbit file again (for another GNSS station), so it is saved.
It is stored in that orbits directory we saw earlier. You can check that:

`ls /etc/gnssrefl/orbits/2023/sp3`

You can also check for the output of rinex2snr, which is a SNR file:

`ls /etc/gnssrefl/refl_code/2023/snr/sc02`

You should see

`sc021500.23.snr66.gz`

If you want to take a quick look at these data:

`quickLook sc02 2023 150`

creates two png files. Notice that the screen says:

`Plot saved to  /etc/gnssrefl/refl_code/Files/sc02/quickLook_lsp.png`

`Plot saved to  /etc/gnssrefl/refl_code/Files/sc02/quickLook_summary.png`

That tells you where they are using the docker folder definitions.
If you were using a local python install, the plots would be automatically displayed. 
To look at them using a docker, you have to navigate to the folder where they are 
stored on your machine. In this example, they are stored in :

`/usr/kristine/local/refl_code/Files/sc02` 

On many machines, simply clicking twice on the filename brings it to the screen, but you can 
use the way that works best for you. Once you are used to the gnssrefl directory structure, this will 
become easier. But until you do, remember that the location of all outputs are 
printed to the screen. This is to help you find them.

In most of the gnssrefl code and documentation the location of files are defined with 
environment variables. These are also available when using the docker. Let's say you are in the terminal
window of the Docker and you want to list the contents of the folder that the Docker calls 
`/etc/gnssrefl/refl_code/Files`. You can type:

`ls $REFL_CODE/Files`

It can be a bit confusing to know how to turn your Docker off and on again. Please check the 
shutdown section below for assistance.

## Analyze your own GNSS data

If you want to use your own GNSS data, you have some options. For convenience, here we 
will only cover RINEX 2.11 users. The [naming conventions for RINEX files](https://gnssrefl.readthedocs.io/en/latest/pages/file_structure.html) are the same whether you run gnssrefl using a regular python install or the Docker. 

I assume that you have already decided where to run the docker and you have opened the terminal 
window to that directory. You have two choices. We will cover them both.

Probably the best method is to store your RINEX files in the standard gnssrefl directory structures. 
The main benefit is that the RINEX files will *not* be deleted after you translate them.
gnssrefl has very specific requirements for these folders.  For RINEX files from the year 
2023 and with a station name of abcd, you need to use this command (this is before you start the docker)

`mkdir -p refl_code/2023/rinex/abcd`

Make sure that the RINEX files are stored in `/usr/kristine/local/refl_code/2023/rinex/abcd`. 

If you only have one or two files to translate, it is a bit annoying to have to create extra folders. 
The code allows you to put them in your local working directory. The downside is that 
they will be deleted after they are translated. If you have not previously done so, make sure to 
create the refl_code directory:

`mkdir refl_code`

Make sure the RINEX files are stored in `/usr/kristine/local/refl_code`. 

The gnssrefl code should recognize various RINEX types - gzip, Hatanaka compression, unix compression and so on.  
Please check the [rinex2snr](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.rinex2snr_cl.html) 
documentation to see what endings are allowed or when capitalization of filenames is allowed. There is also
information there on how to store your RINEX 3 files. 

One can also use NMEA files in gnssrefl. The translation code for NMEA files was 
written by a user that prefers a different directory structure, i.e.
if the station is abcd and the files are from the year 2023, you should store them in:

`/usr/kristine/local/refl_code/nmea/abcd/2023` 

For other details about nmea2snr, please see the [documentation](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.nmea2snr_cl.html).

Once you have your files stored appropriately, start your Docker just like you were shown earlier.

```bash
docker run -it -v $(pwd)/refl_code:/etc/gnssrefl/refl_code/  --name gnssrefl ghcr.io/kristinemlarson/gnssrefl:latest /bin/bash
```

At this point you can start analyzing your data. If your RINEX file called abcd1500.23o is stored
in the appropriate directory, you can translate it using the -nolook option:

`rinex2snr abcd 2023 150 -nolook T`

At this point you can follow the standard documentation.  

## Shutdown Docker <a name="Shutdown"></a>

To exit down the container from the terminal, type:

`exit`

After exiting, to re-enter this container:

`docker start gnssrefl` followed by `docker exec -it gnssrefl /bin/bash`

To shut down the docker container type: 

`docker stop gnssrefl`

If you need to see the container(s) you have running you can use `docker ps`

If you need to see all container(s) you can use `docker container ls -a`


## For WINDOWS users:

Thank you Paul Wu and James Monaco 

Remember to install [Docker for Windows](https://docs.docker.com/desktop/windows/install/)

Problem: `WSL2 Installation is incomplete`.  

* Solution: Need to download and install [from step 4](https://docs.microsoft.com/en-us/windows/wsl/install-manual#step-4---download-the-linux-kernel-update-package)

Problem: Docker stuck at initial stage

* Solution: restart the computer after docker installation

Problem: need to convert existing WSL environment into WSL 2 and associate with Docker

* Solution: follow [this documentation](https://docs.docker.com/desktop/windows/wsl/)

To run the gnssrefl Docker

Docker run commands have slightly different syntax to accomodate windows directories in volume mounting:

Use either Windows Power Shell:

```bash
docker run -it -v ${pwd}\refl_code:/etc/gnssrefl/refl_code/ --name gnssrefl ghcr.io/kristinemlarson/gnssrefl:latest /bin/bash 
```

Or Windows Command Line:

```bash
docker run -it -v %cd%\refl_code:/etc/gnssrefl/refl_code/ --name gnssrefl ghcr.io/kristinemlarson/gnssrefl:latest /bin/bash 
```

Execute docker run command (see above) in terminal window

Feedback from jupyter notebook user:

About folder permission: In the notebook environment test, the error prompted that the program could not 
write to the file.  This is remedied by changing the permissions of the folder from the command line.

Docker folder `/etc/gnssrefl/refl_code` will be visible in Windows under `C:\Users\yourlogin\refl_code`

If you modify the source code, you'll need to make the installation [editable](https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-e):

`cd /usr/src/gnssrefl; pip install -e .`


## additional references:
* [gnssrefl docker file](https://github.com/kristinemlarson/gnssrefl/blob/master/Dockerfile)


