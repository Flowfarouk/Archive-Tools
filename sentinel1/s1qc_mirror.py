#! /usr/bin/env python
###############################################################################
#  s1qc_mirror.py
#
#  Project:  Archive-Tools
#  Purpose:  Mirror the Sentinel-1 orbit data from ESA 
#  Author:   Scott Baker
#  Created:  Feb 2015
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
import glob
import re
import ssl
try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python2
    from urllib2 import urlopen

ORBITS_DIR = '/Users/baker/data/s1qc' # THIS IS THE DIRECTORY TO MIRROR THE ORBITS

s1qc_files = [os.path.basename(f) for f in glob.glob("*/S1*")]
urls = ['https://qc.sentinel1.eo.esa.int/aux_cal','https://qc.sentinel1.eo.esa.int/aux_ins','https://qc.sentinel1.eo.esa.int/aux_poeorb','https://qc.sentinel1.eo.esa.int/aux_pp1','https://qc.sentinel1.eo.esa.int/aux_pp2','https://qc.sentinel1.eo.esa.int/aux_resatt','https://qc.sentinel1.eo.esa.int/aux_resorb','https://qc.sentinel1.eo.esa.int/aux_scs','https://qc.sentinel1.eo.esa.int/mpl_orbpre']
gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1) 
for myurl in urls:
    for i in re.findall('''href=["'](.[^"']+)["']''', urlopen(myurl, context=gcontext).read().decode('utf-8'), re.I):
        base_url = myurl.split("?")[0]
        dl_dir = ORBITS_DIR+os.path.basename(base_url)
        if "S1" in i and i not in s1qc_files:
             os.system("wget --no-check-certificate -c --directory-prefix=%s %s/%s" % (dl_dir, base_url, i))
        elif "page=" in i:
            next_url = "%s/%s" % (myurl, i)
            for i in re.findall('''href=["'](.[^"']+)["']''', urlopen(next_url, context=gcontext).read().decode('utf-8'), re.I):
                if "S1" in i and i not in s1qc_files:
                    os.system("wget --no-check-certificate -c --directory-prefix=%s %s/%s" % (os.path.basename(myurl), myurl, i) )
