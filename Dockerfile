FROM ubuntu:18.04

LABEL maintainer="yannforget@mailbox.org"

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /usr/opt/she-decides
COPY SheDecides_Python_chain.py shedecides.py
COPY LIBS ./LIBS

# Install python 2.7, Pandas and NumPy
RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get install -y --no-install-recommends \
        python2.7 \
        python-numpy \
        python-pandas

# Install GRASS GIS
RUN apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable && \
    apt-get -y update && \
    apt-get -y install grass

# Create data directories
RUN mkdir -p /usr/opt/she-decides/data/input && \
    mkdir -p /usr/opt/she-decides/data/output
