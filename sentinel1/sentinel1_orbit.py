#! /usr/bin/env python
###############################################################################
#  scihub_download.py
#
#  Purpose:  Get Sentinel-1 orbits from UNAVCO and format for GMTSAR
#  Author:   Scott Baker
#  Created:  Oct 2015
#
###############################################################################
#  Copyright (c) 2015, Scott Baker
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
###############################################################################
import os
import sys
import datetime
import urllib2
import xml.dom.minidom

BASE_URL = 'https://www.unavco.org/data/imaging/sar/lts1/winsar/s1qc'
SECONDS_SPAN = 200 # S1 orbits are every 10 seconds, so this determines how many orbits will be recorded

if len(sys.argv)<2:
    print "Need to provide the time in ISO 8601 format: YYYYmmddTHHMMSS"
    print "Ideally, you would give the scene center time."
    print "USAGE: sentinel1_orbits.py 20150921T013054"
    exit()

scene_center_time = datetime.datetime.strptime(sys.argv[1],"%Y%m%dT%H%M%S")
start_orb_time = scene_center_time - datetime.timedelta(seconds=SECONDS_SPAN) 
stop_orb_time = scene_center_time + datetime.timedelta(seconds=SECONDS_SPAN) 

##### GET LIST OF FILES AND FIND ONE THAT COVERS THE SCENE #####
orb_file=None
files = urllib2.urlopen(BASE_URL+'/aux_poeorb/').read().splitlines()
xml_resorb = [f.split(">")[2].split("<")[0] for f in files  if "_POEORB_" in f]
for xml_orb in xml_resorb:
    orb_file_dates = os.path.splitext(xml_orb)[0].split('_V')[1].split("_")
    orb_start = datetime.datetime.strptime(orb_file_dates[0], "%Y%m%dT%H%M%S")
    orb_stop = datetime.datetime.strptime(orb_file_dates[1], "%Y%m%dT%H%M%S")
    if (orb_start < scene_center_time) and (orb_stop > scene_center_time):
        print xml_orb,"::",orb_file_dates
        orb_file = BASE_URL+'/aux_poeorb/'+xml_orb.strip()

if not orb_file:
    files = urllib2.urlopen('https://www.unavco.org/data/imaging/sar/lts1/winsar/s1qc/aux_resorb/').read().splitlines()
    xml_resorb = [f.split(">")[2].split("<")[0] for f in files  if "_RESORB_" in f]
    for xml_orb in xml_resorb:
        orb_file_dates = os.path.splitext(xml_orb)[0].split('_V')[1].split("_")
        orb_start = datetime.datetime.strptime(orb_file_dates[0], "%Y%m%dT%H%M%S")
        orb_stop = datetime.datetime.strptime(orb_file_dates[1], "%Y%m%dT%H%M%S")
        if (orb_start < scene_center_time) and (orb_stop > scene_center_time):
            print xml_orb,"::",orb_file_dates
            orb_file = BASE_URL+'/aux_resorb/'+xml_orb.strip()

##### READ AND PARSE THE XML FILE #####
xml_data = urllib2.urlopen(orb_file).read()
dom_page = xml.dom.minidom.parseString(xml_data)
orbits = []
for node in dom_page.getElementsByTagName('OSV'):
    x = float(node.getElementsByTagName('X')[0].firstChild.data)
    y = float(node.getElementsByTagName('Y')[0].firstChild.data)
    z = float(node.getElementsByTagName('Z')[0].firstChild.data)
    vx = float(node.getElementsByTagName('VX')[0].firstChild.data)
    vy = float(node.getElementsByTagName('VY')[0].firstChild.data)
    vz = float(node.getElementsByTagName('VZ')[0].firstChild.data)
    utc = datetime.datetime.strptime(node.getElementsByTagName('UTC')[0].firstChild.data,"UTC=%Y-%m-%dT%H:%M:%S.%f")
    if (utc > start_orb_time) and (utc < stop_orb_time):
        orbits.append('%s %s %s %f %f %f %f %f %f' % (utc.year, utc.strftime('%j'), int(utc.strftime('%H')) * 3600 + int(utc.strftime('%M')) * 60 + int(utc.strftime('%S')), x,y,z,vx,vy,vz))

##### WRITE ORBIT DATA TO FILE #####
first_line = str(len(orbits)) + ' ' + orbits[0][:14] + ' 10\n'
with open(scene_center_time.strftime("%Y%m%d")+".LED",'w') as LED:
    LED.write(first_line)
    for orb in orbits:
        LED.write(orb + '\n')
