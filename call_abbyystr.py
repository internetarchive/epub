from gzip import GzipFile
from urllib import urlopen

import abbyystreams


import sys

import gzip

f = gzip.open(sys.argv[1])

# f = GzipFile(fileobj=urlopen(sys.argv[1]))
# f = open(sys.argv[1])

def printit(x, y):
    print 'Header: ' + x.encode('utf-8')
    return False

def printfoot(x, y):
    print 'Footer: ' + x.encode('utf-8')
    return False


for par in abbyystreams.abbyytext(f, header=printit, footer=printfoot, debug=True):
# for par in abbyystreams.abbyytext(f, header=printit, footer=printfoot, debug=False):
    print par.encode('utf-8')
    print
