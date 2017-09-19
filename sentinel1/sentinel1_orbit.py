#! /usr/bin/env python
###############################################################################
#  sentinel1_orbit.py
#
#  Purpose:  Get Sentinel-1 orbits from ESA PDGS
#  Author:   Scott Baker
#  Created:  Sept 2017
#
###############################################################################
#  Copyright (c) 2017, Scott Baker
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
from __future__ import print_function
import os
import sys
import re
import datetime
import ssl
import argparse
try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)

def parse():
    '''Command line parser.'''
    parser = argparse.ArgumentParser(
        description='Download Sentinel-1 orbit file',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('SCENE_CENTER_TIME', action='store', type=str, help='ISO 8601 format: YYYYmmddTHHMMSS')
    parser.add_argument('-sat', action='store', type=str, default='S1A', help='Satellite: S1A or S1B')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse()
    scene_center_time = datetime.datetime.strptime(args.SCENE_CENTER_TIME,"%Y%m%dT%H%M%S")
    validity_start_time = scene_center_time-datetime.timedelta(days=1)
    orb_type = 'aux_poeorb'
    if (datetime.datetime.now()-scene_center_time).days < 21:
        orb_type = 'aux_resorb'
        validity_start_time = scene_center_time-datetime.timedelta(hours=10)
    ##### FIND THE CORRECT ORBIT FILE #####
    BASE_URL = 'https://qc.sentinel1.eo.esa.int/%s/?validity_start_time=%s' % (orb_type, validity_start_time.strftime("%Y-%m-%d"))
    for i in re.findall('''href=["'](.[^"']+)["']''', urlopen(BASE_URL, context=gcontext).read().decode('utf-8'), re.I):
        if '.EOF' in i and args.sat in i:
            orbit_file_url = "%s/%s" % (BASE_URL.split("?")[0], i)
            orbit_file = os.path.basename(orbit_file_url)
            orb_file_dates = os.path.splitext(orbit_file)[0].split('_V')[1].split("_")
            orb_start = datetime.datetime.strptime(orb_file_dates[0], "%Y%m%dT%H%M%S")
            orb_stop = datetime.datetime.strptime(orb_file_dates[1], "%Y%m%dT%H%M%S")
            if not os.path.exists(orbit_file) and (orb_start < scene_center_time) and (orb_stop > scene_center_time):
                os.system("wget --no-check-certificate -c %s" % orbit_file_url)
                exit() # only download 1 orbit file, this is relevant for RESORB

