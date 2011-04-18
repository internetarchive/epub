from urllib2 import urlopen, HTTPError
from urlparse import urlparse

import sys
import os
import string
import StringIO
import json
import cgi
import re

def getbookpath(iaid):
    tmp_url="http://www.archive.org/download/%s/%s_meta.xml"%(iaid,iaid)
    urlstream=urlopen(tmp_url)
    real_url=urlstream.geturl()
    urlstream.close()
    return real_url

def getimageurl(iaid,bookpath):
    parsed=urlparse(bookpath)
    return (("http://"+parsed.netloc+"/BookReader/BookReader.php")+
            ("?zip="+parsed.path+"_jp2.zip")+
            ("&file="+iaid+"/"+iaid+"_%%%%"+".jp2")+
            ("&scale=4&rotate=0"))

def getbooklink(olib):
    return "http://www.openlibrary.org/books/"+olib

def getauthorlink(olib):
    return "http://www.openlibrary.org/authors/"+olib

olib="OL2588416M"
leaf=42
if (cgi.FieldStorage):
    form=cgi.FieldStorage()
    if ("olib" in form):
        olib=form["olib"]
    if ("leaf" in form):
        leaf=int(form["leaf"])

olibstream=urlopen("http://www.openlibrary.org/books/%s.json"%olib)
olibinfo=json.load(olibstream)
iaid=olibinfo["ocaid"]
if (not(iaid)):
    error ("No archive reference for %s"%olibid)
authorid=olibinfo["authors"][0]["key"]
olibstream=urlopen("http://www.openlibrary.org%s.json"%authorid)
authorinfo=json.load(olibstream)

bookpath=getbookpath(olib)

template=open("proto.html").read()
rewrite=string.replace(
    string.replace(
        string.replace(
            string.replace(
                string.replace(
                    string.replace(
                        string.replace(template,"%%OLIB",olib),
                        "%%LEAF",str(leaf)),
                    "%%TTILE",olibinfo["title"]),
                "%%IMGTEMPLATE",getimageurl(olib,bookpath)),
            "%%BOOKLINK",getbooklink(olib)),
        "%%AUTHORLINK",getauthorlink(authorid)),
    "%%AUTHORNAME",authorinfo["name"])

print "Content-type: text/html"
print
print rewrite

