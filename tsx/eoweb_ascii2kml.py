#! /usr/bin/env python
###############################################################################
#  eoweb_ascii2kml.py
#
#  Project:  WInSAR TSX Portal
#  Purpose:  Create KML of EOWEB search exported as ASCII text
#  Author:   Scott Baker
#  Created:  January 2015
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
import re
import csv
import itertools
import operator

if len(sys.argv) < 2:
    print "USAGE: eoweb_ascii2kml.py EOWEB_ASCII_FILE"
    exit()

tsxTasking = csv.DictReader(open(sys.argv[1]), delimiter='|')
"""
Id|Avail.|Transfer|Abstract|Item Type|Start Date|End Date|Mission/Satellite|Sensor/Instrument|Sensor Mode|Polarization Mode|Start Orbit|Stop Orbit|Beam|Full Perf. Min. Inc. Angle|Full Perf. Max. Inc. Angle|Incidence Angle Variation|Pass Direction|Looking Direction|Start Phase|Start Cycle|Start Cycle Seconds|Start Orbit Seconds|Stop Phase|Stop Cycle|Stop Cycle Seconds|Stop Orbit Seconds|PN Type|Antenna Receive Configuration|Microseconds|System Order Identification|System Order Path|Costs(Prio1)|Costs(Prio2)|Costs(Prio3)|Costs(Prio4)|Costs(Prio5)|Costs(Prio6)|Costs(Prio7)|Costs(Prio8)|Costs(Prio9)|Costs(Prio10)|ItemDescriptorIdentifier|FOOTPRINT|ACQUISITIONDESCRIPTOR|Display
"""
kmlFile = os.path.splitext(os.path.basename(sys.argv[1]))[0]+'.kml'
data = [row for row in tsxTasking]
#print data[0]
#exit()
with open(kmlFile, 'w') as KML:
    KML.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    KML.write('<kml xmlns="http://www.google.com/earth/kml/2">\n')
    KML.write('<Document><name>TerraSAR-X SAR DATA</name>\n')
    trackgroups = []
    for key, items in itertools.groupby(sorted(data, key=operator.itemgetter('Start Orbit')), operator.itemgetter('Start Orbit')):
        trackgroups.append(list(items))
    for tg in trackgroups:
        track = tg[0]['Start Orbit']
        KML.write('<Folder><name>Orbit ' + str(track) + ' (' + str(len(tg)) + ')</name>\n')
        ### GROUP TRACKS INTO BEAM/SWATH ###
        tmp = []
        for key, items in itertools.groupby(sorted(tg, key=operator.itemgetter('Beam')), operator.itemgetter('Beam')):
            tmp.append(list(items))
        for sg in tmp:
            swath = sg[0]['Beam']
            KML.write('<Folder><name>' + swath + ' (' + str(len(sg)) + ')</name>\n')
            for d in sorted(sg):
                fp = re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", d['FOOTPRINT'])
                lats = [t for t in map(lambda i: float(fp[i]), filter(lambda i: i % 2 == 0, range(len(fp))))]
                lons = [t for t in map(lambda i: float(fp[i]), filter(lambda i: i % 2 == 1, range(len(fp))))] 
                KML.write('<Placemark><name>Track: '+ d['Start Orbit'] + ' ' + d['Sensor Mode'] + ' ' + d['Beam'] + '</name>\n')
                KML.write('<Style id="redLine"><LineStyle><color>7f0000ff</color><width>4</width></LineStyle><PolyStyle><color>7fffffff</color></PolyStyle></Style>\n')
                KML.write('  <description><![CDATA[')
                for k,v in sorted(d.iteritems()):
                    KML.write('<br>%s: %s' % (k,v))
                KML.write('  ]]></description>\n')
                KML.write('  <LineString><tessellate>1</tessellate><coordinates> ')
                for ni in range(len(lats)):
                    KML.write(str(lons[ni]).strip() + ',' + str(lats[ni]).strip() + ',0 ')
                KML.write('  </coordinates></LineString>\n</Placemark>\n')
                print "#####################################################"
                print "Rel Orbit: %s BeamMode: %s BeamSwath: %s" % (d['Start Orbit'],d['Sensor Mode'],d['Beam'])
                print "Footprint: %s" % ("POLYGON ((" + ",".join([str(lon)+' '+str(lat) for lat,lon in zip(lats,lons)]) + "))")
            KML.write('</Folder>\n')
        KML.write('</Folder>\n')
    KML.write('</Document></kml>')


