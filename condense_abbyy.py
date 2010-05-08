#!/usr/bin/python

import sys
import getopt
import re
import os
import gzip

from lxml import etree

# showchars=False
showchars=True

from debug import debug, debugging, assert_d

ns='{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'

def main(argv):
    if len(argv) != 2:
        usage()
        sys.exit(-1)

    aby_file = gzip.open(sys.argv[1])

    if not showchars:
        del to_keep[ns+'charParams']
        (fmt_hints, fmt_attrs) = to_keep[ns+'formatting']
        fmt_hints.append('nonl')

    condense_abbyy(aby_file)

def usage():
    print "Usage: python condense_abbyy.py file_abbyy.gz > output.txt"

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

def nons(tag):
    return re.sub('{.*}', '', tag)

class FilterTarget:
    istr = '  '
    def __init__(self, filter, synonyms, out=sys.stdout):
        self.filter = filter
        self.synonyms = synonyms
        self.tree = None
        self.intag = False
        self.curtag = None
        self.depth = 0
        self.leaf = 0
        self.out = out
        self.current_line = ''
    def pr(self, str):
        p(str, self.out)
    def start(self, tag, attrib):
        self.intag = True
        self.curtag = nons(tag)
        if tag in self.filter:
            (hints, atts_accepted) = self.filter[tag]
            self.pr(self.istr * self.depth)
            ntag = nons(tag)
            if ntag == 'page':
                attrib['leaf'] = str(self.leaf)
                self.leaf += 1
            if ntag == 'formatting':
                self.current_line = ''
            if ntag in self.synonyms:
                ntag = self.synonyms[ntag];
            self.pr('<' + ntag)
            if not 'showall' in hints:
                for attname in atts_accepted:
                    if attname in attrib:
                        nattname = attname
                        nattval = attrib[attname]
                        if nattval in synonyms:
                            nattval = synonyms[nattval]
                        if attname in synonyms:
                            nattname = synonyms[attname]
                        self.pr(' ' + nattname + '=' + nattval)
            else:
                for attname in attrib:
                    nattname = attname
                    if attname in synonyms:
                        nattname = synonyms[attname]
                    self.pr(' ' + nattname + '=' + attrib[attname])
            self.pr('>')
            if not 'nonl' in hints:
                self.pr('\n')
            self.depth += 1
        elif self.curtag == 'charParams':
            pass
        else:
            e('skipped: ' + self.curtag + '\n')
    def end(self, tag):
        self.intag = False
        if tag in self.filter:
            (hints, atts_accepted) = self.filter[tag]
            self.depth -= 1
            ntag = stag = nons(tag)
            if ntag in synonyms:
                ntag = synonyms[ntag];
            if stag == 'formatting':
                if not showchars:
                    self.pr(' - ')
                self.pr(self.current_line)
                self.pr('\n')
    def data(self, data):
        if self.intag and self.curtag == 'charParams':
            if data == "'":
                data = "''"
            elif data == '"':
                data = '""'
            self.current_line += data
            if showchars:
                self.pr(data + '\n')
    def comment(self, text):
        self.pr('comment %s' % text)
    def close(self):
        pass

to_keep = {
    ns+'document':(['indent'], [ 'pagesCount', 'xmlns' ]),
    ns+'page':(['indent'], [ 'width', 'height', 'resolution', 'originalCoords', 'leaf' ]),
    ns+'block':(['indent'], [ 'blockType', 'l', 'r', 't', 'b' ]),
    ns+'region':(['indent'], [ ]),
    ns+'rect':([ 'indent' ], [ 'l', 'r', 't', 'b' ]),
    ns+'text':(['indent'], [ 'backgroundColor', 'inverted']),
    ns+'line':(['indent'], [ 'baseline', 'spacing', 'l', 'r', 't', 'b' ]),
    ns+'par':(['indent'], [ 'startIndent', 'leftIndent', 'rightIndent', 'lineSpacing', 'align']),
    ns+'formatting':(['indent'], [ 'ff', 'fs', 'italic', 'smallcaps' ]),
    ns+'cell':(['indent', 'showall'], [ ]),
    ns+'row':(['indent', 'showall'], [ ]),
    ns+'charParams':(['indent', 'ifverbose', 'nonl'],
                     [ 'wordStart', 'wordFromDictionary', 'wordNormal',
                       'wordNumeric', 'wordIdentifier',
                       'suspicious',
                       'l', 'r', 't', 'b']),
}

synonyms = {
    'formatting':'fmt',
    'baseline':'bl',
    'charParams':'cp',
    'wordStart':'wStart',
    'wordFromDictionary':'inDict',
    'wordNormal':'wNorm',
    'wordNumeric':'wNum',
    'wordIdentifier':'wIdent',
    'true':'T',
    'false':'F',
}

def condense_abbyy(xml):
    try:
        out = sys.stdout
        parser = etree.XMLParser(resolve_entities=False, target=FilterTarget(to_keep, synonyms, out))
        tree = etree.parse(xml, parser)
    finally:
        pass
    for err in parser.error_log:
        e('%s - %s:%s' % (err.message, err.line, err.column))

if __name__ == '__main__':
    main(sys.argv[1:])

