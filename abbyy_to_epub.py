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
import iarchive
import process_abbyy
import common

from debug import debug, debugging, assert_d

def usage():
    sys.stderr.write("Usage: abbyy_to_epub.py book_id path_to_book_files [out.epub]")
    sys.stderr.write("  Output defaults to book_id.epub.")

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

    iabook = iarchive.Book(book_id, book_path)
    ebook = epub.Book(epub_out)

    process_abbyy.process_book(iabook, ebook)

    meta_info_items = process_abbyy.get_meta_items(iabook)
    ebook.finish(meta_info_items)

if __name__ == '__main__':
    main(sys.argv[1:])
