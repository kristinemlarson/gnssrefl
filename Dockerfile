FROM unavdocker/gnssrefl_base
LABEL maintainer="EARTHSCOPE"

ENV PIP_DISABLE_PIP_VERSION_CHECK=1

COPY pyproject.toml README.md setup.py /usr/src/gnssrefl/
COPY gnssrefl /usr/src/gnssrefl/gnssrefl
RUN pip3 install --no-cache-dir /usr/src/gnssrefl
RUN mkdir -p /etc/gnssrefl/refl_code/input/
RUN cp /usr/src/gnssrefl/gnssrefl/gpt_1wA.pickle /etc/gnssrefl/refl_code/input/
RUN cp /usr/src/gnssrefl/gnssrefl/station_pos.db /etc/gnssrefl/refl_code/Files/
WORKDIR /usr/src/gnssrefl
