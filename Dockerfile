FROM python:3.8-slim-buster 
LABEL maintainer="EARTHSCOPE"
ARG DEBIAN_FRONTEND=noninteractive
ARG TARGETARCH

# build requirements
RUN apt-get update && \
  apt-get install -y gfortran python3-pip unzip wget vim 

## executables
RUN mkdir -p /etc/gnssrefl/exe /etc/gnssrefl/orbits /etc/gnssrefl/refl_code/Files /etc/gnssrefl/notebooks
COPY vendor/gfzrnx_2.0-8219_armlx64 /etc/gnssrefl/exe/
COPY vendor/gfzrnx_2.0-8219_lx64 /etc/gnssrefl/exe/

RUN if [ "$TARGETARCH" = "arm64" ] ; then \
  cp /etc/gnssrefl/exe/gfzrnx_2.0-8219_armlx64 /etc/gnssrefl/exe/gfzrnx; else \
  cp /etc/gnssrefl/exe/gfzrnx_2.0-8219_lx64 /etc/gnssrefl/exe/gfzrnx; \
  fi

RUN chmod +x /etc/gnssrefl/exe/gfzrnx

COPY vendor/crx2rnx.c /etc/gnssrefl/exe/
COPY vendor/rnx2crx.c /etc/gnssrefl/exe/
RUN cd /etc/gnssrefl/exe && \
  gcc -ansi -O2 crx2rnx.c -o CRX2RNX \
  && gcc -ansi -O2 rnx2crx.c -o RNX2CRX

ENV PATH="/etc/gnssrefl/exe:$PATH" 

RUN pip install numpy --upgrade --ignore-installed
COPY pyproject.toml README.md setup.py /usr/src/gnssrefl/
COPY gnssrefl /usr/src/gnssrefl/gnssrefl
COPY notebooks/learn-the-code /etc/gnssrefl/notebooks/learn-the-code
COPY notebooks/use-cases /etc/gnssrefl/notebooks/use-cases
RUN pip3 install --no-cache-dir /usr/src/gnssrefl

ENV PIP_DISABLE_PIP_VERSION_CHECK=1

ENV EXE=/etc/gnssrefl/exe
ENV ORBITS=/etc/gnssrefl/refl_code
#ENV ORBITS=/etc/gnssrefl/orbits
ENV REFL_CODE=/etc/gnssrefl/refl_code
ENV DOCKER=true

WORKDIR /usr/src/gnssrefl
