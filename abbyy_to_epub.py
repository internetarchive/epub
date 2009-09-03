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
import common

# remove me for faster execution
debugme = False
if debugme:
    from  pydbgr.api import debug
else:
    def debug():
        pass

def usage():
    sys.stderr.write("Usage: abbyy_to_epub.py book_id path_to_book_files [out.epub]")
    sys.stderr.write("  Output defaults to book_id.epub.")
    sys.stderr.write("  Use '-' to write output to stdout.")

def main(argv):
    if len(argv) != 2 and len(argv) != 3:
        usage()
        sys.exit(-1)
    book_id = argv[0]
    book_path = argv[1]
    if len(argv) == 3:
        if argv[2] == '-':
            epub_out = sys.stdout
        else:
            epub_out = argv[2]
    else:
        epub_out = book_id + '.epub'
    
    z = zipfile.ZipFile(epub_out, 'w')
    add_to_zip(z, 'mimetype', 'application/epub+zip', deflate=False)

    tree_str = epub.make_container_info()
    add_to_zip(z, 'META-INF/container.xml', tree_str)

    # style sheet
    add_to_zip(z, 'OEBPS/stylesheet.css', epub.make_stylesheet())

    # This file enables ADE mojo
    add_to_zip(z, 'OEBPS/page-template.xpgt', epub.make_ade_stylesheet())

    manifest_items = [
        { 'id':'ncx',
          'href':'toc.ncx',
          'media-type':'application/x-dtbncx+xml'
          },
        { 'id':'css',
          'href':'stylesheet.css',
          'media-type':'text/css'
          },
        { 'id','ade-page-template',
          'href':'page-template.xpgt',
          'media-type':'application/vnd.adobe-page-template+xml'
          },
        ]
    spine_items = []
    guide_items = []
    navpoints = []
    for (itemtype, info, item) in process_abbyy.generate_epub_items(book_id,
                                                                    book_path):
        nav_number = 0
        if itemtype == 'content':
            manifest_items.append(info)
            add_to_zip(z, 'OEBPS/'+info['href'], item)
        elif itemtype == 'spine':
            spine_items.append(info)
        elif itemtype == 'guide':
            guide_items.append(info)
        elif itemtype == 'navpoint':
            info['id'] = 'navpoint-' + str(nav_number)
            info['playOrder'] = str(nav_number)
            nav_number += 1
            navpoints.append(info)

    meta_info_items = process_abbyy.get_meta_items(book_id, book_path)

    tree_str = epub.make_opf(meta_info_items,
                         manifest_items,
                         spine_items,
                         guide_items);
    add_to_zip(z, 'OEBPS/content.opf', tree_str)

    tree_str = epub.make_ncx(navpoints);
    add_to_zip(z, 'OEBPS/toc.ncx', tree_str)

    z.close()

def add_to_zip(z, path, s, deflate=True):
    info = zipfile.ZipInfo(path)
    info.compress_type = zipfile.ZIP_DEFLATED if deflate else zipfile.ZIP_STORED
    info.external_attr = 0666 << 16L # fix access
    info.date_time = (2009, 12, 25, 0, 0, 0)
    z.writestr(info, s)

if __name__ == '__main__':
    main(sys.argv[1:])

# bad char? iso-8859-1 - '—' = 80 e2 94
