from gzip import GzipFile
from zipfile import ZipFile
from urllib2 import urlopen, HTTPError

import abbyyhtml

import sys
import getopt
import os
import gzip
import string
import StringIO
import json
import cgi

import iarchive

for line in abbyyhtml.getblocks(open(sys.argv[1])):
    print line.encode('utf-8')

