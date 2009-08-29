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
import process_abbyy

# remove me for faster execution
debugme = True
if debugme:
    from  pydbgr.api import debug
else:
    def debug():
        pass

def main(argv):
    book_id = get_book_id()
    z = zipfile.ZipFile(book_id + '.epub', 'w')
    add_to_zip(z, 'mimetype', 'application/epub+zip', deflate=False)

    tree = epub.make_container_info()
    add_to_zip(z, 'META-INF/container.xml', tree_to_str(tree))

    for content_info in process_abbyy.generate_epub_content(book_id):
        tree = content_info
        add_to_zip(z, 'OEBPS/book.html', tree_to_str(tree))

    tree = epub.make_opf(meta_info_items,
                         manifest_items,
                         spine_items,
                         guide_items);
    add_to_zip(z, 'OEBPS/content.opf', tree_to_str(tree))

    tree = epub.make_ncx(navpoints);
    add_to_zip(z, 'OEBPS/toc.ncx', tree_to_str(tree))

    z.close()

# OPF
manifest_items = [
    { 'id' : 'ncx', 'href' : 'toc.ncx', 'media-type' : 'application/x-dtbncx+xml' },
#     { 'id' : 'cover', 'href' : 'title.html', 'media-type' : 'application/xhtml+xml' },
    { 'id' : 'book', 'href' : 'book.html', 'media-type' : 'application/xhtml+xml' },

#     { 'id' : 'ncx', 'href' : 'toc.ncx', 'media-type' : 'text/html' },
#     { 'id' : 'cover', 'href' : 'title.html', 'media-type' : 'application/xhtml+xml' },
#     { 'id' : 'content', 'href' : 'content.html', 'media-type' : 'application/xhtml+xml' },
#     { 'id' : 'cover-image', 'href' : 'images/cover.png', 'media-type' : 'image/png' },
#     { 'id' : 'css', 'href' : 'stylesheet.css', 'media-type' : 'text/css' },
    ]
spine_items = [
   { 'idref' : 'book' }
#    { 'idref' : 'cover', 'linear' : 'no' },
#    { 'idref' : 'content' }
]
guide_items = [
#    { 'href' : 'title.html', 'type' : 'cover', 'title' : 'cover' }
]
dc = 'http://purl.org/dc/elements/1.1/'
dcb = '{' + dc + '}'
meta_info_items = [
    { 'item':dcb+'title', 'text':'book title here' },
    { 'item':dcb+'creator', 'text':'book creator here' },
    { 'item':dcb+'identifier', 'text':'test id', 'atts':{ 'id':'bookid' } },
    { 'item':dcb+'language', 'text':'en-US' },
    { 'item':'meta', 'atts':{ 'name':'cover', 'content':'cover-image' } }
]


# NCX
navpoints = [
    { 'id' : 'navpoint-1', 'playOrder' : '1', 'text' : 'Book', 'content' : 'book.html' },
#     { 'id' : 'navpoint-1', 'playOrder' : '1', 'text' : 'Book Cover', 'content' : 'title.html' },
#     { 'id' : 'navpoint-2', 'playOrder' : '2', 'text' : 'Contents', 'content' : 'content.html' },
    ]


def get_book_id():
    files=os.listdir(".")
    #ignore files starting with '.' using list comprehension
    files=[filename for filename in files if filename[0] != '.']
    for fname in files:
        if re.match('.*_abbyy.gz$', fname):
            return re.sub('_abbyy.gz$', '', fname)
    print 'couldn''t get book id'
    debug()

def usage():
#    print 'usage: abbyy_to_epub.py book_id abbyy.xml scandata.xml book_id'
    print 'usage: abbyy_to_epub.py'

def add_to_zip(z, path, s, deflate=True):
    info = zipfile.ZipInfo(path)
    info.compress_type = zipfile.ZIP_DEFLATED if deflate else zipfile.ZIP_STORED
    info.external_attr = 0666 << 16L # fix access
    info.date_time = (2009, 12, 25, 0, 0, 0)
    z.writestr(info, s)

def tree_to_str(tree):
    return etree.tostring(tree,
                          pretty_print=True,
                          xml_declaration=True,
                          encoding='utf-8')

if __name__ == '__main__':
    main(sys.argv[1:])

# bad char? iso-8859-1 - '—' = 80 e2 94
