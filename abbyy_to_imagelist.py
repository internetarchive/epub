#!/usr/bin/python

import sys
import getopt
import re
import os
import gzip

from lxml import etree


from debug import debug, debugging, assert_d

ns='{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'

def main(argv):
    aby_file = gzip.open(argv[0], 'rb')
    find_images(aby_file)

def p(s, out):
    try:
        out.write(s.encode('utf-8'))
    except UnicodeEncodeError:
        pass

def e(s):
    try:
        sys.stderr.write(s.encode('utf-8'))
    except UnicodeEncodeError:
        pass

class FilterTarget:
    def __init__(self, out=sys.stdout):
        self.text = ''
        self.out = out
        self.leafno = 0
    def start(self, tag, attrib):
        if tag == ns + 'block' and attrib['blockType'] == 'Picture':
            print 'saw pic on leafno - ' + str(self.leafno)
            print ('coords l %s r %s t %s b %s' %
                   (attrib['l'], attrib['r'],
                   attrib['t'], attrib['b']))
    def end(self, tag):
        if tag == ns + 'page':
            self.leafno += 1
    def close(self):
        pass


def find_images(xml): 
    try:
        out = sys.stdout
        ft = FilterTarget(out)
        parser = etree.XMLParser(resolve_entities=False,
                                 target=ft)
        tree = etree.parse(xml, parser)
    finally:
        pass
    for err in parser.error_log:
        e('%s - %s:%s' % (err.message, err.line, err.column))

if __name__ == '__main__':
    main(sys.argv[1:])
