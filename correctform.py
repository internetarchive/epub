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

def getpageurl(bookid,doc=False):
    if not doc: doc=bookid
    return ("http://www.archive.org/download/%s/%s/page/leaf%%_medium.jpg"%
            (bookid,doc))

def getbooklink(olib):
    return "http://www.openlibrary.org/books/"+olib

def getauthorlink(olib):
    return "http://www.openlibrary.org/authors/"+olib

spec=(sys.argv[1])
leaf=int(sys.argv[2])
cache=sys.argv[3]
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

template=open(os.path.join(os.path.dirname(__file__),"suds/proof.html"),"rt",).read()
html=abbyygethtml.getbookcontent(bookid,cache)
rewrite=string.replace(
    string.replace(
        string.replace(
            string.replace(
                string.replace(
                    string.replace(
                        string.replace(
                            string.replace(
                                string.replace(
                                    string.replace(
                                        string.replace(template,"%%SPEC",spec),
                                        "%%OLID",olid),
                                    "%%BOOKID",bookid),
                                "%%LEAF",str(leaf)),
                            "%%TITLE",olibinfo["title"]),
                        "%%IMGTEMPLATE",getpageurl(bookid)),
                    "%%BOOKLINK",getbooklink(olid)),
                "%%AUTHORLINK",getauthorlink(authorid)),
            "%%AUTHORNAME",authorinfo["name"]),
        "%%BOOKTEXT",html.body),
    "%%STYLE",html.style)

print rewrite.encode('utf-8')
