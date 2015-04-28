#! /usr/bin/env python
###############################################################################
#  download_dlr_ftp.py
#
#  Project:  UNAVCO/WInSAR TerraSAR-X PI Portal 
#  Purpose:  Automated download for DLR orders 
#  Author:   Scott Baker
#  Created:  Nov 2, 2012
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
import os 
import time
import datetime
import sqlite3
import ftplib
from ftplib import FTP_TLS
import collections
FTPDir= collections.namedtuple("FTPDir", "name size mtime tree")
FTPFile= collections.namedtuple("FTPFile", "name size mtime")

class FTPDirectory(object):
    def __init__(self, path='.'):
        self.dirs = []
        self.files = []
        self.path = path

    def getdata(self, ftpobj):
        ftpobj.retrlines('MLSD', self.addline)

    def addline(self, line): 
        data, _, name= line.partition('; ')
        fields= data.split(';')
        for field in fields:
            field_name, _, field_value= field.partition('=')
            if field_name == 'type':
                target = self.dirs if field_value == 'dir' else self.files
            elif field_name in ('sizd', 'size'):
                size = int(field_value)
            elif field_name == 'modify':
                mtime = time.mktime(time.strptime(field_value, "%Y%m%d%H%M%S"))
        try:
            if target is self.files:                
                target.append(FTPFile(name, size, mtime))
            else:
                target.append(FTPDir(name, size, mtime, self.__class__(os.path.join(self.path, name))))
        except:
            pass

    def walk(self):
        for ftpfile in self.files:
            yield self.path, ftpfile
        for ftpdir in self.dirs:
            for path, ftpfile in ftpdir.tree.walk():
                yield path, ftpfile

def get_db_connection(dbPath):
#    print 'Getting connection to %s' % dbPath
    return sqlite3.connect(dbPath)

def get_list(conn):
    conn.row_factory = sqlite3.Row  
    c = conn.cursor()
    c.execute("select * from proposal;")  
    for row in c.fetchall(): 
        fileList = []
        tmp = dict(row)
        proposal_id = tmp['proposal_id']
        print "########################################"  
        print "List of files for proposal %s " % tmp['dlr_proposal_id']
        ftps = ftplib.FTP_TLS('cassiopeia.caf.dlr.de',tmp['dlr_login_username'],tmp['dlr_login_password'])
        ftps.prot_p()
        ftps.voidcmd('TYPE I')
        folder = FTPDirectory()
        folder.getdata(ftps) # get the filenames
        for path, ftpfile in folder.walk():
            fileList.append( { 'proposal_id':proposal_id, 'product_name':ftpfile.name, 'product_size_bytes':ftpfile.size, 'product_mtime':datetime.datetime.fromtimestamp(ftpfile.mtime) } )
        ftps.close()
        for file in fileList:
            print "File: %s, %d, %s " % (file['product_name'],file['product_size_bytes'],file['product_mtime'].strftime('%Y%m%dT%H:%M:%S'))
            try:  
                c.execute('''insert into downloadrequest (proposal_id,product_name,product_mtime,date_requested,product_size_bytes) values (?,?,?,?,?);''', [file['proposal_id'],file['product_name'],file['product_mtime'],datetime.datetime.now(),file['product_size_bytes']] )
            except sqlite3.IntegrityError:
                print "     %s already in database" % file['product_name']  
                next
    conn.commit()
    
def download_new(conn):
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("select * from downloadrequest where product_download_end is null;")  
    print "\n########################################"
    for row in c.fetchall():  
        c.execute('''select * from proposal where proposal_id=%d ;''' % row['proposal_id'] )   
        tmp = c.fetchone()
        ftps = ftplib.FTP_TLS('cassiopeia.caf.dlr.de',tmp['dlr_login_username'],tmp['dlr_login_password'])
        ftps.prot_p()
        ftps.voidcmd('TYPE I')
        filename = row['product_name'] 
        file = open(filename,'wb')
        filesize = ftps.size(filename)
        print 'Downloading ' + filename 
        print 'Total file size: ' + str(filesize/(1024*1024)) + ' MB'
        print 'Total file size: ' + str(filesize) + ' B'
        start_time = datetime.datetime.now()
        ftpconn = ftps.transfercmd('RETR ' + filename)
        bytes_recv = 0
        while 1:
            chunk = ftpconn.recv()
            if bytes_recv >= filesize:
                print '\nDownloaded all ' + str(filesize) + ' bytes'
                break
            elif not chunk:
                print '\nDownloaded ' + str(bytes_recv) + ' bytes'
                break
            file.write(chunk)
            bytes_recv += len(chunk)
        end_time = datetime.datetime.now()
        ftpconn.close()
        file.close() 
        ftps.close()
        c.execute('''update downloadrequest set product_download_start='%s', product_download_end='%s' where product_name='%s' ; ''' % (start_time,end_time,filename) )
        conn.commit()

if __name__ == '__main__':
    dbPath = 'dlr_downloads.db'
    if not os.path.exists(dbPath):
        print """#########################################################
#########################################################
	The %s database does not exist.  Need to create it first and add proposals 
	credentials to it for this to work properly. Here are some steps to get you going.  Run the 
	following from the command line:

sqlite3 %s "CREATE TABLE proposal (proposal_id integer NOT NULL PRIMARY KEY, user_id integer, dlr_proposal_id varchar(10), dlr_login_username varchar(20), dlr_login_password varchar(36))"

sqlite3 %s "CREATE TABLE downloadrequest (id integer NOT NULL PRIMARY KEY, proposal_id integer NOT NULL REFERENCES proposal (proposal_id), product_name varchar(50) NOT NULL UNIQUE, product_mtime datetime, date_requested datetime, product_download_start datetime, product_download_end datetime,product_size_bytes bigint, comments varchar(50))"

sqlite3 %s "INSERT INTO proposal (dlr_proposal_id,dlr_login_username,dlr_login_password) values ('MTH2467','NM_shimonw_MTH2467','YOUR_PASSWORD_HERE')"

	Replace the values in the INSERT statement with your own and be sure to use single quotes for
	the values.  After that, you should be able to run the command and it will get a listing of each 
	directory and download anything it hasn't downloaded already.  The first time it runs, it will 
	download everything, but after that there will be a record of what has been downloaded, so only 
	things you don't have will be downloaded. 
#########################################################
#########################################################
        """ % (dbPath,dbPath,dbPath,dbPath)
        exit()
    conn = get_db_connection(dbPath)  
    get_list(conn)
    download_new(conn)
