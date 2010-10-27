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

ns = '{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'
page_tag = ns + 'page'
block_tag = ns + 'block'

fontmap={}
def getfontname(s):
    if (s in fontmap):
       return fontmap[s]
    else: return string.replace(s," ","")

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
      return ("<a name=\"page%d\" class=\"page\" data-pageno=\"%d\" data-size=\"%sx%s\"/>"%
              (num,num,attribs["width"],attribs["height"]));

blockcount=1
def htmlblock(element):
      global blockcount
      attribs=element.attrib
      l=int(attribs["l"])
      r=int(attribs["r"])
      b=int(attribs["b"])
      t=int(attribs["t"])
      blockname="abbyyblock%d"%blockcount
      blockcount=blockcount+1
      return ("<a name=\"%s\" class=\"block\" title=\"%dx%d+%d+%d\"/>"%(blockname,r-l,b-t,l,t));

if "debug" in sys.argv:
    debug_arg=True
else: debug_arg=False

title=False
creator=False

if (os.path.exists(sys.argv[1])):
    if sys.argv[1].endswith('.gz'):
        f=gzip.open(sys.argv[1])
    else: f=open(sys.argv[1])
elif (sys.argv[1].startswith('http')):
    if sys.argv[1].endswith('.gz'):
        f=GzipFile(fileobj=urlopen(sys.argv[1]))
    else: f=urlopen(sys.argv[1])
else:
    urlstream=urlopen("http://www.archive.org/download/%s/%s_abbyy.gz"%
                      (sys.argv[1],sys.argv[1]))
    zipdata=urlstream.read()
    f=GzipFile(fileobj=StringIO.StringIO(zipdata))
    detailstream=urlopen("http://www.archive.org/details/%s?output=json"%sys.argv[1])
    details=json.load(detailstream)
    if "metadata" in details:
       metadata=details["metadata"]
       if "title" in metadata: title=metadata["title"][0]
       if "creator" in metadata: creator=metadata["creator"][0]
    
    
# f = GzipFile(fileobj=urlopen(sys.argv[1]))
# f = open(sys.argv[1])

pars=[]
for par in abbyystreams.abbyytext(f, header=htmlhead, footer=htmlfoot,
    	   			     format=xmlformat,blockfn=htmlblock,
				     pagefn=htmlpage,
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

print "<html>"
print "<head>"
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
       print ("<p id='SBOOK"+str(paracount)+"'"+par[5:-7]+"</p>").encode('utf-8')
       paracount=paracount+1
    elif par.startswith("<span "):
       print ("<div id='SBOOK"+str(paracount)+"'"+par[5:-7]+"</div>").encode('utf-8')
       paracount=paracount+1
    else: print par.encode('utf-8') 
print "</body>"
print "</html>"

