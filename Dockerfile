FROM ubuntu:18.04

LABEL maintainer="yannforget@mailbox.org"

ENV DEBIAN_FRONTEND=noninteractive

RUN useradd -ms /bin/bash shedecides

# Update & upgrade system
RUN apt-get -y update && \
    apt-get -y upgrade

# Setup locales
RUN apt-get install -y locales
RUN echo LANG="en_US.UTF-8" > /etc/default/locale
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Install python 2.7, Pandas and NumPy
RUN apt-get install -y --no-install-recommends \
        python2.7 \
        python-numpy \
        python-pandas

# Install GRASS GIS
# A compiling environment is needed to install GRASS extensions, 
# along with GRASS development files
RUN apt-get install -y \
        wget \
        software-properties-common \
        build-essential && \
    add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable && \
    apt-get -y update && \
    apt-get -y install \
        grass \
        grass-doc \
        grass-dev \
        grass-dev-doc

# Reduce image size
RUN apt-get autoremove -y && \
    apt-get clean -y

# Install manually some missing files from grass-doc package
# Necessary to compile GRASS extensions
RUN mkdir /home/shedecides/grass-doc && \
    cd /home/shedecides/grass-doc && \
    wget 'https://launchpad.net/~ubuntugis/+archive/ubuntu/ubuntugis-unstable/+files/grass-doc_7.6.1-1~bionic2_all.deb' && \
    mv grass-doc_7.6.1-1~bionic2_all.deb grass-doc.deb && \
    ar x grass-doc.deb && \
    tar xf data.tar.xz && \
    cp -R usr/share/doc/grass-doc/html/* /usr/share/doc/grass-doc/html/ && \
    cd /home/shedecides && \
    rm -R grass-doc

USER shedecides
WORKDIR /home/shedecides
COPY SheDecides_Python_chain.py shedecides.py
COPY LIBS ./LIBS

ENTRYPOINT ["python"]
CMD ["shedecides.py"]
