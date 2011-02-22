from gzip import GzipFile
from urllib2 import urlopen

import abbyystreams

import sys
import getopt
import os
import gzip
import string
import StringIO
import json
import cgi

ns = '{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'
page_tag = ns + 'page'
block_tag = ns + 'block'
olibid=False

fontmap={}
def getfontname(s):
    if (s in fontmap):
       return fontmap[s]
    else: return "'%s'"%s

if (os.path.exists(sys.argv[1])):
    bookid='sbook'
    if sys.argv[1].endswith('.gz'):
        f=gzip.open(sys.argv[1])
    else: f=open(sys.argv[1])
elif (sys.argv[1].startswith('http')):
    bookid='sbook'
    if sys.argv[1].endswith('.gz'):
        f=GzipFile(fileobj=urlopen(sys.argv[1]))
    else: f=urlopen(sys.argv[1])
else:
    if (sys.argv[1].startswith('OL')):
        olibstream=urlopen("http://www.openlibrary.org/books/%s.json"%sys.argv[1])
        olibinfo=json.load(olibstream)
        olibid=sys.argv[1]
        iaid=olibinfo["ocaid"]
        if (not(iaid)):
            error ("No archive reference for %s"%olibid)
    else: iaid=sys.argv[1]
    bookid=sys.argv[1]
    urlstream=urlopen("http://www.archive.org/download/%s/%s_abbyy.gz"%
                      (iaid,iaid))
    zipdata=urlstream.read()
    f=GzipFile(fileobj=StringIO.StringIO(zipdata))
    detailstream=urlopen("http://www.archive.org/details/%s?output=json"%iaid)
    details=json.load(detailstream)
    if "metadata" in details:
       metadata=details["metadata"]
       if "title" in metadata: title=string.replace(metadata["title"][0],"'","&apos;")
       if "creator" in metadata: creator=string.replace(metadata["creator"][0],"'","&apos;")

classcount=1
classmap={}
classhist={}
def xmlformat(text,format,curformat):
    global classcount
    global classmap
    global classhist
    if ((curformat) and ((not(format)) or (format!=curformat))):
       style=""
       classname=""
       if ("ff" in curformat):
       	  style=style+"font-family: "+getfontname(curformat["ff"])+";"
       if ("fs" in curformat):
       	  style=style+"font-size: "+curformat["fs"][0:-1]+"px;"
       if ("bold" in curformat):
       	  style=style+"font-weight: bold;"
       if ("italic" in curformat):
       	  style=style+"font-style: italic;"
       if style in classmap:
       	  classname=classmap[style]
	  classhist[classname]=classhist[classname]+1
       else:
          classname="abbyy%d"%classcount
	  classmap[style]=classname
	  classhist[classname]=1
	  classcount=classcount+1
       return ("<span class='%s'>"%classname)+text+"</span>"
    else: return text

def htmlhead(x,elt):
    return "<span class='abbyyheader'>"+x+"</span>"

def htmlfoot(x,elt):
    return "<span class='abbyyfooter'>"+x+"</span>"

def htmlpage(num,element):
      attribs=element.attrib
      return ("<a name='leaf%d' class='leaf' data-leafno='%d' data-leafdim='@%sx%s'/>"%
              (num,num,attribs["width"],attribs["height"]));

img_count=1
def htmlimg(elt,leafno):
  global bookid
  global img_count
  attribs=elt.attrib
  img_name="images/img%d.jpg"%img_count
  img_count=img_count+1
  return (("<img src='%s' data-dim='%s:%d@%s,%s,%s,%s'/>"%
            (img_name,bookid,leafno,
	     attribs["l"],attribs["t"],attribs["r"],attribs["b"])),
	   False)

table_count=1
def htmltable(elt,leafno):
  global bookid
  global img_count
  attribs=elt.attrib
  img_name="images/tbl%d.jpg"%img_count
  table_count=table_count+1
  return ("<img src='%s' class='table' data-dim='%s:%d@%s,%s,%s,%s'/>"%
          	(img_name,bookid,leafno,
		 attribs["l"],attribs["t"],attribs["r"],attribs["b"]))

blockcount=1
def htmlblock(element,leafno):
      global blockcount
      attribs=element.attrib
      l=int(attribs["l"])
      r=int(attribs["r"])
      b=int(attribs["b"])
      t=int(attribs["t"])
      blockname="abbyyblock%d"%blockcount
      blockcount=blockcount+1
      return ("<a name='%s' class='block' title='l%db%dx%d@%d,%d'/>"%
              (blockname,leafno,r-l,b-t,l,t));

def linehandler(elt,lineno,leafno):
  global bookid
  return ("<a name='%s/N%d/L%d' class='line'/>"%(bookid,leafno,lineno));

if "debug" in sys.argv:
    debug_arg=True
else: debug_arg=False

title=False
creator=False
metadata={}

# f = GzipFile(fileobj=urlopen(sys.argv[1]))
# f = open(sys.argv[1])

pars=[]
for par in abbyystreams.abbyytext(f, header=htmlhead, footer=htmlfoot,
    	   			     format=xmlformat,blockfn=htmlblock,
				     pagefn=htmlpage,picture=htmlimg,
				     table=htmltable,escapefn=cgi.escape,
                                  linefn=linehandler,
                                     debug=debug_arg):
    pars.append(par)

topclass=False
topscore=-1
for x in classhist:
    if not (topclass and (classhist[x]<topscore)):
       topclass=x
       topscore=classhist[x]
paraprefix="<span class='%s'>"%topclass
paracount=1

print "<?xml version='1.0' encoding='utf-8' ?>"
print "<!DOCTYPE html>"
print "<html>"
print "<head>"
print ("<meta name='ia.item' content='%s'/>"%iaid)
if olibid:
    print ("<meta name='olib.item' content='%s'/>"%olibid)

if title and creator:
   print "<title>%s by %s</title>"%(title,creator)
elif title:
   print "<title>%s</title>"%title
elif creator:
   print "<title>by %s</title>"%creator
if title:
   print "<meta name='DC.TITLE' content='%s'/>"%title
if creator:
   print "<meta name='DC.CREATOR' content='%s'/>"%creator
if "publisher" in metadata:
   print "<meta name='DC.PUBLISHER' content='%s'/>"%(metadata["publisher"][0])
if "date" in metadata:
   print "<meta name='DC.DATE' content='%s'/>"%(metadata["date"][0])
if "description" in metadata:
   print "<meta name='DC.DESCRIPTION' content='%s'/>"%(metadata["description"][0])
print "<link rel='sbook.refuri' href='http://www.archive.org/sbooks/%s/index.html'/>"%bookid
print "<style>"
print "span.abbyyheader { display: none;}"
print "span.abbyyfooter { display: none;}"
print "p.%s {} /* %d times */"%(topclass,topscore)
for x in classmap:
    print ".%s { %s } /* %d times */"%(classmap[x],x,classhist[classmap[x]])
print "</style>"
print "</head>"
print "<body>"
for par in pars:
    if par.startswith(paraprefix):
       print ("<p id='"+bookid+str(paracount)+"'"+par[5:-7]+"</p>").encode('utf-8')
       paracount=paracount+1
    elif par.startswith("<span "):
       print ("<div id='"+bookid+str(paracount)+"'"+par[5:-7]+"</div>").encode('utf-8')
       paracount=paracount+1
    else: print par.encode('utf-8') 
print "</body>"
print "</html>"

