FROM unavdocker/gnssrefl_base
LABEL maintainer="UNAVCO"

COPY pyproject.toml README.md setup.py /usr/src/gnssrefl/
COPY gnssrefl /usr/src/gnssrefl/gnssrefl
RUN pip3 install /usr/src/gnssrefl
RUN mkdir -p /etc/gnssrefl/refl_code/input/
RUN cp /usr/src/gnssrefl/gnssrefl/gpt_1wA.pickle /etc/gnssrefl/refl_code/input/
