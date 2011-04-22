#!/usr/bin/env python
from gzip import GzipFile
from zipfile import ZipFile
from urllib2 import urlopen, HTTPError

import abbyyhtml
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

import iarchive

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

def tryenv(var,dflt):
    if (os.environ.get(var)):
        return os.environ.get(var)
    else: return dflt

def abbyy2html(spec,nowrap=False,pagemerge=True):
    olid=False
    iaid=False
    olib=False
    details=False
    if (spec.startswith('OL')):
        olid=spec
    else:
        iaid=spec
    if not iaid:
        olibstream=urlopen("http://www.openlibrary.org/books/%s.json"%olid)
        olib=json.load(olibstream)
        iaid=olibinfo["ocaid"]
        if (not(iaid)):
            error ("No archive reference for %s"%olid)
    if not olid:
        detailstream=urlopen("http://www.archive.org/details/%s?output=json"%iaid)
        details=json.load(detailstream)
        if 'olib' in details:
            olib=details['olib']
        else:
            error ("No open library reference for %s"%iaid)
    if not olib:
        olibstream=urlopen("http://www.openlibrary.org/books/%s.json"%olid)
        olib=json.load(olibstream)
    if not details:
        detailstream=urlopen("http://www.archive.org/details/%s?output=json"%iaid)
        details=json.load(detailstream)
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
    if "metadata" in details:
        # Extract some metadata
       metadata=details["metadata"]
       if "title" in metadata: title=string.replace(metadata["title"][0],"'","&apos;")
       if "creator" in metadata: creator=string.replace(metadata["creator"][0],"'","&apos;")
    try:
        s3stream=urlopen("http://s3.us.archive.org/%s/%s_source.html"%(iaid,iaid))
    except HTTPError:
    
    # Do the generation
    # All the strings to be output (not strictly paragraphs, though)
    pars=[]
    # The current open paragraph
    openpar=False
    # The non-body elements processed since the open body paragraph
    waiting=[]
    # Whether the current paragraph ends with a hyphen
    openhyphen=False
    classmap={}
    if not pagemerge:
        for line in abbyyhtml.getblocks(f,bookid,classmap,olid=olibid,iaid=iaid,inline_blocks=True):
            if (len(line)==0):
                pars
            else:
                pars.append(line)
    else:
    # If we're doing pagemerge, we read a stream of blocks,
    #    potentially merging blocks which cross page boundaries.  All
    #    the content blocks are paragraph <p> blocks, and the
    #    algorithm works by keeping the last paragraph block in
    #    _openpar_ and accumulating non paragraph blocks in the
    #    _waiting_ array. 
    #  When we get a paragraph that starts with a lowercase letter, we
    #    add it to the open paragraph together with all of the waiting
    #    non-body elements which have accumulated.
    for line in abbyyhtml.getblocks(f,bookid,classmap,olid=olibid,iaid=iaid,inline_blocks=True):
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

if wrapbody:
    print "<?xml version='1.0' encoding='utf-8' ?>"
    print "<!DOCTYPE html>"
    print "<html>"
    print "<head>"
    style=abbyy_css
    classhist=classmap['%histogram']
    for x in classmap:
        if not(x.startswith('%')):
            style=style+(".%s { %s } /* %d times */\n"%
                         (classmap[x],x,classhist[classmap[x]]))
    print bighead.bighead(olibid,style).encode("utf-8")
    print "</head>"
    print "<body>"

for par in pars:
    print par.encode('utf-8')

if wrapbody:
    print "</body>"
    print "</html>"
