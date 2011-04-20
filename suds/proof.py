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
import re
import io

abbyy2html=os.path.join(os.path.dirname(__file__),"../abbyy2html")
tmp_cache=os.path.join(os.path.dirname(__file__),"../cache/%s.html")

class BookHTML:
    def __init__(self,body,style):
        self.body=body
        if (style):
            self.style=style
        else: self.style=""

def getbookhtml(olib):
    path=tmp_cache%olib
    if (os.path.exists(path)):
        text=io.open(path,"rt",encoding="utf-8").read()
    else:
        args=[abbyy2html,olib]
        proc=subprocess.Popen(args,stdout=io.open(path,"wt",encoding="utf-8"))
        proc.wait()
        text=io.open(path,"rt",encoding="utf-8").read()
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
    return BookHTML(body,style)

def getbookpath(iaid):
    tmp_url="http://www.archive.org/download/%s/%s_meta.xml"%(iaid,iaid)
    urlstream=urlopen(tmp_url)
    # read a little to get it to get the redirect
    urlstream.read(3)
    # Now get the actual URL
    real_url=urlstream.geturl()
    urlstream.close()
    return real_url.replace("_meta.xml","")

def getimageurl(iaid,bookpath):
    parsed=urlparse(bookpath)
    return (("http://"+parsed.netloc+"/BookReader/BookReaderImages.php")+
            ("?zip="+parsed.path+"_jp2.zip")+
            ("&file="+iaid+"_jp2/"+iaid+"_%%%%"+".jp2")+
            ("&scale=4&rotate=0"))

def getbooklink(olib):
    return "http://www.openlibrary.org/books/"+olib

def getauthorlink(olib):
    return "http://www.openlibrary.org/authors/"+olib

olib=sys.argv[1]
if olib.startswith("/books/"):
    olib=olib.slice(7)
elif olib.startswith("books/"):
    olib=olib.slice(6)
leaf=sys.argv[2]

olibstream=urlopen("http://www.openlibrary.org/books/%s.json"%olib)
olibinfo=json.load(olibstream)
iaid=olibinfo["ocaid"]
if (not(iaid)):
    error ("No archive reference for %s"%olib)
authorid=olibinfo["authors"][0]["key"]
olibstream=urlopen("http://www.openlibrary.org%s.json"%authorid)
authorinfo=json.load(olibstream)

bookpath=getbookpath(iaid)

template=open(os.path.join(os.path.dirname(__file__),"proof.html"),"rt",).read()
html=getbookhtml(olib)
rewrite=string.replace(
    string.replace(
        string.replace(
            string.replace(
                string.replace(
                    string.replace(
                        string.replace(
                            string.replace(
                                string.replace(template,"%%OLIB",olib),
                                "%%LEAF",str(leaf)),
                            "%%TITLE",olibinfo["title"]),
                        "%%IMGTEMPLATE",getimageurl(iaid,bookpath)),
                    "%%BOOKLINK",getbooklink(olib)),
                "%%AUTHORLINK",getauthorlink(authorid)),
            "%%AUTHORNAME",authorinfo["name"]),
        "%%BOOKTEXT",html.body),
    "%%STYLE",html.style)

print rewrite.encode('utf-8')


