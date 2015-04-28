#! /usr/bin/env python
###############################################################################
#  compare_tdx_plan.py
#
#  Project:  WInSAR TSX Portal
#  Purpose:  Compares tasking orders with the TanDEM-X acquisition plan
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

import sys
import csv
import dateutil.parser
import pytz

if len(sys.argv) < 2:
    print "USAGE: compare_tdx_plan.py EOWEB_ASCII_FILE"
    exit()

acq_timeline = []
with open('TanDEM-X_Acquisition_Timeline_4.6.csv','rU') as csvfile:
    reader = csv.reader(csvfile,dialect='excel')
    next(reader, None)  # skip the headers
    next(reader, None)  # skip the headers
    for row in reader:
        d1 = dateutil.parser.parse(row[0]).astimezone(dateutil.tz.tzutc())
        d2 = dateutil.parser.parse(row[1]).astimezone(dateutil.tz.tzutc()) 
        acq_timeline.append([d1,d2])

### Read acquisition times and compare to the TDX timeline
for row in open(sys.argv[1]).readlines()[1:]:
    tmp = row.split("|")
    acq_start = dateutil.parser.parse(tmp[5]).replace(tzinfo=pytz.UTC) ## This works for the ascii off the search tab
#    acq_start = dateutil.parser.parse(tmp[8]).replace(tzinfo=pytz.UTC)  ## This works for the ascii off the shopping cart tab
    for tdx in acq_timeline:
        if tdx[0] <= acq_start <= tdx[1]:
            print "Conflicting acquisition    %s: %10s - orbit %3s - %s" % (tmp[9],tmp[17],tmp[11],tmp[13])
