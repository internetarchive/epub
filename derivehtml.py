#!/usr/bin/env python
from gzip import GzipFile
from zipfile import ZipFile
from urllib2 import urlopen, HTTPError
from httplib import HTTPConnection
from lxml.etree import parse

import abbyyhtml
from abbyyhtml import pagemerge
import bighead

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

def makehtml(itemid,doc,abbyyfile,abbyyhtml,scanfile,metafile,olid):
    classmap={}
    # print "Generating HTML file from abbyy scan file"
    scanstream=open(scanfile)
    scaninfo=parse_scandata(scanstream)
    close(scanstream)
    abbyystream=open(abbyyfile)
    metadata=getmetaxml(metafile)
    if (olid): bookid=olid
    else: bookid=itemid
    # print "Generating body content"
    pars=abbyyhtml.makehtmlbody(abbyystream,bookid,itemid,doc,
                                classmap=classmap,
                                scaninfo=scaninfo)
    # print "Wrapping body with metadata, etc"
    result=u"<?xml version='1.0' encoding='utf-8' ?>\n<?xml version='1.0' encoding='utf-8' ?>\n<!DOCTYPE html>\n"
    result=result+u"<html>\n<head>\n"
    style=abbyy_css
    classhist=classmap['%histogram']
    for x in classmap:
        if not(x.startswith('%')):
            style=style+(".%s { %s } /* used %d times */\n"%
                         (classmap[x],x,classhist[classmap[x]]))
    result=result+bighead.bighead(metadata,olid,style)
    result=result+u"\n</head>\n<body class='abbyytext'>"
    for par in pars:
        result=result+"\n"+par
    if wrap:
        result=result+"\n</body>\n</html>\n"
    return result

def main(argv):
    itemid=argv[1]
    doc=argv[2]
    abbyyfile=argv[3]
    htmlout=argv[4]
    scanfile=argv[5]
    metafile=argv[6]
    if (len(argv)>7):
        olid=argv[7]
    else:
        olid=False
    result=makehtml(itemid,doc,abbyyfile,tmpfile,scanfile,metafile,olid)
    f=open(htmlout,"w")
    f.write(result.encode('utf-8'))
    close(f)



    
    

