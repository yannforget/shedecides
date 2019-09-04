# She Decides: Containerized Script

This repository provides a containerized version of the scripts created in the context of the *"She Decides"* project. Initial scripts have been developed by ANAGEO (Université Libre de Bruxelles), based on a preliminary work by the University of Namur.

## Launching the script

``` sh
# Pull the repository & build the docker image
git clone https://github.com/yannforget/shedecides.git
cd shedecides
docker build -t she-decides .

# Use demonstration data
mkdir -p data/input
tar xzvf DATA_DEMO_Senegal.tgz
mv DATA/* data/input
rm -r DATA

# Run container
docker run \
    --name she-decides \
    --volume $pwd/data:/home/shedecides/data:rw,z \
    --privileged \
    she-decides
```

## Data

* Input data are located in `shedecides/data/input`.
* Output data will be located in `shedecides/data/output`.

## Configuration

Configuration variables are read from `LIBS/config.py`. The original file can be overwritten by a local copy using a Docker volume flag, such as: `--volume $pwd/my_config.py:/home/shedecides/LIBS/config.py`.
