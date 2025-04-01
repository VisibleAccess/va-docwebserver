FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

#
# libhdf5-dev  is needed to pip install netifaces

# Install package dependencies
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    gcc-aarch64-linux-gnu \
    python3-dev \
    libsndfile1-dev \
    modemmanager \
    python3-pip \
    vim-tiny \
    python3-venv \
    inetutils-ping \
    traceroute \
    iproute2 \
    dnsutils \
    curl \
    i2c-tools && \
    apt-get clean


RUN mkdir webserver
COPY ./docwebserver/requirements.txt webserver/.
RUN pip3 install -r /webserver/requirements.txt


COPY ./docwebserver/. /webserver/.
COPY webstorm-docweb/static webserver/static

CMD ["python3", "/webserver/manage.py", "runserver", "--noreload", "0.0.0.0:80"]