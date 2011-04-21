#!/usr/bin/env python
from urllib2 import urlopen, HTTPError

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

def olibget(spec):
    if (spec.find("/")<0):
        if (spec.endswith("M")):
            spec="/books/"+spec
        elif (spec.endswith("W")):
            spec="/works/"+spec
        elif (spec.endswith("A")):
            spec="/authors/"+spec
        else: raise Exception("Weird OLIB spec",spec)
    if (not spec.startswith("/")):
        spec="/"+spec
    olibstream=urlopen("http://www.openlibrary.org%s.json"%spec)
    olibinfo=json.load(olibstream)
    olibstream.close()
    return olibinfo

def bighead(spec,style,script):
    h=""
    info=olibget(spec)
    h=h+"<link rel='schema.IA' href='http://archive.org'/>\n"
    h=h+"<link rel='schema.OL' href='http://openlibrary.org'/>\n"
    h=h+"<link rel='schema.OK' href='http://openknotes.org'/>\n"
    h=h+"<link rel='schema.DC' href='http://purl.org/dc/elements/1.1/'/>\n"
    h=h+"<link rel='schema.DCTERMS' href='http://purl.org/dc/terms/'/>\n"    
    h=h+("<meta name='OL.ref' content='%s'/>\n"%(os.dir.basename(spec)))
    h=h+"<meta name='DC.type' scheme='DCTERMS.DCMIType' content='Text'/>\n"
    if 'ocaid' in bookinfo:
        h=h+("<meta name='IA.item' content='%s'/>\n"%info['ocaid'])
    titlestring=""
    if 'title' in info: titlestring=info['title']
    if 'by_statement' in info:
        titlestring=titlestring+(" %s"%info['by_statement'])
    h=h+("<title>%s</title>\n"%title)
    if 'title' in info:
        h=h+("<meta name='DC.title' content='%s'/>\n"%info['title'])
    if 'authors' in info:
        for author in info['authors']:
            h=h+("<link rel='DC.creator' href='http://openlibrary.org%s'/>\n"%
                 author)
            ainfo=olibget(author)
            aname=ainfo['name']
            if 'birth_date' in aname:
                aname=aname+((" %s-")%(ainfo['birth_date']))
                if 'death_date' in aname:
                    aname=aname+ainfo['death_date']
            elif 'death_date' in aname:
                aname=aname+ainfo['death_date']
            h=h+("<meta name='DC.creator' content='%s'/>\n"%aname)
    if 'publishers' in info:
        for publisher in info['publishers']:
            h=h+("<meta name='DC.publisher' content='%s'/>\n"%
                 publisher)
    description=False
    if 'description' in info:
        description=info['description']
        h=h+("<meta name='DESCRIPTION' content='%s'/>\n"%description)
    if 'works' in info:
        for work in info['works']:
            workinfo=olibget(work['key'])
            h=h+("<link rel='OL.work' href='http://openlibrary.org%s'/>\n"%
                 work['key'])
            if not description and 'description' in workinfo:
                h=h+("<meta name='DESCRIPTION' content='%s'/><!-- from %s ->> \n"%
                     (workinfo['description'],workinfo['title']))
    if 'publish_date' in info:
        h=h+("<meta name='DC.date' content='%s'/>\n"%info['publish_date'])
    if (style):
        h=h+("<style>\n%s\n</style>\n"%style)
    if (script):
        h=h+("<script language='javascript'>\n<![CDATA[\n%s\n]!>\n</style>\n"%script)
