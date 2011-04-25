#!/usr/bin/env python
from gzip import GzipFile
from zipfile import ZipFile
from urllib2 import urlopen, HTTPError
from httplib import HTTPConnection
from boto.s3.connection import S3Connection

import couchdb
import abbyyhtml
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

def gethtml(spec,nowrap=False,mergepages=True,force=False):
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
    if olid in db:
        edit_entry=db[olid]
    else:
        edit_entry={}
    edit_entry['iaid']=iaid
    edit_entry['_id']=olid
    edit_entry['olid']=olid
    edit_entry['saved']=math.trunc(time.time())
    if (("attachments" in edit_entry) and
        ("source.html" in edit_entry["attachments"])):
    db[olid]=edit_entry
    conn=S3Connection(appauth.key,appauth.secret,host='s3.us.archive.org',is_secure=False)
    try:
        bucket=conn.get_bucket(olid)
    except Exception:
        bucket=conn.create_bucket(olid)
    key=bucket.get_key("source.xhtml")
    if key:
        return key.get_contents_as_string().decode('utf-8')
    print "No stored copy, generating from abbyy scan file"
    print "Fetching abbyy..."
    try:
        abbyystream=urlopen("http://www.archive.org/download/%s/%s_abbyy.gz"%(iaid,iaid))
        zipdata=abbyystream.read()
        f=GzipFile(fileobj=StringIO.StringIO(zipdata))
    except HTTPError:
        abbyystream=urlopen("http://www.archive.org/download/%s/%s_abbyy.zip"%(iaid,iaid))
        zipdata=abbyystream.read()
        zipfile=ZipFile(StringIO.StringIO(zipdata))
        names=zipfile.namelist()
        f=zipfile.open(names[0])
    # Do the generation
    print "Generating content"
    classmap={}
    if not mergepages:
        for line in abbyyhtml.getblocks(f,olid,classmap,olid=olid,iaid=iaid,inline_blocks=True):
            if (len(line)==0):
                pars
            else:
                pars.append(line)
    else:
        pars=pagemerge(f,olid,classmap,olid,iaid)
    if wrapbody:
        result="<?xml version='1.0' encoding='utf-8' ?>\n<?xml version='1.0' encoding='utf-8' ?>\n<!DOCTYPE html>\n"
        result=result+"<html>\n<head>\n"
        style=abbyy_css
        classhist=classmap['%histogram']
        for x in classmap:
            if not(x.startswith('%')):
                style=style+(".%s { %s } /* %d times */\n"%
                             (classmap[x],x,classhist[classmap[x]]))
        result=result+bighead.bighead(olid,style).encode("utf-8")
        result=result+"\n</head>\n<body>"
    for par in pars:
        result=result+"\n"+par
    print "Saving content to IA S3"
    key=bucket.new_key("%s_source.html"%iaid)
    key.set_contents_from_string(result.encode('utf-8'))
    return result
    
def pagemerge(f,bookid,classmap,olid,iaid,inline_blocks=True):
    # All the strings to be output (not strictly paragraphs, though)
    pars=[]
    # The current open paragraph
    openpar=False
    # The non-body elements processed since the open body paragraph
    waiting=[]
    # Whether the current paragraph ends with a hyphen
    openhyphen=False
    # If we're doing pagemerge, we read a stream of blocks,
    #    potentially merging blocks which cross page boundaries.  All
    #    the content blocks are paragraph <p> blocks, and the
    #    algorithm works by keeping the last paragraph block in
    #    _openpar_ and accumulating non paragraph blocks in the
    #    _waiting_ array. 
    #  When we get a paragraph that starts with a lowercase letter, we
    #    add it to the open paragraph together with all of the waiting
    #    non-body elements which have accumulated.
    for line in abbyyhtml.getblocks(f,bookid,classmap,olid=olid,iaid=iaid,inline_blocks=True):
        if (len(line)==0):
            pars
        elif (line.startswith("<p")):
            # We don't merge centered paragraphs
            if (line.find("abbyycentered")>0):
                if (openpar):
                    pars.append(openpar)
                    for elt in waiting:
                        pars.append(elt)
                    waiting=[]
                    # and start with a new open paragraph
                    pars.append(line)
                    openpar=False
                else:
                    for elt in waiting:
                        pars.append(elt)
                    waiting=[]
                    pars.append(line)
            elif (openpar):
                # We check if the first letter is lowercase by finding
                # the first post-markup letter and the first
                # post-markup lowercase letter and seeing if they're
                # in the same place.  Note that paragraphs whose text
                # starts with punctuation will not pass this test
                # (which I think is the right thing)
                firstletter=re.search("(?m)>(\s|'|\")*[a-zA-z]",line)
                firstlower=re.search("(?m)>(\s|'|\")*[a-z]",line)
                if ((not firstletter or not firstlower) or
                    ((firstletter.start()) != (firstlower.start()))):
                    # Not a continuation, so push the open paragraph
                    pars.append(openpar)
                    # add any intervening elements
                    for elt in waiting:
                        pars.append(elt)
                    waiting=[]
                    # and start with a new open paragraph
                    openpar=line
                else:
                    # This paragraph continues the previous one, so
                    #   we append it to openpar, with waiting elements
                    #   added to the middle
                    if openhyphen:
                        # Replace the closing hyphen (and the closing
                        # </p> tag) with an abbyydroppedhyphen span
                        par_end=openhyphen.start()
                        openpar=openpar[0:par_end]+"<span class='abbyydroppedhyphen'>-</span>"
                    else:
                        # Strip off the closing tag from the open par
                        search_end=re.search("(?m)</p>",openpar)
                        if search_end:
                            openpar=openpar[0:(search_end.start())]+" "
                        else: 
                            openpar=openpar+" "
                    for elt in waiting:
                        openpar=openpar+elt
                    waiting=[]
                    textstart=line.find(">")
                    openpar=openpar+line[textstart+1:]
            else:
                # This is the first paragraph
                openpar=line
                for elt in waiting:
                    pars.append(elt)
                waiting=[]
            # Check if the current open paragraph ends with a hyphen
            if (openpar):
                openhyphen=re.search("(?m)-\s*</p>",openpar)
            else:
                openhyphen=False
        else:
            waiting.append(line)
    if openpar:
        pars.append(openpar)
    for elt in waiting:
        pars.append(elt)
    return pars
        
