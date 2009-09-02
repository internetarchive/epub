#!/usr/bin/python

import sys
import getopt
import re
import os
import gzip

from lxml import etree

import common

noclose=True
# noclose=False
verbose=False

def main(argv):
#     if len(argv) != 2:
#         usage()
#         sys.exit(-1)

    id = common.get_book_id()
    aby_file = gzip.open(id + '_abbyy.gz', 'rb')
    scandata = id + '.xml'

    condense_abbyy(aby_file, scandata)

def usage():
    print "Usage:"

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
        self.current_line = ''
    def pr(self, str):
        p(str, self.out)
    def start(self, tag, attrib):
        self.intag = True
        self.curtag = nons(tag)
        if tag in self.filter:
            (hints, atts_accepted) = self.filter[tag]
            # only print 'ifverbose' tags if verbose
            if not verbose and 'ifverbose' in hints:
                return
            if verbose or not 'inside' in hints:
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
            if verbose or 'indent' in hints:
#                 self.pr('\n')
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
            if not verbose and 'ifverbose' in hints:
                return
            if verbose or 'indent' in hints:
                self.depth -= 1
                self.pr(self.istr * self.depth)
            ntag = stag = nons(tag)
            if ntag in synonyms:
                ntag = synonyms[ntag];
            if stag == 'formatting' and verbose:
                self.pr(self.current_line)
            if stag == 'formatting' and not verbose:
                self.pr('\n')
            if not noclose:
                self.pr('</' + ntag + '>')
                if verbose or not 'inside' in hints:
                    self.pr('\n')
    def data(self, data):
        if self.intag and self.curtag == 'charParams':
            if data == "'":
                data = "''"
            elif data == '"':
                data = '""'
            self.current_line += data
            if verbose:
                self.pr(data + '\n')
            else:
                self.pr(data)
    def comment(self, text):
        self.pr('comment %s' % text)
    def close(self):
        pass
#        print('close')
#        return 'closed!'

# to_keep = {
#     ns+'document':(['indent'], [ 'pagesCount', 'xmlns' ]),
#     ns+'page':(['indent'], [ 'width', 'leaf' ]),
#     ns+'block':(['indent'], [ 'blockType', 'l', 'r', 't', 'b' ]),
#     ns+'region':(['indent'], [ ]),
#     ns+'rect':([ ], [ ]),
#     ns+'text':(['indent'], [ ]),
#     ns+'line':([ ], [ 'baseline', 'spacing', 'l', 'r', 't', 'b' ]),
#     ns+'par':(['indent'], [ 'startIndent', 'leftIndent', 'lineSpacing']),
#     ns+'formatting':(['inside'], [ 'ff', 'fs', 'italic', 'smallcaps' ]),
#     ns+'cell':(['indent', 'showall'], [ ]),
#     ns+'row':(['indent', 'showall'], [ ]),
#     ns+'charParams':(['indent', 'ifverbose', 'nonl'], [ 'wordStart', 'wordFromDictionary', 'wordNormal', 'wordNumeric', 'wordIdentifier', 'l', 'r', 't', 'b']),
# }

to_keep = {
    ns+'document':(['indent'], [ 'pagesCount', 'xmlns' ]),
    ns+'page':(['indent'], [ 'width', 'leaf' ]),
    ns+'block':(['indent'], [ 'blockType', 'l', 'r', 't', 'b' ]),
    ns+'region':(['indent'], [ ]),
    ns+'rect':([ 'indent' ], [ ]),
    ns+'text':(['indent'], [ ]),
    ns+'line':(['indent'], [ 'baseline', 'spacing', 'l', 'r', 't', 'b' ]),
    ns+'par':(['indent'], [ 'startIndent', 'leftIndent', 'lineSpacing']),
    ns+'formatting':(['indent'], [ 'ff', 'fs', 'italic', 'smallcaps' ]),
    ns+'cell':(['indent', 'showall'], [ ]),
    ns+'row':(['indent', 'showall'], [ ]),
    ns+'charParams':(['indent', 'ifverbose', 'nonl'], [ 'wordStart', 'wordFromDictionary', 'wordNormal', 'wordNumeric', 'wordIdentifier', 'l', 'r', 't', 'b']),
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

def condense_abbyy(xml, outfile='outfile.txt'):
    # remove_blank_text?
    try:
#         out = open(outfile, 'w')
        out = sys.stdout
        parser = etree.XMLParser(resolve_entities=False, target=FilterTarget(to_keep, synonyms, out))
        tree = etree.parse(xml, parser)
    finally:
        pass
#         out.close()
#     print tree
    for err in parser.error_log:
        e('%s - %s:%s' % (err.message, err.line, err.column))

if __name__ == '__main__':
    main(sys.argv[1:])

