import sys
import json
import grass.script as grass

def create_pointmap(units, groups, groupsets, pointmapname, overwrite=True):
    """Transform info from json files into a GRASS GIS point map."""
    tempfile = grass.tempfile()
    groupsnotfound = []
    groupsetsnotfound = []
    with open(tempfile, 'w') as fout:
        for unit in units.keys():
            output = []
            output.append(str(unit))
            for v in units[unit]:
                output.append(str(v))
            if unit in groups:
                groupid = groups[unit]['groupid']
                groupname = groups[unit]['groupname'] 
            else:
                # if groupid not in groupsnotfound:
                #     groupsnotfound.append(groupid)
                groupid = ''
                groupname = ''
            output.append(str(groupid))
            output.append(str(groupname))

            if groupid in groupsets:
                groupsetid = groupsets[groupid]['groupsetid']
                groupsetname = groupsets[groupid]['groupsetname']
            else:
                if groupsetid not in groupsetsnotfound:
                    groupsetsnotfound.append(groupsetid)
                groupsetid = ''
                groupsetname = ''
            output.append(str(groupsetid))
            output.append(str(groupsetname))

            output_string = ','.join(output)
            fout.write(output_string)
            fout.write('\n')

    if groupsnotfound:
        warning_message = "Could not find the following groups:\n"
        for group in groupsnotfound:
            warning_message += "%s\n" % group
        grass.warning(warning_message)
    if groupsetsnotfound:
        warning_message = "Could not find the following groupsets:\n"
        for groupset in groupsetsnotfound:
            warning_message += "%s\n" % groupset
        grass.warning(warning_message)

    columns = 'id varchar, x double precision, y double precision, name varchar, shortName varchar, groupid varchar, groupname varchar, groupsetid varchar, groupsetname varchar'
    grass.run_command('v.in.ascii',
                      output=pointmapname,
                      input_=tempfile,
                      x=2,
                      y=3,
                      columns=columns,
                      separator='comma',
                      overwrite=overwrite,
                      quiet=True)

def get_groupsets(json_file):
    """Load groupset info from json file and return as a dictionary."""
    with open(json_file, 'r') as fin:
        datas = json.load(fin)

    groupsets = {}

    for line in datas['organisationUnitGroupSets']:
        if not line['organisationUnitGroups']:
            continue
        for group in line['organisationUnitGroups']:
            groupdict = {}
            groupdict['groupsetid'] = line['id']
            groupdict['groupsetname'] = line['name'].encode('utf-8')
            groupsets[group['id']] = groupdict

    return groupsets

def get_groups(json_file):
    """Load group info from json file and return as a dictionary."""
    with open(json_file, 'r') as fin:
        datas = json.load(fin)

    groups = {}

    for line in datas['organisationUnitGroups']:
        if not line['organisationUnits']:
            continue
            for unit in line['organisationUnits']:
                unitdict = {}
                unitdict['groupid'] = line['id']
                unitdict['groupname'] = line['name'].encode('utf-8')
                groups[unit['id']] = unitdict

    return groups

def get_units(json_file):
    """Load health facility info from json file and return as a list.
    
    We use a list, here, in order to ensure a specific order of the data.
    """
    with open(json_file, 'r') as fin:
        datas = json.load(fin)

    units = {}
    for line in datas['organisationUnits']:
        if 'coordinates' in line and line['featureType'] == 'POINT':
            unitinfo = []
            unitinfo.append(json.loads(line['coordinates'])[0])
            unitinfo.append(json.loads(line['coordinates'])[1])
            unitinfo.append(line['name'].encode('utf-8'))
            unitinfo.append(line['shortName'].encode('utf-8'))
            units[line['id']] = unitinfo

    return units
