#! /usr/bin/env python
###############################################################################
#  scihub_opensearch.py
#
#  Purpose:  Search Sentinel-1 on scihub with OpenSearch interface and build db of products
#  Author:   Scott Baker
#  Created:  Mar 2015
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
import glob
import optparse
import urllib
import urllib2
import xml.dom.minidom
import time
import datetime
import dateutil.parser
import threading
import Queue
import sqlite3

from osgeo import ogr

BASE_URL = 'https://scihub.esa.int/dhus'
SERVICE_ACTION = "/search"
USERNAME=''
PASSWORD=''
PARALLEL_DOWNLOAD = 2

def xml2text(element, tag):
    if len(element.getElementsByTagName(tag)) == 1:
        if element.getElementsByTagName(tag)[0].firstChild == None: # is there but is null
                return None
        return element.getElementsByTagName(tag)[0].firstChild.data #things are A-OK
    else:  # none existant
        return None

def find_next_page(dom_page):
    links = dom_page.getElementsByTagName('link')
    next = None
    self = None
    last = None
    for link in links:
        if link.getAttribute('rel') == 'next':
            next = link.getAttribute('href')
        elif link.getAttribute('rel') == 'self':
            self = link.getAttribute('href')
        elif link.getAttribute('rel') == 'last':
            last = link.getAttribute('href')
    if last == self: #we are at the end
        return None
    else:
        return next

def database_connection():
    """Define your database connection here
       This is just using a simple SQLite db for now, but could 
       be replaced by PostgreSQL/PostGIS or something else.
    """
    db_path = 'scihub_archive.db'
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        conn.execute("""CREATE TABLE scihub_scene (status TEXT, platformname TEXT, platformidentifier TEXT, id TEXT UNIQUE, identifier TEXT, missiondatatakeid TEXT, acquisitiontype TEXT, orbitnumber TEXT, relativeorbitnumber TEXT, beginposition TEXT, endposition TEXT, sensoroperationalmode TEXT, swathidentifier TEXT, orbitdirection TEXT, polarisationmode TEXT, slicenumber TEXT, ingestiondate TEXT, producttype TEXT, filename TEXT, format TEXT, size TEXT, footprint )""")
        conn.execute("""CREATE TABLE product_download (id TEXT UNIQUE, filename TEXT, date_download TEXT)""")
    else:
        conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def scihub_opensearch(conn, opener):
    INDEX = 0
    STRIDE = 5000
    scenes=[]
    next_page=1
    if opt_dict['all']:
        #search scihub and get a list of all scenes for all times
        while next_page:
            url = BASE_URL+SERVICE_ACTION+"?q=*&rows=%d&start=%d" % (STRIDE,INDEX)
            print url
            f = opener.open(url)
            unparsed_page = f.read()
            dom_page = xml.dom.minidom.parseString(unparsed_page)
            for node in dom_page.getElementsByTagName('entry'):
                d1 = {s.getAttribute('name'):s.firstChild.data for s in node.getElementsByTagName('str')}
                d2 = {s.getAttribute('name'):s.firstChild.data for s in node.getElementsByTagName('int')}
                d3 = {s.getAttribute('name'):dateutil.parser.parse(s.firstChild.data).astimezone(dateutil.tz.tzutc()) for s in node.getElementsByTagName('date')}
                d1['id'] = node.getElementsByTagName('id')[0].firstChild.data
                d1 = dict(d1,**d2)
                scenes.append(dict(d1,**d3))
            next_page = find_next_page(dom_page)
            INDEX += STRIDE
    else:
        #search scihub and get a list of all scenes ingested in the last 4 days 
        while next_page:
            url = BASE_URL+SERVICE_ACTION+"?q=*+AND+ingestionDate:[NOW-4DAY+TO+NOW]&rows=%d&start=%d" % (STRIDE,INDEX)
            print url
            f = opener.open(url)
            unparsed_page = f.read()
            dom_page = xml.dom.minidom.parseString(unparsed_page)
            for node in dom_page.getElementsByTagName('entry'):
                d1 = {s.getAttribute('name'):s.firstChild.data for s in node.getElementsByTagName('str')}
                d2 = {s.getAttribute('name'):s.firstChild.data for s in node.getElementsByTagName('int')}
                d3 = {s.getAttribute('name'):dateutil.parser.parse(s.firstChild.data).astimezone(dateutil.tz.tzutc()) for s in node.getElementsByTagName('date')}
                d1['id'] = node.getElementsByTagName('id')[0].firstChild.data
                d1 = dict(d1,**d2)
                scenes.append(dict(d1,**d3))
            next_page = find_next_page(dom_page)
            INDEX += STRIDE

    cursor = conn.cursor()
    # Get the list of exisiting scene id
    cursor.execute("SELECT * FROM scihub_scene")
    current_scene = [c['id'] for c in cursor.fetchall()]
    count = 0
    for scene in scenes:
        if not 'swathidentifier' in scene.keys():
            scene['swathidentifier']=scene['identifier'].split("_")[1]
        if not 'producttype' in scene.keys():
            scene['producttype']=scene['identifier'].split("_")[2]
        if scene['id'] not in current_scene:
            cursor.execute("""INSERT INTO scihub_scene (status, platformname, platformidentifier, id, identifier, missiondatatakeid, acquisitiontype, orbitnumber, relativeorbitnumber, beginposition, endposition, sensoroperationalmode, swathidentifier, orbitdirection, polarisationmode, slicenumber, ingestiondate, producttype, filename, format, size, footprint ) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""" , (scene['status'], scene['platformname'], scene['platformidentifier'], scene['id'], scene['identifier'], scene['missiondatatakeid'], scene['acquisitiontype'], scene['orbitnumber'], scene['relativeorbitnumber'], scene['beginposition'], scene['endposition'], scene['sensoroperationalmode'], scene['swathidentifier'], scene['orbitdirection'], scene['polarisationmode'], scene['slicenumber'], scene['ingestiondate'], scene['producttype'], scene['filename'], scene['format'], scene['size'], scene['footprint']) )
            conn.commit()
            count += 1
    print "Added %d to archive.db" % count

class ThreadDownload(threading.Thread):
    """Threaded SAR data download"""
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            new, opener, conn = self.queue.get()
            download_scene(new,opener,conn)
            self.queue.task_done()

def download_scene(new,opener,conn):
    url = "https://scihub.esa.int/dhus/odata/v1/Products('%s')/$value" % new['id']
    filename = new['identifier']+".zip"
    try:
        f = opener.open(url)
    except:
        print "Problem opening %s" % new
        return
    dl_file_size = int(f.info()['Content-Length'])
    if os.path.exists(filename):
        file_size = os.path.getsize(filename)
        if dl_file_size == file_size:
            print "%s already downloaded" % filename
            f.close()
            return
    print "S1A Download:",filename
    start = time.time()
    CHUNK = 256 * 10240
    with open(filename, 'wb') as fp:
        while True:
            chunk = f.read(CHUNK)
            if not chunk: break
            fp.write(chunk)
    f.close()
    total_time = time.time()-start
    mb_sec = (os.path.getsize(filename)/(1024*1024.0))/total_time
    print "%s download time: %.2f secs (%.2f MB/sec)" %(filename,total_time,mb_sec)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO product_download values ('%s','%s','%s')" % (new['id'],filename,datetime.dateime.now()))
    conn.commit()

def download_new(opener,conn):
    # Get the list of scenes from the archive.db
    cursor = conn.cursor()
    cursor.execute("""select * from scihub_scene where producttype='SLC'""") # get the SLC scenes 
    scenes_slc = cursor.fetchall()
    cursor.execute("""select * from scihub_scene where producttype='RAW' and sensoroperationalmode='SM'""") # get the L0 Stripmap scenes
    scenes_l0 = cursor.fetchall()

    scenes = scenes_l0+scenes_slc
    print "Total on scihub:",len(scenes)

    # Get the list of scenes already downloaded
    cursor.execute("select * from product_download")
    dl_files = [s['filename'] for s in cursor.fetchall()]
#    dl_files = glob.glob("S1*.zip") # if everything is kept in one directory, just use glob 
    print "Total in downloaded: %d " % len(dl_files)

    #specify your area-of-interest for data
    if opt_dict['intersectsWith']:
        wkt = opt_dict['intersectsWith']
    elif os.path.exists('/home/baker/north_america.shp'):
        ## You can make a shapefile that defines the area(s) that you want to download regularly
        na_shp = ogr.Open('/home/baker/north_america.shp')
        lyr = na_shp.GetLayerByName('north_america')
        for feat in lyr:
           geom = feat.GetGeometryRef()
        wkt = str(geom)
    else:
        ## You can also hardwire a WKT here
        ## This one is roughly the US and Caribbean
        wkt = 'POLYGON((-125.33 49.13,-123.83 46.65,-124.19 42.72,-124.01 39.88,-120.23 34.42,-117.68 33.76,-116.63 31.996,-110.03 22.80,-103.62 18.36,-96.59 15.75,-94.30 16.34,-91.05 13.63,-88.33 13.71,-86.04 10.10,-80.68 7.23,-78.22 7.32,-68.11 18.44,-79.89 25.53,-81.47 31.39,-76.20 35.21,-75.41 38.10,-73.82 40.55,-69.96 41.67,-71.10 43.29,-67.32 44.75,-68.73 47.49,-82.26 41.48,-84.02 46.23,-95.10 48.95,-125.33 49.12))' 
    aoi = ogr.CreateGeometryFromWkt(wkt)

    #create a queue for parallel downloading
    queue = Queue.Queue()
    #spawn a pool of threads, and pass them queue instance
    for i in range(PARALLEL_DOWNLOAD):
        t = ThreadDownload(queue)
        t.setDaemon(True)
        t.start()
    #populate queue with data
    count = 0
    newFileList = ''
    for scene in scenes:
        scene_area = ogr.CreateGeometryFromWkt(scene['footprint'])
        if scene['identifier']+'.zip' not in dl_files and scene_area.Intersects(aoi):
            queue.put([scene, opener, conn])
            newFileList += scene['identifier']+'\n'
            count += 1
    print "Total new to download: %d" % count
    queue.join()
 
class MyParser(optparse.OptionParser):
    def format_epilog(self, formatter):
        return self.epilog
    def format_description(self, formatter):
        return self.description

if __name__ == '__main__':
    if len(sys.argv)==1:
        sys.argv.append('-h')
    ### READ IN PARAMETERS FROM THE COMMAND LINE ###
    desc = """Command line client for searching scihub and creating a database 
For questions or comments, contact Scott Baker: baker@unavco.org
    """
    epi = """You will need to add your SciHub USERNAME and PASSWORD in this file (it's near the top). 
A good thing to do will be to run this once and build the initial catalog of scenes:
    scihub_archive.py --opensearch --all

After this, you can set a cron job to run and update this catalog:
    scihub_archive.py --opensearch

The default is to search the last 4 days for new ingested products, so this can be run at least daily

Other Example:
scihub_archive.py --download
scihub_archive.py --opensearch
scihub_archive.py --opensearch --download

scihub_archive.py --download --intersectsWith='POINT(-155.3 19.4)'
"""
    parser = MyParser(description=desc, epilog=epi, version='1.0')
    querygroup = optparse.OptionGroup(parser, "Parameters", "These options are used to control what is done")

    querygroup.add_option('-o','--opensearch', action="store_true", default=False, help='Search scihub with opensearch and create archive.db')
    querygroup.add_option('-a','--all', action="store_true", default=False, help='Search everything at scihub')
    querygroup.add_option('-d','--download', action="store_true", default=False, help='Download new scenes')
    querygroup.add_option('-i','--intersectsWith', action="store", dest="intersectsWith", metavar='<ARG>', default='',help='WKT format POINT,LINE, or POLYGON')
    parser.add_option_group(querygroup)
    opts, remainder = parser.parse_args(sys.argv[1:])
    opt_dict= vars(opts)

    #open a connection to the scihub
    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, BASE_URL, USERNAME,PASSWORD)
    authhandler = urllib2.HTTPBasicAuthHandler(passman)
    opener = urllib2.build_opener(authhandler)

    conn = database_connection()
    if opt_dict['opensearch']: 
        scihub_opensearch(conn,opener)
    if opt_dict['download']:
        download_new(opener,conn)
    

