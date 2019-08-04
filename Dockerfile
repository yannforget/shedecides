FROM ubuntu:18.04

LABEL maintainer="yannforget@mailbox.org"

ENV DEBIAN_FRONTEND=noninteractive

RUN useradd -ms /bin/bash shedecides

# Install python 2.7, Pandas and NumPy
RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get install -y --no-install-recommends \
        python2.7 \
        python-numpy \
        python-pandas

# Install GRASS GIS
# A compiler is needed to install GRASS extensions, i.e.
# make, gcc, and grass development files
RUN apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable && \
    apt-get -y update && \
    apt-get -y install grass grass-dev build-essential

USER shedecides
WORKDIR /home/shedecides
COPY SheDecides_Python_chain.py shedecides.py
COPY LIBS ./LIBS

ENTRYPOINT ["python"]
CMD ["shedecides.py"]
