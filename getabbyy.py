from gzip import GzipFile
from zipfile import ZipFile
from urllib2 import urlopen, HTTPError

import abbyystreams

import sys
import getopt
import os
import gzip
import string
import StringIO
import json
import cgi

import iarchive

ns = '{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'
page_tag = ns + 'page'
block_tag = ns + 'block'
olibid=False
iabook=False
iaid=False
max_width = 600
max_height = 780

def tryenv(var,dflt):
    if (os.environ.get(var)):
        return os.environ.get(var)
    else: return dflt

fontmap={}
def getfontname(s):
    if (s in fontmap):
       return fontmap[s]
    else: return "'%s'"%s

if (os.path.exists(sys.argv[1])):
    bookid='sbook'
    if sys.argv[1].endswith('.gz'):
        f=gzip.open(sys.argv[1])
    else: f=open(sys.argv[1])
elif (sys.argv[1].startswith('http')):
    bookid='sbook'
    if sys.argv[1].endswith('.gz'):
        f=GzipFile(fileobj=urlopen(sys.argv[1]))
    else: f=urlopen(sys.argv[1])
else:
    if (sys.argv[1].startswith('OL')):
        olibstream=urlopen("http://www.openlibrary.org/books/%s.json"%sys.argv[1])
        olibinfo=json.load(olibstream)
        olibid=sys.argv[1]
        iaid=olibinfo["ocaid"]
        if (not(iaid)):
            error ("No archive reference for %s"%olibid)
    else: iaid=sys.argv[1]
    bookid=sys.argv[1]
    try:
        urlstream=urlopen("http://www.archive.org/download/%s/%s_abbyy.gz"%(iaid,iaid))
        zipdata=urlstream.read()
        f=GzipFile(fileobj=StringIO.StringIO(zipdata))
    except HTTPError:
        urlstream=urlopen("http://www.archive.org/download/%s/%s_abbyy.zip"%(iaid,iaid))
        zipdata=urlstream.read()
        zipfile=ZipFile(StringIO.StringIO(zipdata))
        names=zipfile.namelist()
        f=zipfile.open(names[0])

output=open("%s.abbyy"%sys.argv[1],"w")
while (True):
    try:
        line=f.read(65536)
        if len(line)==0:
            output.close()
            break
        output.write(line)
    except IOError:
        output.close()
        break


