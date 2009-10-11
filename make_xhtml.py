#!/usr/bin/python

import sys
import getopt
import re

try:
    from lxml import etree
except ImportError:
    sys.path.append('/petabox/sw/lib/lxml/lib/python2.5/site-packages') 
    from lxml import etree
from lxml import objectify

from debug import debug, debugging, assert_d

def usage():
    print 'usage: make_xhtml.py abbyy.xml scandata.xml outfile.xml'

def main(argv):
    if len(argv) != 3:
        usage()
        sys.exit(-1)
    make_xhtml(argv[0], argv[1], argv[2])

out = sys.stdout

def pr_out(s):
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

def recursive_dict(element):
     return element.tag, \
            dict(map(recursive_dict, element)) or element.text

abbyyns="{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}"


def include_page(page):
    add = page.find('addToAccessFormats')
    if add is not None and add.text == 'true':
        return True
    else:
        return False




def build_html(context, scandata, out):
    print etree.tostring(scandata, pretty_print=True)

    bookData = scandata.find('bookData')
    scanLog = scandata.find('scanLog')
    scandata_pages = scandata.xpath('/book/pageData/page')

    for page in scandata_pages:
        result = include_page(page)
        print result, page.get('leafNum')

    def CLASS(*args): # class is a reserved word in Python
        return {"class":' '.join(args)}
    from lxml.builder import E
    html = E.html(
        E.head( 
           E.title("This is a sample document"),
           E.meta(name='generator', content='abbyy to xhtml tool'),
           E.link(rel="stylesheet",
                  href="css/main.css",
                  type="text/css"),
           E.meta({'http-equiv':"Content-Type"},
                  content="application/xhtml+xml; charset=utf-8")
        ), 
        E.body(
          E.div(CLASS('body'))
        ),
        xmlns="http://www.w3.org/1999/xhtml",
    )

    bdiv = html.xpath('/html/body/div')[0]
    for action, elem in context:
        out.write(etree.tostring(elem, method="text", encoding="UTF-8") +'\n')
        out.write("%s - %s" % (action, elem.tag) + '\n')
        if (action == 'end'):
            elem.clear()
    htmldoc = etree.ElementTree(html);
    return htmldoc

def scandata_asserts(scandata):
    # assert: len == 0
    bookData = scandata.xpath('/book/bookData')
    scanLog = scandata.xpath('/book/scanLog')
    # does leafNum always monotonicall increase?
    # start at 0?
    # NOT NECESSARILY
    pass

def try_objectify(scandata_file):
    tree = objectify.parse(scandata_file)
    debug()

def make_xhtml(xml, scandata_file, outfile='tmp_tmp_out.txt'):
    try:
        global out
        out = open(outfile, 'w')
        events = ("start", "end")
        try_objectify(scandata_file)
        
        scandata = etree.parse(scandata_file)
        scandata_asserts(scandata)
        context = etree.iterparse(xml, events=events, tag=abbyyns+'page')
        tree = build_html(context, scandata, out)
        sys.stdout.write(etree.tostring(tree,
                                        pretty_print=True,
                                        xml_declaration=True))
        
    finally:
        out.close()
