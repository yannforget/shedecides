
#!/usr/bin/env python

"""
Functions related to environment variables
"""

import os,sys
from config import config_parameters


def setup_environmental_variables():
    """Setting the environment variables for using GRASS GIS python libraries. 

    Documentation available on: https://grass.osgeo.org/grass76/manuals/variables.html
    """

    # Check if environment variables exist, and if not, create them (empty).
    if not 'PYTHONPATH' in os.environ:
        os.environ['PYTHONPATH']=''
    if not 'LD_LIBRARY_PATH' in os.environ:
        os.environ['LD_LIBRARY_PATH']=''
    # Set environment variables
    os.environ['GISBASE'] = config_parameters['GISBASE']
    os.environ['PATH'] += os.pathsep + os.path.join(os.environ['GISBASE'],'bin')
    os.environ['PATH'] += os.pathsep + os.path.join(os.environ['GISBASE'],'script')
    os.environ['PATH'] += os.pathsep + os.path.join(os.environ['GISBASE'],'lib')
    os.environ['PYTHONPATH'] += os.pathsep + os.path.join(os.environ['GISBASE'],'etc','python')
    os.environ['PYTHONPATH'] += os.pathsep + os.path.join(os.environ['GISBASE'],'etc','python','grass')
    os.environ['PYTHONPATH'] += os.pathsep + os.path.join(os.environ['GISBASE'],'etc','python','grass','script')
    os.environ['PYTHONLIB'] = config_parameters['PYTHONLIB']
    os.environ['LD_LIBRARY_PATH'] += os.pathsep + os.path.join(os.environ['GISBASE'],'lib')
    os.environ['GIS_LOCK'] = '$$'
    os.environ['GISRC'] = os.path.join(config_parameters['workingdir'], '.grass7', 'rc')
    # The following should only be necessary on MS Windows or for custom GDAL
    # installations
    #os.environ['GDAL_DATA'] = config_parameters['GDAL_DATA']


    ## Define GRASS-Python environment
    sys.path.append(os.path.join(os.environ['GISBASE'],'etc','python'))


def print_environmental_variables():
    """Display the current environment variables of your computer."""
    for key in os.environ.keys():
        print "%s = %s \t" % (key,os.environ[key])
