from gzip import GzipFile
from urllib2 import urlopen

import abbyystreams

import sys
import getopt
import os
import gzip
import string
import StringIO

ns = '{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'
page_tag = ns + 'page'
block_tag = ns + 'block'

fontmap={}

def getfontname(s):
    if (s in fontmap):
       return fontmap[s]
    else: return "\"%s\""%s

def xmlhead(x,elt):
    return "<header>"+x+"</header>"
def xmlfoot(x,elt):
    return "<footer>"+x+"</footer>"
def xmlformat(text,format,curformat):
    if ((curformat) and ((not(format)) or (format!=curformat))):
       style=""
       if ("ff" in curformat):
       	  style=style+"font-family: "+getfontname(curformat["ff"])+";"
       if ("fs" in curformat):
       	  style=style+"font-size: "+curformat["fs"][0:-1]+"px;"
       if ("bold" in curformat):
       	  style=style+"font-weight: bold;"
       if ("italic" in curformat):
       	  style=style+"font-style: italic;"
       return ("<span style='%s'>"%style)+text+"</span>"
    else: return text
def xmlpage(num,element):
    attribs=element.attrib
    return ("<page num=\"%d\" width=\"%s\" height=\"%s\"/>"%
    	    	      (num,attribs["width"],attribs["height"]));
def xmlblock(element):
    attribs=element.attrib
    return ("<block left=\"%s\" top=\"%s\" right=\"%s\" bottom=\"%s\"/>"%
    	    	       (attribs["l"],attribs["t"],attribs["r"],attribs["b"]));

def htmlhead(x,elt):
    return "<span class='header'>"+x+"</span>"
def htmlfoot(x,elt):
    return "<span class='footer'>"+x+"</span>"
def htmlpage(num,element):
      attribs=element.attrib
      return ("<a name=\"page%d\" class=\"page\" data-pageno=\"%d\" data-size=\"%sx%s\"/>"%
              (num,num,attribs["width"],attribs["height"]));
def htmlblock(element):
      attribs=element.attrib
      l=int(attribs["l"])
      r=int(attribs["r"])
      b=int(attribs["b"])
      t=int(attribs["t"])
      return ("<a class=\"block\" title=\"%dx%d+%d+%d\"/>"%(r-l,b-t,l,t));

def printhead(x, y):
    print 'Header: ' + x.encode('utf-8')
    return False

def printfoot(x, y):
    print 'Footer: ' + x.encode('utf-8')
    return False

if "debug" in sys.argv:
    debug_arg=True
else: debug_arg=False

if "label" in sys.argv:
    header_arg=printhead
    footer_arg=printfoot
    content_label=True
    format_arg=False
    layout_arg=False
    page_arg=False
    block_arg=False
elif "xml" in sys.argv:
    header_arg=xmlhead
    footer_arg=xmlfoot
    content_label=False
    format_arg=xmlformat
    layout_arg=False
    page_arg=xmlpage
    block_arg=xmlblock
elif "html" in sys.argv:
    header_arg=htmlhead
    footer_arg=htmlfoot
    content_label=False
    format_arg=xmlformat
    layout_arg=False
    page_arg=htmlpage
    block_arg=htmlblock
else:
    header_arg=False
    footer_arg=False
    content_label=False
    format_arg=False
    layout_arg=False
    page_arg=False
    block_arg=False

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
    
# f = GzipFile(fileobj=urlopen(sys.argv[1]))
# f = open(sys.argv[1])

for par in abbyystreams.abbyytext(f, header=header_arg, footer=footer_arg,
    	   			     format=format_arg,layout=layout_arg,
				     blockfn=block_arg,pagefn=page_arg,
                                     debug=debug_arg):
    if content_label:
        print "Content:",par.encode('utf-8')
    else: print par.encode('utf-8')
