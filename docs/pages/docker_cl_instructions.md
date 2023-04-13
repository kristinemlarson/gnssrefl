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

Reminder: If you want to process EarthScope data, you will need to create [an EarthScope profile.](https://data.unavco.org/user/profile/info)

change directory into the local directory that you wish to keep your processed results

```bash
docker run -it -v $(pwd)/refl_code:/etc/gnssrefl/refl_code/  --name gnssrefl ghcr.io/kristinemlarson/gnssrefl:latest /bin/bash
```

Description of the commands used:  

`-it` calls interactive process (bin/bash shell) 

`-v` mounts external volumes to allow the user to keep their processing results and figures 

Now you can start working with the [gnssrefl code.](https://github.com/kristinemlarson/gnssrefl#understanding)

### Notes:
docker has vim for editing text files (ie .json station config file)

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

After exitining, to re-enter this container, `docker start gnssrefl` followed by `docker exec -it gnssrefl /bin/bash`

To shut down the docker container run `docker stop gnssrefl`

If you need to see the container(s) you have running you can use `docker ps`

If you need to see all container(s) you can use `docker container ls -a`

### Update Docker Image to newest version <a name="Update Docker"></a>

`docker pull ghcr.io/kristinemlarson/gnssrefl:latest`


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

## additional references:
* [gnssrefl base image dockerfile](https://gitlab.com/gnss_reflectometry/gnssrefl_docker_base_img/-/blob/master/Dockerfile)
* [gnssrefl docker file](https://github.com/kristinemlarson/gnssrefl/blob/master/Dockerfile)


