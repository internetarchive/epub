#!/usr/bin/python

import sys
import getopt
import re

from lxml import etree

def main(argv):
    condense_abbyy(argv[0], argv[1])

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

ns='{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'
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
        self.leaf = 1
        self.out = out
    def pr(self, str):
        p(str, self.out)
    def start(self, tag, attrib):
        self.intag = True
        self.curtag = nons(tag)
        if tag in self.filter:
            (hints, atts_accepted) = self.filter[tag]
            if not 'inside' in hints:
                self.pr(self.istr * self.depth)
            ntag = nons(tag)
            if ntag == 'page':
                attrib['leaf'] = str(self.leaf)
                self.leaf += 1
            if ntag in self.synonyms:
                ntag = self.synonyms[ntag];
            self.pr('<' + ntag)
            if not 'showall' in hints:
                for attname in atts_accepted:
                    if attname in attrib:
                        nattname = attname
                        if attname in synonyms:
                            nattname = synonyms[attname]
                        self.pr(' ' + nattname + '=' + attrib[attname])
            else:
                for attname in attrib:
                    nattname = attname
                    if attname in synonyms:
                        nattname = synonyms[attname]
                    self.pr(' ' + nattname + '=' + attrib[attname])
            self.pr('>')
            if 'indent' in hints:
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
            if 'indent' in hints:
                self.depth -= 1
                self.pr(self.istr * self.depth)
            ntag = nons(tag)
            if ntag in synonyms:
                ntag = synonyms[ntag];
            self.pr('</' + ntag + '>')
            if not 'inside' in hints:
                self.pr('\n')
    def data(self, data):
        if self.intag and self.curtag == 'charParams':
            if data == "'":
                data = "''"
            elif data == '"':
                data = '""'
            self.pr(data)
    def comment(self, text):
        self.pr('comment %s' % text)
    def close(self):
        pass
#        print('close')
#        return 'closed!'

to_keep = {
    ns+'document' : (['indent'], [ 'pagesCount', 'xmlns' ]),
    ns+'page' : (['indent'], [ 'width', 'leaf' ]),
    ns+'block' : (['indent'], [ 'blockType', 'l', 'r', 't', 'b' ]),
    ns+'region' : (['indent'], [ ]),
    ns+'rect' : ([ ], [ ]),
    ns+'text' : (['indent'], [ ]),
    ns+'line' : ([ ], [ 'baseline', 'spacing', 'l', 'r', 't', 'b' ]),
    ns+'par' : (['indent'], [ 'startIndent', 'leftIndent', 'lineSpacing']),
    ns+'formatting' : (['inside'], [ 'fs' ]),
    ns+'cell' : (['indent', 'showall'], [ ]),
    ns+'row' : (['indent', 'showall'], [ ]),
}

synonyms = {
    'formatting' : 'fmt',
    'baseline' : 'bl',
}

def condense_abbyy(xml, outfile='outfile.txt'):
    # remove_blank_text?
    try:
        out = open(outfile, 'w')
        parser = etree.XMLParser(resolve_entities=False, target=FilterTarget(to_keep, synonyms, out))
        tree = etree.parse(xml, parser)
    finally:
        out.close()
#     print tree
    for err in parser.error_log:
        e('%s - %s:%s' % (err.message, err.line, err.column))

if __name__ == '__main__':
    main(sys.argv[1:])

