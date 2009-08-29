#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import getopt
import re
import os
import gzip
import zipfile

from lxml import etree
from lxml import objectify
from lxml import html
import lxml

import epub

# remove me for faster execution
debugme = True
if debugme:
    from  pydbgr.api import debug
else:
    def debug():
        pass

aby_ns="{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}"
def generate_epub_content(book_id):
    scandata = objectify.parse(book_id + '_scandata.xml').getroot()
    metadata = objectify.parse(book_id + '_meta.xml').getroot()
    aby_file = gzip.open(book_id + '_abbyy.gz', 'rb')
    context = etree.iterparse(aby_file,  tag=aby_ns+'page', resolve_entities=False)
    tree = build_html(context, scandata, metadata)
    yield tree

def include_page(page):
    add = page.find('addToAccessFormats')
    if add is not None and add.text == 'true':
        return True
    else:
        return False

def build_html(context, scandata, metadata):
    bookData = scandata.find('bookData')
    scanLog = scandata.find('scanLog')
    scandata_pages = scandata.xpath('/book/pageData/page')

    def CLASS(*args): # class is a reserved word in Python
        return {"class":' '.join(args)}
    from lxml.builder import E
    html = E.html(
        E.head( 
           E.title('test title'), # metadata.title
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
    i = 0
    for event, page in context:
        for block in page:
            if block.get('blockType') == 'Text':
                pass
            else:
                pass
            for el in block:
                if el.tag == aby_ns+'region':
                    for rect in el:
                        pass
                elif el.tag == aby_ns+'text':
                    for par in el:
                        lines = []
                        for line in par:
                            lines.append(etree.tostring(line, method='text', encoding=unicode))
                        bdiv.append(E.p(' '.join(lines)))
#                         par_coords = box_from_par(par)
#                         if par_coords is not None:
#                             pass
#                         for line in par:
#                             for fmt in line:
#                                 for cp in fmt:
#                                     assert_d(cp.tag == aby_ns+'charParams')
#                                     draw.text((int(cp.get('l')),
#                                                int(cp.get('b'))),
#                                               cp.text.encode('utf-8'),
#                                               font=f,
#                                               fill=color.white)
                   
                elif (el.tag == aby_ns+'row'):
                    pass
                else:
                    print('unexpected tag type' + el.tag)
                    sys.exit(-1)
        page.clear()

    htmldoc = etree.ElementTree(html);
    return htmldoc
