#!/usr/bin/env python
# coding: utf-8

# Accessibility to health facilities

# This python code implements the methods developed by ANAGEO (ULB), based on preliminary
# work by UNamur. 
# 
# The code was developped on Linux, 
# but has also been tested on Windows 7 Professional and GRASS GIS 7.6.0 installed with the 
# OSGEO4W (64bit) installer.
#
# Copyright 2019 Moritz Lennert, Sabine Vanhuysse, Taïs Grippa, ULB

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
# and associated documentation files (the "Software"), to deal in the Software without 
# restriction, including without limitation the rights to use, copy, modify, merge, publish, 
# distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the 
# Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or 
# substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING 
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Define working environment

# Import libraries needed for setting parameters of operating system 
import os
import sys

# Add folder with python libs to path
script_path = os.path.dirname(os.path.realpath(__file__))
src = os.path.join(script_path, 'LIBS')
if src not in sys.path:
    sys.path.append(src)

# Import configuration parameters
# Please edit the file in `../SRC/config.py`, containing the configuration parameters
# according to your own computer setup.

from config import config_parameters, data, outputs, hc_rules, rule_file, roads_veloc, streams_veloc

# Import functions that setup the environmental variables
import environ_variables as envi

# Set environmental variables
envi.setup_environmental_variables() 

# Import the GRASS GIS Python API libraries

# Import libraries needed to launch GRASS GIS in the jupyter notebook
import grass.script.setup as gsetup
# Import libraries needed to call GRASS using Python
import grass.script as gscript
import grass.script.core

# Import other local libraries

# Import functions that check existence and create GRASS GIS database folder if needed
from grass_database import check_gisdb, check_location, check_mapset, working_mapset

# Import functions for processing time information
from processing_time import start_processing, print_processing_time

# Import function that clips multiple raster according to extention of a vector layer
from clip_multiple_raster import clip_multiple_raster

# Import function that checks and create folder
from mkdir import check_create_dir

# Import functions for handling json input
from import_json import get_groupsets, get_groups, get_units, create_pointmap

# Import function that checks if GRASS GIS add-on is installed and install it if needed
from gextension import check_install_addon

# BEGINNING OF CODE

# Create list for storing name of intermediates layers
TMP_rast = []
TMP_vect = []

# Create temporary directory to hold all temporary files that will be erased at
# the end
check_create_dir(config_parameters['workingdir'])

# Create directory to hold final outputs
check_create_dir(config_parameters['outputdir'])

# # Preprocessing

# Create a GRASSDATA, create a location in WGS84 (lat/long) and start working in that location

gisrc = gscript.setup.init(config_parameters['GISBASE'],
                           config_parameters["gisdb"],
                           "Worldpop_transform", config_parameters['mapset'])

# Check if the GRASS GIS database exists and create it if not
check_gisdb(config_parameters["gisdb"])
# Check if the location exists and create it if not, with the CRS defined by the epsg code 
check_location(config_parameters["gisdb"],"Worldpop_transform","4326")
# Change the current working GRASS GIS session mapset
working_mapset(config_parameters["gisdb"],"Worldpop_transform",config_parameters['mapset'])

# Make sure that all the input datasets are in WGS84

# WOCBA

# Import raster
gscript.run_command('r.in.gdal', overwrite=True, input=data['WOCBA_PPP'][1], output=data['WOCBA_PPP'][0])

# Define region based on this layer
gscript.run_command('g.region', flags='s', raster=data['WOCBA_PPP'][0])

# Compute density - Population per hectare (pph)
formula = "%s=%s/(area()/10000)" % (data['WOCBA_PPH'],data['WOCBA_PPP'][0])
gscript.mapcalc(formula, overwrite=True)

# POPULATION

# Import raster
gscript.run_command('r.in.gdal', overwrite=True, input=data['POP_PPP'][1], output=data['POP_PPP'][0])

# Define region based on this layer
gscript.run_command('g.region', raster=data['POP_PPP'][0])

# Compute density - Population per hectare (pph)
formula = "%s=%s/(area()/10000)" % (data['POP_PPH'],data['POP_PPP'][0])
gscript.mapcalc(formula, overwrite=True)

# HEALTH CENTERS

# Import points directly from the json files
groupsets = get_groupsets(data['GROUPSETS'])
groups = get_groups(data['GROUPS'])
units = get_units(data['HC'][1])
temppointmap = gscript.tempname(20)
create_pointmap(units, groups, groupsets, temppointmap, overwrite=True)

# Check if points fall outside of current computational region.
# If yes, emit a warning
gscript.run_command('g.region', flags='d')

tempregion = gscript.tempname(20)
gscript.run_command('v.in.region',
                    output=tempregion,
                    quiet=True)

error_map = gscript.tempname(20)

gscript.run_command('v.select',
                    ain=temppointmap,
                    bin_=tempregion,
                    output=data['HC'][0],
                    operator='within',
                    quiet=True)

topoinfo_tempmap = gscript.vector_info_topo(temppointmap)
topoinfo_finalmap = gscript.vector_info_topo(data['HC'][0])


# Check if some points fall outside the working region
if topoinfo_tempmap['points'] != topoinfo_finalmap['points']:

    # Get points that fall outside
    gscript.run_command('v.select',
                        ain=temppointmap,
                        bin_=tempregion,
                        output=error_map,
                        operator='within',
                        flags='r',
                        quiet=True)
    topoinfo = gscript.vector_info_topo(error_map)

    error_file_name = data['HC'][0] + '_errors.csv'
    error_file = os.path.join(config_parameters['outputdir'], error_file_name)
    
    warning_message = '%s points are outside the working region, please check !\n' % topoinfo['points']
    warning_message += 'Only those points falling into the working region will be considered.\n'
    warning_message += 'The working region is determined by the WOCBA input file.\n'
    warning_message += 'The offending points have been saved in the file %s' % error_file_name
    warning_message += ' in the output directory.\n'
    gscript.warning(warning_message)

    gscript.run_command('v.db.select',
                        map_=temppointmap,
                        separator='comma',
                        file_=error_file,
                        overwrite=True,
                        quiet=True)
    gscript.run_command('g.remove',
                        type_='vector',
                        name=error_map,
                        flags='f',
                        quiet=True)

gscript.run_command('g.remove',
                    type_='vector',
                    name=[tempregion,temppointmap],
                    flags='f',
                    quiet=True)

# Determine health center hierarchical level
gscript.run_command('v.db.addcolumn',
                    map_=data['HC'][0],
                    column='level integer',
                    quiet=True)

for hc_level, rule in hc_rules.iteritems():
    gscript.run_command('v.db.update',
                        map_=data['HC'][0],
                        column='level',
                        value=hc_level,
                        where=rule,
                        quiet=True)


# **LULC**


# Import raster
gscript.run_command('g.region', flags='d')
gscript.run_command('r.in.gdal', flags='r', overwrite=True, input=data['LULC'][1], output=data['LULC'][0])

# **ROADS**

# For OSM roads, in a future version, the roads could be imported directly from the OSM database. Here, they were downloaded in QGIS with Quick OSM.

if data['ROADS'][0] <> "OSM":
    # Import vector with roads (not osm)
    gscript.run_command('v.in.ogr', overwrite=True, input=data['ROADS'][1], output=data['ROADS'][0])
else:
    # Import vector with OSM roads
    tmp_layer = gscript.tempname(20) # Create a name for temporary layer
    gscript.run_command('v.in.ogr', overwrite=True, input=data['ROADS'][1], output=tmp_layer)
    # Extract features of interest from OSM data
    where_condition = "highway IN ('motorway','motorway_link','primary','primary_link','road','secondary','secondary_link','tertiary','tertiary_link','trunk','trunk_link')"
    gscript.run_command('v.extract', overwrite=True, input=tmp_layer, where=where_condition, output=data['ROADS'][0])
    # Remove temporary layer
    gscript.run_command('g.remove', flags='f', type='vector', name=tmp_layer)

# **ADMINISTRATIVE UNITS**

# Import administrative units
gscript.run_command('v.in.ogr', overwrite=True, input=data['admin'][1], output=data['admin'][0])


# **SRTM (ELEVATION)**

# TODO ?
#In a future version, the SRTM tiles could be imported on the fly and mosaicked to create the elevation layer. 
# r.in.srtm.region should be used for that. This requires creating a login and
# password at https://urs.earthdata.nasa.gov/users/new

#For the moment, this is performed outside the script. Here are the commands used:
#Download the SRTM tiles for the AOI and store them (zip files) in the same directory. Unzip them.
# In a Grass location with SRS 4326 (WGS84), import all the SRTM .hgt files (tiles) that cover the AOI. Source type: Directory. Source input: SRTMHGT. File Format Extension: hgt
#r.import input=E:\Sabine\my_shedecides_datasets\senegal\Data\Elevation\N12W012.hgt output=N12W012
#Print a list containing the name of the files that will be used to define the region. 
#g.list type=raster mapset=PERMANENT

#Copy-paste it to a text editor and replace the paragraph mark with a comma.
#Copy-paste the file list into g.region to define the computational region (Option: set region to match raster map(s))
#g.region raster=N13W015,N13W016,N13W017,N14W012,N14W013,N14W014,N14W015,N14W016,N14W017,N14W018,N15W012,N15W013,N15W014,N15W015,N15W016,N15W017,N15W018,N16W012,N16W013,N16W014,N16W015,N16W016,N16W017
#Copy-paste the list into r.patch to mosaic all the SRTM tiles.
#r.patch input=N12W012,N12W013,N12W014,N12W015,N12W016,N12W017,N13W012,N13W013,N13W014,N13W015,N13W016,N13W017,N14W012,N14W013,N14W014,N14W015,N14W016,N14W017,N14W018,N15W012,N15W013,N15W014,N15W015,N15W016,N15W017,N15W018,N16W012,N16W013,N16W014,N16W015,N16W016,N16W017 output=senegal_srtm_4326

# Import SRTM elevation raster
gscript.run_command('r.in.gdal', overwrite=True, input=data['SRTM'][1], output=data['SRTM'][0])

# **STREAMS**
# Import TCI raster (this was replaced with the extraction of the stream network with r.stream.extract)
#gscript.run_command('r.in.gdal', overwrite=True, input=data['TCI'][1], output=data['TCI'][0])



# Extract the stream network using the elevation layer, enlarge the streams and recode them to 1
tmp_layer1 = gscript.tempname(20) # Create a name for temporary layer
tmp_layer2 = gscript.tempname(20) # Create a name for temporary layer
gscript.run_command('r.stream.extract', overwrite=True, elevation=data['SRTM'][0], threshold=1000, stream_length=10, memory=config_parameters['memory'], stream_raster=tmp_layer1)
gscript.run_command('r.grow', overwrite=True, input=tmp_layer1, new=1, output=tmp_layer2)
gscript.run_command('r.recode', overwrite=True, input=tmp_layer2, output=data['STREAMS'], rules=rule_file['Recode_streams'])
gscript.run_command('g.remove', flags='f', type='raster', name=','.join([tmp_layer1,tmp_layer2])) # Delete temporary layers




# # Processing : Computation of accessibility to health centers

# ## Launch GRASS GIS session

# **Create a location in a projected system (UTM or other) and start working in that location**

# In GRASS GIS, original data are usually imported and stored in the config_parameters['mapset'] mapset (automatically created when creating a new location).


# Check if the GRASS GIS database exists and create it if not
check_gisdb(config_parameters["gisdb"])
# Check if the location exists and create it if not, with the CRS defined by the epsg code 
check_location(config_parameters["gisdb"], config_parameters['location'], config_parameters["locationepsg"])
# Change the current working GRASS GIS session mapset
working_mapset(config_parameters["gisdb"], config_parameters['location'], config_parameters['mapset'])


# # Import data / Preparation of data


# Saving current time for processing time management
begintime_importdata=start_processing()


# ## Administrative units

# Reproject layer from location in WGS84
gscript.run_command('v.proj', overwrite=True, location="Worldpop_transform",
                    input=data['admin'][0], output="Study_area")


# Define computational region based on the Study_area vector layer
gscript.run_command('g.region', vector="Study_area",
        res=config_parameters['resolution'], flags='a')


# **WOCBA**


# Reproject layer from location in WGS84
gscript.run_command('r.proj', overwrite=True, location="Worldpop_transform", method='bicubic',
                    input=data['WOCBA_PPH'], output=data['WOCBA_PPH'],
                    resolution=config_parameters['resolution'])

# Save default computational region (CR) based on the WOCBA
gscript.run_command('g.region', flags='s', raster=data['WOCBA_PPH'])

# Compute Population per pixel (ppp) by multiplying population per ha by number
# of ha in a pixel
formula = "%s=(%s * area()/10000)" % (data['WOCBA_PPP'][0], data['WOCBA_PPH'])
gscript.mapcalc(formula, overwrite=True)

# Remove pph raster
gscript.run_command('g.remove', flags='f', type='raster', name=data['WOCBA_PPH'])


# **POPULATION**

# Reproject layer from location in WGS84
gscript.run_command('r.proj', overwrite=True, location="Worldpop_transform", method='bicubic',
                    input=data['POP_PPH'], output=data['POP_PPH'],
                    resolution=config_parameters['resolution'])

# Save default computational region (CR) based on the WOCBA
gscript.run_command('g.region', raster=data['POP_PPH'])

# Compute Population per pixel (ppp)
formula = "%s= (%s * area()/10000)" % (data['POP_PPP'][0], data['POP_PPH'])
gscript.mapcalc(formula, overwrite=True)

# Remove pph raster
gscript.run_command('g.remove', flags='f', type='raster', name=data['POP_PPH'])


# **LULC**

# Reproject layer from location in WGS84
gscript.run_command('r.proj', overwrite=True, location="Worldpop_transform", method='nearest',
                    input=data['LULC'][0], output=data['LULC'][0],
                    resolution=config_parameters['resolution'])
TMP_rast.append(data['LULC'][0])


# **ELEVATION**

# Reproject layer from location in WGS84
gscript.run_command('r.proj', overwrite=True, location="Worldpop_transform", method='bicubic',
                    input=data['SRTM'][0], output=data['SRTM'][0],
                    resolution=config_parameters['resolution'])
TMP_rast.append(data['SRTM'][0])


# **STREAMS**

# Reproject layer from location in WGS84
gscript.run_command('r.proj', overwrite=True, location="Worldpop_transform", method='nearest',
                    input=data['STREAMS'], output=data['STREAMS'],
                    resolution=config_parameters['resolution'])
TMP_rast.append(data['STREAMS']) 


# ## Import vector layer (roads) and clip to the extent of the study area

# Install required add-on if not yet installed
check_install_addon("v.clip")

# **ROADS**

# Create a name for temporary layer
tmp_layer = gscript.tempname(20)
# Reproject layer from location in WGS84
gscript.run_command('v.proj', overwrite=True, location="Worldpop_transform",
                    input=data['ROADS'][0], output=tmp_layer)

# Clip vector layer
gscript.run_command('v.clip', overwrite=True, input=tmp_layer, clip="Study_area", output=data['ROADS'][0])
TMP_vect.append(data['ROADS'][0])
# Remove temporary layer
gscript.run_command('g.remove', flags='f', type='vector', name=tmp_layer)


# ## Clip rasters to AOI

# Please notice that WOCBA is used as a reference for the following steps (spatial extent and pixel alignement).

# Install required add-on if not yet installed
check_install_addon("r.clip")

# Define the list with names of raster layers to clip
raster_to_clip = [data['WOCBA_PPP'][0],data['POP_PPP'][0],data['LULC'][0],data['SRTM'][0],data['STREAMS']]
print "\n".join(raster_to_clip)

# Define computational region based default region
gscript.run_command('g.region', flags='d')
# Define MASK and get a copy
gscript.run_command('r.mask', overwrite=True, vector='Study_area')
gscript.run_command('g.copy', overwrite=True, raster='MASK,Study_area')
# Clip multiple rasters
clip_multiple_raster(raster_to_clip, overwrite=True, resample=True, n_jobs=config_parameters['njobs'])
# Rename raster to overwrite the original one
[gscript.run_command('g.rename', overwrite=True, raster='%s_clip,%s' % (name,name)) for name in raster_to_clip]
# Remove MASK
gscript.run_command('r.mask', flags='r')

# Define computational region
gscript.run_command('g.region', raster=raster_to_clip[0])
# Define MASK and get a copy
gscript.run_command('r.mask', overwrite=True, vector='Study_area')
gscript.run_command('g.copy', overwrite=True, raster='MASK,Study_area')

for rast in raster_to_clip:
    gscript.run_command('r.clip', flags='r', overwrite=True, input=rast, output='%s_clip'%rast)  # With resampling

# Rename raster to overwrite the original one
[gscript.run_command('g.rename', overwrite=True, raster='%s_clip,%s' % (name,name)) for name in raster_to_clip]
# Remove MASK
gscript.run_command('r.mask', flags='r')


# ## Health facilities (HC)

# Create a name for temporary layer
tmp_layer = gscript.tempname(20)
# Reproject layer from location in WGS84
gscript.run_command('v.proj', overwrite=True, location="Worldpop_transform", input=data['HC'][0], output=tmp_layer)

# Select point into study area (create new layer)
gscript.run_command('v.select', overwrite=True, ainput=tmp_layer, binput="Study_area", output=data['HC'][0], operator="within")
TMP_vect.append(data['HC'][0])

# Remove temporary layer
gscript.run_command('g.remove', flags='f', type='vector', name=tmp_layer)

# Create two new sub-layer based on level of HC (HCL1 ; HCL2)
for hc_level in hc_rules.keys():
    gscript.run_command('v.extract',
                        overwrite=True,
                        input=data['HC'][0],
                        where="level=%s" % str(hc_level),
                        output='%sL%s' % (data['HC'][0], str(hc_level)))

# Rename HC layer that contain both levels
gscript.run_command('g.rename', overwrite=True, vector="%s,%sall" % (data['HC'][0],data['HC'][0]))


# ## Convert roads into raster

# Define computational region based default region
gscript.run_command('g.region', flags='d')
# Rasterize roads layer
gscript.run_command('v.to.rast', overwrite=True, input=data['ROADS'][0], output=data['ROADS'][0], use='val')


# ## Reclassify LULC




for season in ("WS","DS"):
    # Create a name for temporary layer
    tmp_layer = gscript.tempname(20) 
    # Define computational region based default region
    gscript.run_command('g.region', flags='d')
    # Reclassify raster
    gscript.run_command('r.reclass', overwrite=True, input=data['LULC'][0], 
                        output=tmp_layer, rules=rule_file['ESACCI_%s'%season])
    # Create hard copy of the reclassified raster
    formula = "%s_%s=%s" % (data['LULC'][0],season,tmp_layer)
    gscript.mapcalc(formula, overwrite=True)
    TMP_rast.append(tmp_layer)


## Print processing time
print_processing_time(begintime_importdata ,"Data imported in ")


# # Methodology

# Saving current time for processing time management
begintime_processing=start_processing()

# ## Create velocity rasters

# **LULC**


# Create velocity raster
for season in ("WS","DS"):
    # Define computational region based default region
    gscript.run_command('g.region', flags='d')
    # Reclassify raster
    gscript.run_command('r.recode', overwrite=True, input="%s_%s" % (data['LULC'][0],season), 
                        output="velocity_%s_%s" % (data['LULC'][0],season), 
                        rules=rule_file['Velocity_LULC'])


# **ROADS**

# Create velocity raster 
for car in ("WC","NC"):
    # Define computational region based default region
    gscript.run_command('g.region', flags='d')
    # Create velocity raster
    formula = "velocity_%s_%s = if(%s==1,%s,null())" % (data['ROADS'][0],car,data['ROADS'][0],roads_veloc[car])
    gscript.mapcalc(formula, overwrite=True)


# **STREAMS**

# Create velocity raster 
# Define computational region based default region
gscript.run_command('g.region', flags='d')
# Create velocity raster
formula = "velocity_%s = if(%s==1,%s,null())" % (data['STREAMS'],data['STREAMS'],streams_veloc["WS"])
gscript.mapcalc(formula, overwrite=True)

# ## Combine three rasters of velocity together

# Create a list for saving layer name
veloc_raster = []

# Create all possible combinations
for season in ("WS","DS"):
    for car in ("WC","NC"):
        # Define computational region based default region
        gscript.run_command('g.region', flags='d')
        # Create velocity raster
        veloc_LULC = "velocity_%s_%s" % (data['LULC'][0],season)
        veloc_ROADS = "velocity_%s_%s" % (data['ROADS'][0],car)
        veloc_STREAMS = "velocity_%s"%data['STREAMS']
        veloc_combined = "velocity_%s_%s" % (car,season)
        if season == "WS":
            #For the wet season only, streams layer is also used in the final velocity map.
            formula = "{combi}=if(isnull({vel_roads}),if({lulc}!=210,if(isnull({vel_streams}),{vel_lulc},{vel_streams}),{vel_lulc}),{vel_roads})".format(combi=veloc_combined,vel_roads=veloc_ROADS,lulc=data['LULC'][0],vel_lulc=veloc_LULC,vel_streams=veloc_STREAMS)
        else:
            #For the dry season, streams layer is not used.
            formula = "{combi}=if(isnull({vel_roads}),{vel_lulc},{vel_roads})".format(combi=veloc_combined,vel_roads=veloc_ROADS,vel_lulc=veloc_LULC)
        gscript.mapcalc(formula, overwrite=True)
        # Add the combined veloc in list of velocity rasters
        veloc_raster.append(veloc_combined)
        # Add individual velocity layers in list of temp files
        TMP_rast.append(veloc_LULC)
        TMP_rast.append(veloc_ROADS)    
        TMP_rast.append(veloc_STREAMS)
        TMP_rast.append(veloc_combined)


# ## Calculate cost distance raster

# The computation of cost distance raster is performed here using [r.cost](https://grass.osgeo.org/grass76/manuals/r.cost.html). For NO CAR scenarios, [r.walk](https://grass.osgeo.org/grass76/manuals/r.walk.html) is used as it takes into account the cost of moving uphill and downhill. 

# Possible improvement: parallelize the loops


# Create a list for saving layer name
cost_raster = []
nearest_raster = []
# Create all cost distance raster
for veloc_rast in veloc_raster:
    for hclevel in ("all","L2"):
        printlist = []
        # Determine the car status
        car = veloc_rast[-5:-3]
        # Define name of the output layers
        output_costlayer = "CostDist_HC%s_%s" % (hclevel,veloc_rast[-5:])
        output_nearestlayer = "Nearest_HC%s_%s" % (hclevel,veloc_rast[-5:])
        # Define computational region based default region
        gscript.run_command('g.region', flags='d')
        # Compute cost distance raster -'k' for Knight's move
        gscript.run_command('r.cost', flags='k', overwrite=True,
                            input=veloc_rast, output=output_costlayer, nearest=output_nearestlayer,
                            start_points="%s%s" % (data['HC'][0],hclevel), memory=config_parameters['memory'])
        # Add to list of output
        cost_raster.append(output_costlayer)
        nearest_raster.append(output_nearestlayer)
        # Add to temp layers
        TMP_rast.append(output_costlayer)
        TMP_rast.append(output_nearestlayer)
        # Add to printlist
        printlist.append(output_costlayer)
        printlist.append(output_nearestlayer)

        print "Layers created: %s"%','.join(printlist)


# Possible improvement: For NO CAR scenarios, use r.walk instead of r.cost, as r.walk takes into account the cost of moving uphill and downhill. The code in the cell below outputs the cost distance with r.walk, but it does not output a cost allocation raster based on the nearest starting point (whereas r.cost does it with 'nearest').
# Create a list for saving layer name
cost_raster = []
nearest_raster = []
# Create all cost distance raster
for veloc_rast in veloc_raster:
    for hclevel in ("all","L2"):
        printlist = []
        # Determine the car status
        car = veloc_rast[-5:-3]
        # Define name of the output layers
        output_costlayer = "CostDist_HC%s_%s" % (hclevel,veloc_rast[-5:])
        output_nearestlayer = "Nearest_HC%s_%s" % (hclevel,veloc_rast[-5:])
        # Define computational region based default region
        gscript.run_command('g.region', flags='d')
        # Compute cost distance raster -'k' for Knight's move
        gscript.run_command('r.cost', flags='k', overwrite=True,
                            input=veloc_rast, output=output_costlayer, nearest=output_nearestlayer,
                            start_points="%s%s" % (data['HC'][0],hclevel), memory=config_parameters['memory'])
        # Add to list of output
        cost_raster.append(output_costlayer)
        nearest_raster.append(output_nearestlayer)
        # Add to temp layers
        TMP_rast.append(output_costlayer)
        TMP_rast.append(output_nearestlayer)
        # Add to printlist
        printlist.append(output_costlayer)
        printlist.append(output_nearestlayer)

# ## Calculate isochrones

# Create a list for saving layer name
isochrone_layers = []

# Create isochrones rasters
for cost_rast in cost_raster:
    # Define name of the output layer
    output_layer = "Isochrones_%s"%cost_rast[9:]
    # Define computational region based default region
    gscript.run_command('g.region', flags='d')
    # Create accessibility raster (time to travel)
    formula_prefix = "%s="%output_layer
    formula_suffix = "null()"
    for time in config_parameters['time_limits']:
        formula_prefix += "if(%s<=%s,%s," % (cost_rast,time,time)
        formula_suffix += ")"
    gscript.mapcalc(formula_prefix+formula_suffix, overwrite=True)
    print "Layer '%s' created."%output_layer
    isochrone_layers.append(output_layer)
    
# Convert the next cell to code for vectorizing isochrones (requested for statistics of pop. per isochrone)
# Convert isochrone rasters to vector layers
for isochrone in isochrone_layers:
    gscript.run_command('g.region', flags='d')
    gscript.run_command('r.to.vect', flags='v', overwrite=True,
                        input=isochrone, output=isochrone, type="area")
# ## Overlay isochrones with population and calculate population statistics (per isochrone)


# Layers to be used for computing statistics (zonal statistics)
layers_stats = ["POP_PPP","WOCBA_PPP"]


# **Get sum for the study area (total population)**

# Initialize a dictionnary for saving total
TOT={}
# Compute sum for the whole study area
for layer in layers_stats:
    TOT["%s"%layer] = float(gscript.parse_command('r.univar', flags='g', map=layer, zones="Study_area")["sum"])
#print "Total population of the study area = %s"%TOT["POP_PPP"]
#print "Total Women of Child-Bearing Age (WOCBA) of the study area = %s"%TOT["WOCBA_PPP"]


# **Get sum for each isochrone and compute proportion**

# Convert the next cell to code for calculating statistics of population per isochrones (requires isochrones in vector format).
# Compute proportions for each isochrone layer
for isochrone in isochrone_layers:
    print "Start working on layer '%s'"%isochrone
    for layer in layers_stats:
        print "        Working with %s"%layer
        # Create temp .csv file
        head, tail = os.path.split(gscript.tempfile())
        table = 'tmp_table_%s'%tail.replace(".","_")
        tmp_csv = os.path.join(head,'%s.csv'%table)
        print "        1"
        # Compute sum for each isochrone zone
        gscript.run_command('r.univar', flags='t', overwrite=True, map=layer, 
                            zones=isochrone, output=tmp_csv, separator="comma")
        print "        2"
        # Import .csv and join
        gscript.run_command('db.in.ogr', overwrite=True, input=tmp_csv, output=table)
        print "        3"
        gscript.run_command('v.db.join', map=isochrone, column='cat', 
                            other_table=table, other_column='zone', subset_columns='sum')
        gscript.run_command('v.db.renamecolumn', map=isochrone, column='sum,%s_SUM'%layer)
        print "        4"
        # Add TOTAL count
        gscript.run_command('v.db.addcolumn', map=isochrone, columns='%s_TOT double precision'%layer)
        gscript.run_command('v.db.update', map=isochrone, column='%s_TOT'%layer, value=TOT["%s"%layer])
        print "        5"
        # Compute proportion
        gscript.run_command('v.db.addcolumn', map=isochrone, columns='%s_PROP double precision'%layer)
        gscript.run_command('v.db.update', map=isochrone, column='%s_PROP'%layer, 
                            value='({layer}_SUM/{layer}_TOT)*100'.format(layer=layer))
        print "        6"
    print "Proportion computed for layer '%s'"%isochrone


# # Cross catchment areas with isochrones and calculate population statistics

# Create a list for saving layer names
cross_layers = []

# Cross catchment areas with isochrones
for isochrone in isochrone_layers:
    # Define computational region based default region
    gscript.run_command('g.region', flags='d')  
    # Define name of the output layer
    output_layer = "Cross_%s"%isochrone[11:]
    #Define name of the catchment area layer
    nearest_layer = "Nearest_%s"%isochrone[11:]
    # Cross catchement areas and isochrones
    gscript.run_command('r.cross', overwrite=True, input=(nearest_layer,isochrone), output=output_layer)
    print "Layer '%s' created."%output_layer
    cross_layers.append(output_layer)


# Calculate population statistics per health facility per isochrone


# Create a folder for storing the output
outputdir_stats = os.path.join(config_parameters['workingdir'],"Stats")
# Check and create folder if needed
check_create_dir(outputdir_stats)


# Create a list for saving csv names
catchpop_csv = []
# Calculate catchment population statistics per health facility and per isochrone
for cross in cross_layers:
     for layer in layers_stats:
        # Define name of the output csv
        stats_csv = os.path.join(outputdir_stats,"stats_%s_%s.csv" % (cross,layer))
        gscript.run_command('r.univar', flags='t', overwrite=True, map=layer, zones=cross, output=stats_csv, separator="comma")
        catchpop_csv.append(stats_csv)


# **Pivot and join to the table of health facilities**
# If user needs cumulative figures, please use "GetCatchmentCumulPopByISO"

# Import function from script
from csv_pivotingtable_catchmentpop import GetCatchmentPopByISO, GetCatchmentCumulPopByISO

# Create a list for saving csv names
pivot_csv = []
# Extract the relevant fields and pivot to have one line per health facility
for catchpop in catchpop_csv:
    # Define name of the output csv
    path, ext = os.path.splitext(catchpop)
    pivot = "%s_pivot%s" % (path,ext)
    # Define colum prefix according to file name
    stat_prefix = os.path.split(catchpop)[1].split("_")[-2]
    GetCatchmentPopByISO(catchpop,out_file=pivot,in_sep=',',col_prefix=stat_prefix)
    pivot_csv.append(pivot)



# Create a list for saving HC layers
HC_layers = []
# Join to the table of health facilities
for csv in pivot_csv:
    scenario = "_".join(os.path.split(csv)[1].split("_")[2:-1])
    HC_level = os.path.split(csv)[1].split("_")[2]
    pivot_scenario = "pivot_%s"%scenario
    HC_layers.append(scenario)
    # Copy HC layer corresponding to current scenario
    gscript.run_command('g.copy', overwrite=True, vector='%s,%s' % (HC_level,scenario))
    # Join with health facility csv
    gscript.run_command('db.in.ogr', overwrite=True, input=csv, output=pivot_scenario)
    # Join both tables
    gscript.run_command('v.db.join', map=scenario, column='cat', other_table=pivot_scenario, other_column='HF_cat')
    # Drop column
    gscript.run_command('v.db.dropcolumn', map=scenario, columns='HF_cat')


# # Export and clean mapset

# **Export output to csv**

if outputs['csv_per_healthfacility']:
    # Create a folder for storing the csv files, ie. the population per health facility per isochrone
    outputdir_final = os.path.join(config_parameters['outputdir'],"Pop_per_health_facility")
    # Check and create folder if needed
    check_create_dir(outputdir_final)
    for layer in HC_layers:
        output_csv = os.path.join(outputdir_final,"%s.csv" % layer)
        gscript.run_command('v.db.select', overwrite=True, map=layer, separator="comma", file=output_csv)

if outputs['isochrone_maps']:
    # Output the isochrone maps
    # # Create a folder for storing the csv files, ie. the population per isochrone
    outputdir_isochrones = os.path.join(config_parameters['outputdir'],"Isochrone_maps")
    # Check and create folder if needed
    check_create_dir(outputdir_isochrones)# Export isochrone layers as GeoPackage and attribute table as .csv
    for isochrone in isochrone_layers:
        output_gpkg = os.path.join(outputdir_isochrones,"%s.gpkg" % isochrone)
        gscript.run_command('v.out.ogr', flags='m', overwrite=True,
                            input=isochrone, output=output_gpkg, format="GPKG")


## Print processing time
print_processing_time(begintime_processing ,"All processing terminated in ")

# CLEANUP
if not outputs['keep_temporary_files']:
    # Delete the temporary working directory
    import shutil
    shutil.rmtree(config_parameters['workingdir'])
