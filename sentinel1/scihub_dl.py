#! /usr/bin/env python
###############################################################################
#  scihub_download.py
#
#  Purpose:  Command line download from SciHub
#  Author:   Scott Baker
#  Created:  Jan 2015
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
import urllib
import urllib2
import time
import re

BASE_URL = 'https://scihub.copernicus.eu/apihub'
USERNAME='' # hardwire your SciHub username here 
PASSWORD='' # hardwire your SciHub password here 

passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
passman.add_password(None, BASE_URL, USERNAME, PASSWORD) 
authhandler = urllib2.HTTPBasicAuthHandler(passman)
opener = urllib2.build_opener(authhandler)

### EXAMPLE URL FOR DATA PRODUCT: https://scihub.esa.int/dhus/odata/v1/Products('87c36024-4c38-43d8-b21a-d60bb9fe3eba')/$value
url = BASE_URL+"/odata/v1/Products('%s')/$value" % sys.argv[1] # this is the product id from scihub
f = opener.open(url)
dl_file_size = int(f.info()['Content-Length'])
filename = f.info()['Content-Disposition'].split("=")[-1].strip().replace('"','') # the filename has quotes, so remove from the string
if os.path.exists(filename):
    file_size = os.path.getsize(filename)
    if dl_file_size == file_size:
        print "%s already downloaded" % filename
        f.close()
        exit()
print "S1A Download:",filename
start = time.time()
CHUNK = 256 * 10240 # Read data as 2MB chunks
with open(filename, 'wb') as fp:
    while True:
        chunk = f.read(CHUNK)
        if not chunk: break
        fp.write(chunk)
f.close()
total_time = time.time()-start
mb_sec = (os.path.getsize(filename)/(1024*1024.0))/total_time
print "%s download time: %.2f secs (%.2f MB/sec)" %(filename,total_time,mb_sec)
