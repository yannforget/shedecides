import os
import random, string

# Initialize dictionnaries
config_parameters = {}
outputs = {}
data = {}
hc_rules = {}
rule_file = {}
roads_veloc = {}
streams_veloc = {}

# Define temporary working dir and output dir
workingdirbase = '/tmp/SHE_DECIDES' # directory in which to create the temporary working dir
tempdirname = "".join(random.choice(string.ascii_letters) for _ in range(20))
config_parameters['workingdir'] = os.path.join(workingdirbase, tempdirname)

outputdirbase ='/home/shedecides/data/output'
config_parameters['outputdir'] = os.path.join(outputdirbase, 'SEN')

# Define desired outputs
outputs['csv_per_healthfacility'] = True
outputs['isochrone_maps'] = False

# Should temporary files be kept ?
outputs['keep_temporary_files'] = False

## PARAMETERS DEPENDING ON THE AREA OF INTEREST ##

config_parameters['locationepsg'] = '32628' #  EPSG code for WGS84 UTM ZONE 28N (Senegal)
#config_parameters['locationepsg'] = os.path.join(HOMEDIR, "Data", "rgc_proj4") # Example of custom projection

# DATA INFO
datadir = '/home/shedecides/data/input'
data['admin'] = ('admin1',os.path.join(datadir, 'Admin/gadm36_SEN_0.shp'))
data['WOCBA_PPP'] = ('WOCBA_PPP',os.path.join(datadir, 'Population/ppp_prj_2014_SEN_WOCBA.tif'))
data['POP_PPP'] = ('POP_PPP',os.path.join(datadir, 'Population/ppp_prj_2014_SEN.tif'))
data['WOCBA_PPH'] = 'WOCBA'
data['POP_PPH'] = 'POP'
data['LULC'] = ('LULC',os.path.join(datadir, 'LandCover/esacci.tif'))
data['HC'] = ('HC',os.path.join(datadir, 'Health/metadata_senegal.json'))
data['GROUPS'] = os.path.join(datadir, 'Health/Senegal_Groups.json')
data['GROUPSETS'] = os.path.join(datadir, 'Health/Senegal_Groups_Sets.json')
data['SRTM'] = ('SRTM',os.path.join(datadir, 'Elevation/senegal_srtm_4326.tif'))
data['ROADS'] = ('OSM', os.path.join(datadir, 'Roads/OSM/osm_roads.shp'))
data['STREAMS'] = 'STREAMS'

# RULES CONCERNING THE CLASSIFICATION OF HEALTH FACILITIES
hc_rules[1] = "groupid = 'elD2xyvPUxh'"
hc_rules[2] = "groupid = 'Wx1Z05p1qwW' OR groupid = 'QDZvyQQZZN5'"

## GENERAL PARAMETERS OF THE ANALYSIS ##

# Velocity values on roads, with and without a car
roads_veloc["WC"] = "0.17"
roads_veloc["NC"] = "1.2"

# Velocity values on streams (wet season)
streams_veloc["WS"] = "15.0"
config_parameters['resolution'] = '100' # Resolution of cost surface in meters
config_parameters['time_limits'] = ('30','60','120','240','360','480','9999999')  # time limits for isochrones (in minutes)

# RULES FILES (notably translation from land cover to friction cost)
rule_file['Velocity_LULC'] = os.path.join(datadir, 'Velocity_LULC')
rule_file['ESACCI_WS'] = os.path.join(datadir, 'LandCover/reclass_ESACCI_WS')
rule_file['ESACCI_DS'] = os.path.join(datadir, 'LandCover/reclass_ESACCI_DS')
rule_file['Recode_streams'] = os.path.join(datadir, 'Recode_streams')

# COMPUTATIONAL PARAMETERS
config_parameters['njobs'] = 4 # Adapt according to the number of cores you want to use
config_parameters['memory'] = 8000 # available RAM in MB

# GRASS GIS INSTALLATION INFORMATION

config_parameters['GISBASE'] = '/usr/lib/grass76'
config_parameters['PYTHONLIB'] = '/usr/lib/python2.7'
# The following should only be necessary on MS Windows or for custom GDAL
# installations
#config_parameters['GDAL_DATA'] = ''

# INTERNAL GRASS GIS PARAMETERS (NORMALLY NO NEED TO CHANGE)
config_parameters['gisdb'] = os.path.join(config_parameters['workingdir'], 'GRASSDATA') # path to the GRASSDATA folder
config_parameters['location'] = 'SHEDECIDES'  # name of the location (existing or for a new one)
config_parameters['mapset'] = 'PERMANENT'  # name of the location (existing or for a new one)
