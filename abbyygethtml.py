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

cache="/tmp/abbyy2html/"

ns = '{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'
page_tag = ns + 'page'
block_tag = ns + 'block'
olibid=False
iabook=False
iaid=False
max_width = 600
max_height = 780
wrapbody=True

abbyy_css=open(os.path.join(os.path.dirname(__file__),"abbyy.css")).read()

db=couchdb.client.Server(('http://%s:%s@ol-couch0:5984/'%(appauth.couchuser,appauth.couchpass)))['corrections']

def tryenv(var,dflt):
    if (os.environ.get(var)):
        return os.environ.get(var)
    else: return dflt

def gethtml(spec,nowrap=False,mergepages=True,usecouch=True,skipcache=False):
    olid=False
    iaid=False
    olib=False
    if (spec.startswith('OL')):
        olid=spec
    else:
        iaid=spec
    if not iaid:
        olibstream=urlopen("http://www.openlibrary.org/books/%s.json"%olid)
        olib=json.load(olibstream)
        iaid=olib["ocaid"]
        if (not(iaid)):
            error ("No archive reference for %s"%olid)
    if not olid:
        olibstream=urlopen("http://www.openlibrary.org/ia/%s.json"%iaid)
        olib=json.load(olibstream)
        olid=os.path.basename(olib['key'])
    if usecouch:
        if olid in db:
            edit_entry=db[olid]
        else:
            edit_entry={}
        edit_entry['iaid']=iaid
        edit_entry['_id']=olid
        edit_entry['olid']=olid
        edit_entry['saved']=math.trunc(time.time())
        if ((not skipcache) and ("_attachments" in edit_entry) and
            ("source.html" in edit_entry["_attachments"])):
            return (db.get_attachment(olid,"source.html")).read().decode("utf-8")
    if not skipcache:
        try:
            archivestream=urlopen(
                ("http://www.archive.org/download/%s/%s_corrected.html"%
                 (iaid,iaid)))
        except HTTPError:
            archivestream=urlopen(
                ("http://www.archive.org/download/%s/%s_source.html"%
                 (iaid,iaid)))
        except HTTPError:
            archivestream=False
    else:
        archivestream=False
    if archivestream:
        return archivestream.read()

    print "No stored copy, generating from abbyy scan file"
    classmap={}
    print "Generating content"
    pars=abbyyhtml.makehtml(olid,iaid,classmap)
    if wrapbody:
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
    for par in pars:
        result=result+"\n"+par
    if usecouch:
        print "Saving content to CouchDB"
        db[olid]=edit_entry
        new_entry=db[olid]
        db.put_attachment(new_entry,result.encode('utf-8'),
                          'source.html','text/html')
    try:
        conn=S3Connection(appauth.key,appauth.secret,host='s3.us.archive.org',is_secure=False)
        # bucket=conn.get_bucket(iaid)
        bucket=conn.get_bucket('abbyyhtml')
        key=bucket.get_key("%s_source.html"%iaid)
        if not key:
            key=bucket.new_key("%s_source.html"%iaid)
            key.set_contents_from_string(result.encode('utf-8'))
    except:
        print "Error saving to IA S3"
    return result

