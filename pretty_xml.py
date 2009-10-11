#!/usr/bin/python

import sys

try:
    from lxml import etree
except ImportError:
    sys.path.append('/petabox/sw/lib/lxml/lib/python2.5/site-packages') 
    from lxml import etree
from lxml import objectify

from debug import debug, debugging, assert_d

def usage():
    print 'usage: pretty_xml.py ugly.xml'

def main(argv):
    if len(argv) != 1:
        usage()
        sys.exit(-1)
    print_pretty(argv[0])

def print_pretty(xmlfile):
    xml = etree.parse(xmlfile)
    print etree.tostring(xml, pretty_print=True)

if __name__ == '__main__':
    main(sys.argv[1:])

