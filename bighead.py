#!/usr/bin/env python
from urllib2 import urlopen, HTTPError
from lxml import objectify

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

def redirurl(url):
    i=0
    f=urlopen(url)
    while ((f.geturl()!=url) and (i<5)):
        url=f.geturl()
        f=urlopen(url)
        i=i+1
    if (f.geturl() is url):
        return f
    else: return False

def getmetaxml(spec):
    if ((spec.find("/")>=0) and (spec.starts_with("http"))):
        f=urlopen(spec)
    elif (spec.find("/")>=0):
        f=open(xmlfile)
    else: f=redirurl("http://www.archive.org/services/find_file.php?file=%s"%spec)
    xml=objectify.parse(f)
    result={}
    if (xml.find('identifier')):
        result['identifier']=xml.find('identifier')
    if (xml.find('identifier-access')):
        result['identifier-access']=xml.find('identifier-access')
    if (xml.find('title')):
        result['title']=xml.find('title')
    if (xml.find('creator')):
        result['creators']=xml.findall('creator')
    if (xml.find('subject')):
        result['subjects']=xml.findall('subject')
    if (xml.find('publisher')):
        result['publishers']=xml.findall('publisher')
    if (xml.find('date')):
        result['date']=xml.find('date')
    return result

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

def bighead(metaxml,olid,style=False,script=False):
    return bighead_ia(metaxml,olid,style,script)

def bighead_olib(metafile,spec,style=False,script=False):
    h=""
    olibinfo=olibget(spec)
    h=h+"<link rel='schema.IA' href='http://archive.org'/>\n"
    h=h+"<link rel='schema.OL' href='http://openlibrary.org'/>\n"
    h=h+"<link rel='schema.OK' href='http://openknotes.org'/>\n"
    h=h+"<link rel='schema.DC' href='http://purl.org/dc/elements/1.1/'/>\n"
    h=h+"<link rel='schema.DCTERMS' href='http://purl.org/dc/terms/'/>\n"    
    h=h+("<meta name='OL.ref' content='%s'/>\n"%(os.path.basename(spec)))
    h=h+"<meta name='DC.type' scheme='DCTERMS.DCMIType' content='Text'/>\n"
    if 'identifier' in metaxml:
        h=h+("<meta name='IA.item' content='%s'/>\n"%metaxml['identifier'])
    if 'identifier-access' in metaxml:
        h=h+("<link rel='IA.details' href='%s'/>\n"%metaxml['identifier-access'])
    titlestring=""
    if 'title' in info: titlestring=info['title']
    if 'by_statement' in info:
        titlestring=titlestring+(" %s"%info['by_statement'])
    h=h+("<title>%s</title>\n"%cgi.escape(titlestring,True))
    if 'title' in info:
        h=h+("<meta name='DC.title' content='%s'/>\n"%cgi.escape(info['title'],True))
    if 'authors' in info:
        for author in info['authors']:
            h=h+("<link rel='DC.creator' href='http://openlibrary.org%s'/>\n"%
                 author['key'])
            ainfo=olibget(author['key'])
            aname=ainfo['name']
            if 'birth_date' in aname:
                aname=aname+((" %s-")%(ainfo['birth_date']))
                if 'death_date' in aname:
                    aname=aname+ainfo['death_date']
            elif 'death_date' in aname:
                aname=aname+ainfo['death_date']
            h=h+("<meta name='DC.creator' content='%s'/>\n"%cgi.escape(aname,True))
    if 'publishers' in info:
        for publisher in info['publishers']:
            h=h+("<meta name='DC.publisher' content='%s'/>\n"%
                 cgi.escape(publisher,True))
    description=False
    if 'description' in info:
        description=info['description']
        h=h+("<meta name='DESCRIPTION' content='%s'/>\n"%cgi.escape(description,True))
    if 'works' in info:
        for work in info['works']:
            workinfo=olibget(work['key'])
            h=h+("<link rel='OL.work' href='http://openlibrary.org%s'/>\n"%
                 work['key'])
            if not description and 'description' in workinfo:
                d=workinfo['description']
                if type(d) is dict:
                    d=d['value']
                if isinstance(d,basestring): # odd result from olib
                    ""
                elif 'title' in workinfo:
                    h=h+("<meta name='DESCRIPTION' content='%s'/><!-- from %s --> \n"%
                         (cgi.escape(re.sub("\s+"," ",workinfo['description']),True),
                          cgi.escape(workinfo['title'],True)))
                else:
                    h=h+("<meta name='DESCRIPTION' content='%s'/><!-- from %s --> \n"%
                         (cgi.escape(re.sub("\s+"," ",workinfo['description']),True)))
    if 'publish_date' in info:
        h=h+("<meta name='DC.date' content='%s'/>\n"%cgi.escape(info['publish_date'],True))
    if (style):
        h=h+("<style id='ABBYYSTYLE'>\n%s\n</style>\n"%style)
    if (script):
        h=h+("<script language='javascript'>\n<![CDATA[\n%s\n]!>\n</style>\n"%script)
    return h

def bighead_ia(metafile,spec,style=False,script=False):
    h=""
    if spec:
        olibinfo=olibget(spec)
    else: olibinfo={}
    metaxml=getmetaxml(metafile)
    h=h+"<link rel='schema.IA' href='http://archive.org'/>\n"
    h=h+"<link rel='schema.OL' href='http://openlibrary.org'/>\n"
    h=h+"<link rel='schema.OK' href='http://openknotes.org'/>\n"
    h=h+"<link rel='schema.DC' href='http://purl.org/dc/elements/1.1/'/>\n"
    h=h+"<link rel='schema.DCTERMS' href='http://purl.org/dc/terms/'/>\n"    
    h=h+"<meta name='DC.type' scheme='DCTERMS.DCMIType' content='Text'/>\n"
    if spec:
        h=h+("<meta name='OL.ref' content='%s'/>\n"%(os.path.basename(spec)))
    if 'identifier' in metaxml:
        h=h+("<meta name='IA.item' content='%s'/>\n"%metaxml['identifier'])
    if 'identifier-access' in metaxml:
        h=h+("<link rel='IA.details' href='%s'/>\n"%metaxml['identifier-access'])
    titlestring=""
    if 'title' in metaxml: titlestring=metaxml['title']
    if 'creator' in metaxml: titlestring=titlestring+metaxml['creators'][0]
    h=h+("<title>%s</title>\n"%cgi.escape(titlestring,True))
    if 'title' in metaxml:
        h=h+("<meta name='DC.title' content='%s'/>\n"%cgi.escape(metaxml['title'],True))
    if 'creators' in metaxml:
        for author in metaxml['creators']:
            h=h+("<meta name='DC.creator' content='%s'/>\n"%cgi.escape(author,True))
    if 'publishers' in metaxml:
        for publisher in metaxml['publishers']:
            h=h+("<meta name='DC.publisher' content='%s'/>\n"%
                 cgi.escape(publisher,True))
    if 'subjects' in metaxml:
        keywords=False
        for subject in metaxml['subjects']:
            h=h+("<meta name='DC.subject' content='%s'/>\n"%cgi.escape(subject,True))
            if keywords:
                keywords=subject
            else: keywords=keywords+","+subject
        if keywords:
            h=h+("<meta name='KEYWORDS' content='%s'/>"%keywords)
    if (style):
        h=h+("<style id='ABBYYSTYLE'>\n%s\n</style>\n"%style)
    if (script):
        h=h+("<script language='javascript'>\n<![CDATA[\n%s\n]!>\n</style>\n"%script)
    return h
