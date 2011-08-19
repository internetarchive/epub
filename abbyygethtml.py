#!/usr/bin/env python
from gzip import GzipFile
from zipfile import ZipFile
from urllib2 import urlopen, HTTPError
from httplib import HTTPConnection

#import couchdb
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
    auth="LOW %s:%s"%(appauth.key,appauth.secret)
    c=HTTPConnection("s3.us.archive.org")
    c.request("PUT",url,data,{"Authorization":auth})
    r=c.getresponse()
    #print r.getheaders()
    #print r.read()

ns = '{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'
page_tag = ns + 'page'
block_tag = ns + 'block'
olibid=False
iabook=False
bookid=False
max_width = 600
max_height = 780
wrapbody=True

abbyy_css=open(os.path.join(os.path.dirname(__file__),"abbyy.css")).read()

#db=couchdb.client.Server(('http://%s:%s@ol-couch0:5984/'%(appauth.couchuser,appauth.couchpass)))['corrections']

def tryenv(var,dflt):
    if (os.environ.get(var)):
        return os.environ.get(var)
    else: return dflt

def olib_lookup(bookid):
    try:
        oliburl="http://www.openlibrary.org/ia/%s.json"%bookid
        olibstream=urlopen(oliburl)
        return json.load(olibstream)
    except HTTPError:
        return False

def tryopen(ref):
    stream=False
    if ((ref.startswith("http:")) or
        (ref.startswith("https:"))):
        try:
            stream=urlopen(ref)
        except HTTPError:
            stream=False
    else:
        try:
            stream=open(ref)
        except FileError:
            stream=False
    if stream:
        if (ref.endswith('.gz')):
            zipdata=stream.read()
            return GzipFile(fileobj=StringIO.StringIO(zipdata))
        elif (ref.endswith('.zip')):
            zipdata=stram.read()
            zipfile=ZipFile(StringIO.StringIO(zipdata))
            names=zipfile.namelist()
            return zipfile.open(names[0])
        else: return stream
    else: return stream

def trypaths(paths):
    for path in paths:
        stream=tryopen(path)
        if stream:
            return stream
    return False

def find_scandata(bookid,doc,path):
    if not doc: doc=bookid
    if not path: path="http://www.archive.org/downloads/"
    base=path+bookid+"/"+doc
    stream=trypaths([base+"_scandata.xml",
                     base+"_scandata.zip",
                     base+"_scandata.xml.gz",
                     base+"_scandata.xml.zip"])
    if (stream): return stream
    elif bookid is doc:
        return trypaths([path+bookid+"/scandata.xml",
                         path+bookid+"/scandata.xml.zip",
                         path+bookid+"/scandata.xml.gz",
                         path+bookid+"/scandata.zip",
                         path+bookid+"/scandata.gz"])
    else: return False

def parse_scandata(stream,scandata=False):
    if not scandata:
        scandata=parse(stream)
    pages=scandata.getElementsByTagName('page')
    scaninfo={}
    for x in pages:
        leafno=int(x.getAttribute('leafNum'))
        info={"leafno": leafno}
        scaninfo[leafno]=info
        pagenum=x.getElementsByTagName('pageNumber')
        if (pagenum and (pagenum.length>0) and
            pagenum[0] and (pagenum[0].childNodes.length==1)):
            info['pageno']=pagenum[0].childNodes[0].nodeValue
        doscan=x.getElementsByTagName('addToAccessFormats')
        if (pagenum and (pagenum.length>0) and
            pagenum[0] and (pagenum[0].childNodes.length==1) and
            pagenum[0].childNodes[0].nodeValue=='false'):
            info['ignore']=True
        else:
            info['ignore']=False
    return scaninfo

def find_abbyy(bookid,doc=False,path=False):
    if not doc: doc=bookid
    if not path: path="http://www.archive.org/download/"
    base=path+bookid+"/"+doc
    # print "Looking for abbyy under %s"%base
    return trypaths([base+"_abbyy.xml",
                     base+"_abbyy.zip",
                     base+"_abbyy.gz"])

def makehtml(bookid,doc=False,path=False,
             abbyyref=False,scanref=False,
             wrap=True,mergepages=True):
    if not doc: doc=bookid
    classmap={}
    olib=False
    olid=False
    if doc is bookid:
        olib=olib_lookup(bookid)
        if olib: olid=os.path.basename(olib['key'])
    if olid:
        idprefix=olid
    else:
        idprefix=bookid
    # print "Generating HTML file from abbyy scan file"
    if scanref: scanstream=tryopen(scanref)
    else: scanstream=find_scandata(bookid,doc,path)
    if scanstream:
        scaninfo=parse_scandata(scanstream)
    else:
        scaninfo=False
    abbyystream=False
    if abbyyref:
        abbyystream=tryopen(abbyyref)
        if not abbystream:
            raise Exception("Can't open abbyy file '%s'"%abbyyref)
    else:
        abbyystream=find_abbyy(bookid,doc,path)
        if not abbyystream:
            raise Exception("Can't find abbyy file for '%s/%s' under '%s'"%
                        (bookid,doc,path))
    # print "Generating body content"
    pars=abbyyhtml.makehtmlbody(abbyystream,idprefix,bookid,doc,
                                classmap=classmap,
                                scaninfo=scaninfo)
    if wrap:
        # print "Wrapping body with metadata, etc"
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
    if wrap:
        result=result+"\n</body>\n</html>\n"
    return result

def gethtml(spec,doc=False,
            wrap=True,mergepages=True,
            useS3=True,skipcache=False,
            filecache=False):
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
            raise Exception("No archive reference for %s"%olid)
        if not doc: doc=bookid
    elif (spec.find('/')>0):
        split=spec.find('/')
        bookid=spec[0:split]
        doc=spec[split+1:]
    else:
        bookid=spec
        if not doc: doc=bookid
    if not skipcache and filecache:
        cache_path=os.path.join(filecache,bookid+".html")
        if (os.path.exists(cache_path)):
            return open(cache_path).read().decode('utf-8')
    cachestream=False
    if not skipcache and useS3:
        try:
            cachestream=urlopen(
                ("http://www.archive.org/download/%s/%s_abbyy.html"%(bookid,bookid)))
        except HTTPError:
            try:
                cachestream=urlopen(
                    ("http://www.archive.org/download/%s/%s_ondemand.html"%(bookid,bookid)))
            except HTTPError:
                cachestream=False
    if cachestream:
        return cachestream.read().decode('utf8')
    # print "No stored copy, generating from abbyy scan file"
    result=makehtml(bookid,doc,wrap=wrap,mergepages=mergepages)
    resultdata=result.encode('utf-8')
    if filecache and not skipcache:
        cache_path=os.path.join(filecache,bookid+".html")
        # print "Saving to '%s'"%cache_path
        stream=open(cache_path,'w')
        stream.write(resultdata)
        stream.close()
    if useS3:
        path="http://s3.us.archive.org/%s/%s_ondemand.html"%(bookid,bookid)
        path="http://s3.us.archive.org/abbyyhtml/%s_ondemand.html"%bookid
        try:
            s3save(path,resultdata)
        except:
            print "Error saving to IA S3"
    return result


# Remaking HTML

def remakehtml(olid,body,style):
    result="<?xml version='1.0' encoding='utf-8' ?>\n<?xml version='1.0' encoding='utf-8' ?>\n<!DOCTYPE html>\n"
    result=result+"<html>\n<head>\n"
    result=result+bighead.bighead(olid,style).encode("utf-8")
    result=result+"\n</head>\n<body class='abbyytext'>"+body+"</body>"
    return result


class BookContent:
    def __init__(self,body,style):
        self.body=body
        if (style):
            self.style=style
        else: self.style=""

def getbookcontent(spec,cache=False):
    text=gethtml(spec,filecache=cache)
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

