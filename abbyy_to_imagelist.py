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
    import optparse
    parser = optparse.OptionParser(usage='usage: %prog [options] '
                                   'inputfile_abbyy.gz',
                                   description='Get image coordinate data '
                                   'from abbyy.')
    parser.add_option('--output',
                      choices=['json', 'xml'],
                      default='json',
                      help='Output format - json or xml.  Image coordinates in the json format are [left, top, right, bottom]')
    parser.add_option('--callback',
                      action='store',
                      help='Wrap json result in supplied callback fn')
    opts, args = parser.parse_args(argv)

    if len(args) != 1:
        parser.error('Please specify exactly one abbyy.gz file as input.')
    if opts.callback is not None:
        import re
        p = re.compile('^[a-z0-9_\[\]\.]+$')
        if p.match(opts.callback) is None:
            parser.error('callback argument must be composed of a-z, 0-9, . '
                         'and [ ].')
            
    aby_file = gzip.open(args[0], 'rb')
    find_images(aby_file, opts)

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
    def __init__(self):
        self.leafno = 0
        self.pages = {}
    def start(self, tag, attrib):
        if tag == ns + 'block' and attrib['blockType'] == 'Picture':
            if not str(self.leafno) in self.pages:
                self.pages[str(self.leafno)] = []
            self.pages[str(self.leafno)].append([ int(attrib['l']),
                                                  int(attrib['t']),
                                                  int(attrib['r']),
                                                  int(attrib['b']) ])
            # print 'saw pic on leafno - ' + str(self.leafno)
            # print ('coords l %s r %s t %s b %s' %
            #        (attrib['l'], attrib['r'],
            #        attrib['t'], attrib['b']))
    def end(self, tag):
        if tag == ns + 'page':
            self.leafno += 1
    def close(self):
        pass


def find_images(xml, opts): 
    try:
        ft = FilterTarget()
        parser = etree.XMLParser(resolve_entities=False,
                                 target=ft)
        tree = etree.parse(xml, parser)
        pages = ft.pages
        keys = pages.keys()
        keys.sort(lambda x, y: 1 if int(x) > int(y) else -1)

        if opts.output == 'xml':
            write_xml(keys, pages)
        else:
            write_json(keys, pages, opts.callback)
    finally:
        pass
    for err in parser.error_log:
        e('%s - %s:%s' % (err.message, err.line, err.column))

def write_json(keys, pages, callback):
    if callback is not None:
        sys.stdout.write(callback + '(')
    sys.stdout.write('{')
    first = True
    for key in keys:
        if not first:
            sys.stdout.write(', ')
        first = False
        sys.stdout.write('"' + key + '":')
        sys.stdout.write(str(pages[key]))
    sys.stdout.write('}')
    if callback is not None:
        sys.stdout.write(')')

def write_xml(keys, pages):
    sys.stdout.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    sys.stdout.write('<PictureList>\n')
    for key in keys:
        sys.stdout.write('  <Page leafno=' + key + '>\n')
        for pic_coords in pages[key]:
            sys.stdout.write('    <Picture'
                             ' l=' + str(pic_coords[0]) +
                             ' t=' + str(pic_coords[1]) +
                             ' r=' + str(pic_coords[2]) +
                             ' b=' + str(pic_coords[3]) +
                             ' />\n')
        sys.stdout.write('  </Page>\n')
    sys.stdout.write('</PictureList>\n')
    pass

    



if __name__ == '__main__':
    main(sys.argv[1:])
