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
    lura2hocr(aby_file)


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

def r(s, rfactor=8):
    n = int(s)
    n = n / rfactor
    return str(n)

class FilterTarget:
    def __init__(self, out=sys.stdout):
        self.text = ''
        self.out = out
        self.leafno = 0
    def pr(self, str):
        p(str, self.out)
    def start(self, tag, attrib):
        if tag == ns + 'page':
            self.text += '<div class="ocr_page" '
            self.text += ('title="bbox 0 0 %s %s; image %s">' %
                          (r(attrib['width']),
                           r(attrib['height']),
                           'images/image' + str(self.leafno).zfill(2) + '.jpg'))
            self.pr(self.text)
            self.text = ''
            # <div class="ocr_page" title="bbox 0 0 896 1450; image 002b.png">
            # <page width="2136" height="3260"
            # resolution="400" originalCoords="true">
        elif tag == ns + 'text':
            self.text += '<div'
            if 'backgroundColor' in attrib:
                self.text += (' style="background-color: #%s"'
                              % abbycolor2hexcolor(attrib['backgroundColor']))
            self.text += '>'
            self.pr(self.text)
            self.text = ''
        elif tag == ns + 'par':
            self.text += '<p'
            if 'align' in attrib:
                self.text += ' style="text-align: %s"' % attrib['align'].lower()
            self.text += '>'
            self.pr(self.text)
            self.text = ''
        elif tag == ns + 'line':
            self.text += '<span class="ocr_line" '
            self.text += ('title="bbox %s %s %s %s">' %
                          (r(attrib['l']), r(attrib['t']),
                           r(attrib['r']), r(attrib['b'])))
            self.pr(self.text)
            self.text = ''
            # <line baseline="99" l="149" t="56" r="1989" b="105">
            # <span class="ocr_line" title="bbox 24 566 913 608">blah</span>
        elif tag == ns + 'formatting':
            newa = {}
            if 'ff' in attrib:
                newa['font-family'] = attrib['ff']
            if 'fs' in attrib:
                newa['font-size'] = attrib['fs'][:-1] + 'pt'
            if 'italic' in attrib:
                newa['font-style'] = 'italic'
            if 'bold' in attrib:
                newa['font-weight'] = 'bold'
            if 'smallcaps' in attrib:
                newa['font-variant'] = 'small-caps'
            if 'color' in attrib:
                newa['color'] = '#' + abbycolor2hexcolor(attrib['color'])
            self.text += '<span style="'
            for k, v in newa.items():
                self.text += k + ': ' + v + '; '
            self.text += '">'
            self.pr(self.text)
            self.text = ''

    def end(self, tag):
        if tag == ns + 'page':
            self.text += '</div>'
            self.leafno += 1
        elif tag == ns + 'text':
            self.text += '</div>'
        elif tag == ns + 'par':
            self.text += '</p>\n'
        elif tag == ns + 'line':
            self.text += '</span><br />'
        elif tag == ns + 'formatting':
            self.text += '</span>'
        self.pr(self.text)
        self.text = ''
    def data(self, data):
        if data == '"':
            data = '&quot;'
        self.pr(data)    

    # def comment(self, text):
    #     self.pr('comment %s' % text)
    def close(self):
        pass


def abbycolor2hexcolor(color):
    color = hex(int(color))[2:].zfill(6)
    color = color[4:5] + color[2:3] + color[0:1]
    return color


def lura2hocr(xml): 
    try:
        out = sys.stdout
        parser = etree.XMLParser(resolve_entities=False,
                                 target=FilterTarget(out))
        p('<html style=""><head><meta http-equiv="content-type" content="text/html; charset=ISO-8859-1"><meta content="ocr_line ocr_page" name="ocr-capabilities"><meta content="en" name="ocr-langs"><meta content="Latn" name="ocr-scripts"><meta content="" name="ocr-microformats"><title>OCR Output</title></head><body>\n', out)

        tree = etree.parse(xml, parser)
        p('</body></html>\n', out)

        
    finally:
        pass
    for err in parser.error_log:
        e('%s - %s:%s' % (err.message, err.line, err.column))

if __name__ == '__main__':
    main(sys.argv[1:])
