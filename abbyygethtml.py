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

import iarchive

# Useful test cases
# OL13684064M giftformsfunctio00maus
# OL2588416M handofethelberta01hard

def s3save(url,data):
    c=HTTPConnection("s3.us.archive.org")
    c.request("PUT",url,data,{"Authorization":auth})
    r=c.getresponse()
    print r.getheaders()
    print r.read()

ns = '{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'
page_tag = ns + 'page'
block_tag = ns + 'block'
olibid=False
iabook=False
bookid=False
max_width = 600
max_height = 780
wrapbody=True

tmp_cache=os.path.join(os.path.dirname(os.path.abspath(__file__)),"cache/%s.html")

abbyy_css=open(os.path.join(os.path.dirname(__file__),"abbyy.css")).read()

db=couchdb.client.Server(('http://%s:%s@ol-couch0:5984/'%(appauth.couchuser,appauth.couchpass)))['corrections']

def tryenv(var,dflt):
    if (os.environ.get(var)):
        return os.environ.get(var)
    else: return dflt

def makehtml(bookid,nowrap=False,mergepages=True):
    olib=False
    olid=False
    try:
        oliburl="http://www.openlibrary.org/ia/%s.json"%bookid
        olibstream=urlopen(oliburl)
        olib=json.load(olibstream)
        olid=os.path.basename(olib['key'])
    except HTTPError:
        error ("Can't get openlibrary info for %s"%bookid)
    olid=olib['key']
    print "Generating HTML file from abbyy scan file"
    classmap={}
    print "Generating body content"
    pars=abbyyhtml.makehtmlbody(olid,bookid,classmap)
    if not nowrap:
        result="<?xml version='1.0' encoding='utf-8' ?>\n<?xml version='1.0' encoding='utf-8' ?>\n<!DOCTYPE html>\n"
        result=result+"<html>\n<head>\n"
        style=abbyy_css
        classhist=classmap['%histogram']
        for x in classmap:
            if not(x.startswith('%')):
                style=style+(".%s { %s } /* used %d times */\n"%
                             (classmap[x],x,classhist[classmap[x]]))
        result=result+bighead.bighead(olid,style).encode("utf-8")
        result=result+"\n</head>\n<body class='abbyytext'>"
    else:
        result=""
    for par in pars:
        result=result+"\n"+par
    if not nowrap:
        result=result+"\n</body>\n</html>\n"
    return result

def gethtml(spec,nowrap=False,mergepages=True,filecache=tmp_cache,skipcache=False):
    olid=False
    bookid=False
    olib=False
    if (spec.startswith('OL')):
        olid=spec
        oliburl="http://www.openlibrary.org/books/%s.json"%olid
        olibstream=urlopen(oliburl)
        olib=json.load(olibstream)
        bookid=olib["ocaid"]
        if (not(bookid)):
            error ("No archive reference for %s"%olid)
    else:
        bookid=spec
    cachestream=False
    if not skipcache:
        try:
            cachestream=urlopen(
                ("http://www.archive.org/download/%s/%s_corrected.html"%(bookid,bookid)))
        except HTTPError:
            try:
                cachestream=urlopen(
                    ("http://www.archive.org/download/%s/%s_abbyy.html"%(bookid,bookid)))
            except HTTPError:
                if filecache and os.path.exists(filecache%bookid):
                    cachestream=open(tmp_cache%bookid)
                else: cachestream=False
    if cachestream:
        return cachestream.read().decode('utf8')
    print "No stored copy, generating from abbyy scan file"
    result=makehtml(bookid,nowrap=nowrap,mergepages=mergepages)
    resultdata=result.encode('utf-8')
    if filecache:
        open(filecache%bookid,"w").write(resultdata)
    return result


class BookContent:
    def __init__(self,body,style):
        self.body=body
        if (style):
            self.style=style
        else: self.style=""

def getbookcontent(spec):
    text=gethtml(spec)
    style_start=re.search("(?i)<style[^>]*>",text)
    style_end=re.search("(?i)</style[^>]*>",text)
    body_start=re.search("(?i)<body[^>]*>",text)
    body_end=re.search("(?i)</body[^>]*>",text)
    body=False
    style=False
    if ((body_start) and (body_end)):
        if ((style_start) and (style_end)):
            style=text[style_start.end():style_end.start()]
        body=text[body_start.end():body_end.start()]
    else:
        body=text
    return BookContent(body,style)
