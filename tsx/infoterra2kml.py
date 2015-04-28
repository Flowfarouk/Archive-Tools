#! /usr/bin/env python
###############################################################################
#  infoterra2kml.py
#
#  Project:  
#  Purpose:  Query Infoterra TSX archive using WFS capabilities
#  Author:   Scott Baker
#  Created:  September 25, 2012
#
###############################################################################
#  Copyright (c) 2012, Scott Baker 
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

import sys
import time
import datetime
import urllib2
import urllib
import json
import operator
import itertools

def main(argv):
    tmp = 'intersects(the_geom,%s)' % argv[0]
    filter = urllib.quote_plus(tmp)
    url = 'http://infoterra.de/geoserver/onlinearchivewfs/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=cat0:cat0&maxFeatures=100000&outputFormat=json&r=22514&cql_filter=%s' % filter 
    f = urllib2.urlopen(url)
    start = time.time()
    json_data = f.read()
    print "Total query time: %f" % (time.time()-start)
    try:
        data = json.loads(json_data)
        results = data['features']
    except:
        print json_data
        exit()
    
    data = []
    for r in results:
        props = r['properties']
        props['coords'] = r['geometry']['coordinates']
        data.append(props)
    print "Found %d scenes within your AOI" % len(data)
    
    beamModes = []
    for key, items in itertools.groupby(sorted(data, key=operator.itemgetter('img_mod')), operator.itemgetter('img_mod')):
        beamModes.append(list(items))
    ### CREATE THE KML ###
    kmlFile = 'infoterra_search_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.kml'
    print "Creating KML file %s" % kmlFile
    with open(kmlFile, 'w') as KML:
        KML.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        KML.write('<kml xmlns="http://www.google.com/earth/kml/2">\n')
        KML.write('<Document><name>UNAVCO TSX Search</name>\n')
        KML.write('<Style id="yellowLine"><LineStyle><color>7f00ffff</color><width>4</width></LineStyle><PolyStyle><color>7fffffff</color></PolyStyle></Style>\n')
        KML.write('<Style id="blueLine"><LineStyle><color>7fff0000</color><width>4</width></LineStyle><PolyStyle><color>7fffffff</color></PolyStyle></Style>\n')
        KML.write('<Style id="purpleLine"><LineStyle><color>7fff00ff</color><width>4</width></LineStyle><PolyStyle><color>7fffffff</color></PolyStyle></Style>\n')
        KML.write('<Style id="greenLine"><LineStyle><color>7f00ff00</color><width>4</width></LineStyle><PolyStyle><color>7fffffff</color></PolyStyle></Style>\n')
        style_dict = {'Wide ScanSAR (WS)':'#yellowLine', 'ScanSAR (SC)':'#yellowLine', 'Stripmap (SM)':'#greenLine', 'Spotlight (SL)':'#blueLine', 'High Resolution Spotlight (HS)':'#purpleLine', 'Staring Spotlight (ST)': '#purpleLine'} 
        for mode in beamModes:
            trackgroups = []
            for key, items in itertools.groupby(sorted(mode, key=operator.itemgetter('rel_orbit')), operator.itemgetter('rel_orbit')):
                trackgroups.append(list(items))
            KML.write('<Folder><name>' + mode[0]['img_mod'] + ' (' + str(len(mode)) + ')</name>\n')
            for tg in trackgroups:
                track = tg[0]['rel_orbit']
                KML.write('<Folder><name>Track ' + str(track) + ' (' + str(len(tg)) + ')</name>\n')
                ### GROUP TRACKS INTO BEAM/SWATH ###
                tmp = []
                for key, items in itertools.groupby(sorted(tg, key=operator.itemgetter('beam_id')), operator.itemgetter('beam_id')):
                    tmp.append(list(items))
                for sg in tmp:
                    swath = sg[0]['beam_id']
                    KML.write('<Folder><name>' + swath + ' (' + str(len(sg)) + ')</name>\n')
                    for d in sorted(sg, key=operator.itemgetter('start_time')):
                        lats = [n[1] for n in d['coords'][0]]
                        lons = [n[0] for n in d['coords'][0]]
                        KML.write('<Placemark><name>' + d['id'] + '</name>\n')
                        KML.write('<styleUrl>' + style_dict[d['img_mod']] + '</styleUrl>\n')
                        KML.write('  <description><![CDATA[')
                        for k,v in sorted(d.iteritems()):
                            if k =='coords':
                                continue
                            KML.write('<br>%-20s%-s' % (k,v))
                        KML.write('  ]]></description>\n')
                        KML.write('  <LineString><tessellate>1</tessellate><coordinates> ')
                        for ni in range(len(lats)):
                            KML.write(str(lons[ni]) + ',' + str(lats[ni]) + ',0 ')
                        KML.write('  </coordinates></LineString>\n</Placemark>\n')
                    KML.write('</Folder>\n') 
                KML.write('</Folder>\n')  
            KML.write('</Folder>\n')
        KML.write('</Document></kml>')

    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print """USAGE:
inforterra2kml.py WKT_GEOM

Examples (Notice: you need to use single or double quotes around WKT):
./infoterra2kml.py 'POLYGON((-120.0061 38.9997, -114.6338 35.0005, -114.6118 32.7385, -117.1057 32.4886, -117.2595 33.1442, -118.2593 33.7492, -118.8196 34.0592, -120.4675 34.5221, -121.8408 36.4188, -123.1262 38.4426, -120.0061 38.9997))'
./infoterra2kml.py 'LINESTRING(-118.5559 34.5945, -117.8967 34.4497, -117.3914 34.3137, -117.2046 34.1229, -116.8311 33.9681, -116.6003 33.9043, -116.1938 33.7857, -115.9000 33.5205, -115.6665 33.3922, -115.4688 33.2085, -115.3479 32.9323)'
./infoterra2kml.py 'POINT(-115.53 32.98)'
"""
        exit()
    main(sys.argv[1:])
    
    


