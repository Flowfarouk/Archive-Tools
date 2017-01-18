#! /usr/bin/env python

###############################################################################
#  alos2_path_from_orbit.py
#
#  Project:  Archive Tools 
#  Purpose:  Brute force method to determine a formula for ALOS-2 path numbers
#  Author:   Scott Baker, scott@bostechnologies.com
#  Created:  <MONTH> 2017
#
###############################################################################
#  Copyright (C) 2017, Scott Baker
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  Contributors:
#    Scott Baker - UNAVCO, Inc. 
###############################################################################

from __future__ import print_function

"""
Known orbit-path numbers:
1000 - 155
1001 - 169
1003 - 197
"""
for x in range(1,100):
    for y in range(1,100):
        tmp = (x*1000+y)%207
        tmp2 = (x*1001+y)%207
        tmp3 = (x*1003+y)%207
        if tmp == 155 and tmp2==169 and tmp3==197:
            print("Formula for ALOS-2 path number: ({0}*ORBIT+{1}) % 207".format(x,y))
