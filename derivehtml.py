#!/usr/bin/env python
from gzip import GzipFile
from zipfile import ZipFile
from urllib2 import urlopen, HTTPError
from httplib import HTTPConnection
from boto.s3.connection import S3Connection

import couchdb
import abbyyhtml
from abbyyhtml import pagemerge
import bighead
import appauth

import sys
import getopt
import os
import gzip
import string
import StringIO
import json
import cgi
import re
import math
import time

def main(argv):
    abbyyref=argv[1]
    scanref=argv[2]
    outfile=argv[3]
    bookid=argv[4]
    doc=argv[5]
    try:
        already=urlopen(
            ("http://www.archive.org/download/%s/%s_ondemand.html"%(bookid,doc)))
    except HTTPError:
        already=False
    if (already):
        content=already.read()
        open(outfile,'w').write(content)
        exit()
    result=makehtml(bookid,doc=doc,abbyyref=abbyyref,scanref=scanref)
    resultdata=result.encode('utf-8')
    f=open(outfile,'w')
    f.write(resultdata)


    
    

