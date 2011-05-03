#!/usr/bin/env python
from urllib2 import urlopen, HTTPError
from urlparse import urlparse

import sys
import subprocess
import os
import string
import StringIO
import json
import cgi
#import cgitb
import re
import io

#cgitb.enable()

import abbyyhtml
import abbyygethtml
from abbyygethtml import gethtml

abbyy2html=os.path.join(os.path.dirname(os.path.abspath(__file__)),"../abbyy2html")

def getbookpath(bookid):
    tmp_url="http://www.archive.org/download/%s/%s_meta.xml"%(bookid,bookid)
    urlstream=urlopen(tmp_url)
    # read a little to get it to get the redirect
    urlstream.read(3)
    # Now get the actual URL
    real_url=urlstream.geturl()
    urlstream.close()
    return real_url.replace("_meta.xml","")

def getimageurl(bookid,bookpath):
    parsed=urlparse(bookpath)
    return (("http://"+parsed.netloc+"/BookReader/BookReaderImages.php")+
            ("?zip="+parsed.path+"_jp2.zip")+
            ("&file="+bookid+"_jp2/"+bookid+"_%%%%"+".jp2")+
            ("&scale=4&rotate=0"))

def getbooklink(olib):
    return "http://www.openlibrary.org/books/"+olib

def getauthorlink(olib):
    return "http://www.openlibrary.org/authors/"+olib

spec=(sys.argv[1])
leaf=int(sys.argv[2])
bookid=False
olid=False

if (spec.startswith('OL')):
    olibstream=urlopen("http://www.openlibrary.org/books/%s.json"%spec)
else:
    olibstream=urlopen("http://www.openlibrary.org/ia/%s.json"%spec)

olibinfo=json.load(olibstream)

if (spec.startswith('OL')):
    olid=spec
    bookid=olibinfo['ocaid']
else:
    bookid=spec
    olid=os.path.basename(olibinfo['key'])

authorid=olibinfo["authors"][0]["key"]
olibstream=urlopen("http://www.openlibrary.org%s.json"%authorid)
authorinfo=json.load(olibstream)

bookpath=getbookpath(bookid)

template=open(os.path.join(os.path.dirname(__file__),"suds/proof.html"),"rt",).read()
html=abbyygethtml.getbookcontent(bookid)
rewrite=string.replace(
    string.replace(
        string.replace(
            string.replace(
                string.replace(
                    string.replace(
                        string.replace(
                            string.replace(
                                string.replace(template,"%%SPEC",spec),
                                "%%LEAF",str(leaf)),
                            "%%TITLE",olibinfo["title"]),
                        "%%IMGTEMPLATE",getimageurl(bookid,bookpath)),
                    "%%BOOKLINK",getbooklink(olid)),
                "%%AUTHORLINK",getauthorlink(authorid)),
            "%%AUTHORNAME",authorinfo["name"]),
        "%%BOOKTEXT",html.body),
    "%%STYLE",html.style)

print rewrite.encode('utf-8')
