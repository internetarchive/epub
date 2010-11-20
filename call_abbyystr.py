from gzip import GzipFile
from urllib2 import urlopen

import abbyystreams

import sys
import getopt
import os
import gzip
import StringIO

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
else:
    header_arg=False
    footer_arg=False
    content_label=False

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
                                  debug=debug_arg):
    if content_label:
        print "Content:",par.encode('utf-8')
    else: print par.encode('utf-8')
