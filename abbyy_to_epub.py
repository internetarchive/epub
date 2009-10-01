#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import getopt
import os

import epub
import iarchive
import process_abbyy
import common

from debug import debug, debugging, assert_d

def usage():
    sys.stderr.write("\n")
    sys.stderr.write("Usage: abbyy_to_epub.py book_id path_to_book_files [out.epub]\n")
    sys.stderr.write("  Output defaults to book_id.epub.\n")
    sys.stderr.write("\n")
    sys.stderr.write("  -d calls epubcheck-1.0.3.jar to check output.\n")
    sys.stderr.write("  (epubcheck jar is assumed to be in the script directory)\n")

def main(argv):
    epub_out = None
    import getopt
    try:
        opts, args = getopt.getopt(argv,
                                   "dho:",
                                   ["debug", "help", "outfile=",
                                    "page-map"])
    except getopt.GetoptError:
        usage()
        sys.exit(-1)
    debug_output = False
    include_page_map = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-d', '--debug'):
            debug_output = True
        elif opt in ('--page-map'):
            include_page_map = True
        elif opt in ('-o', '--outfile'):
            epub_out = arg
    if len(args) == 0:
        book_id = common.get_book_id()
        if book_id is None:
            print 'No args given and no book found in current directory'
            usage()
            sys.exit(-1)
        book_path = '.'
    elif len(args) == 1:
        book_id = args[0]
        if not os.path.exists(book_id):
            print 'Only book_id arg given, and no corresponding book dir found'
            usage()
            sys.exit(-1)
        book_path = book_id
    elif len(args) == 2:
        book_id = args[0]
        book_path = args[1]
    elif len(args) == 3:
        if epub_out is not None:
            print 'outfile found as 3rd argument, but outfile is already specified via -o'
            usage()
            sys.exit(-1)
        book_id = args[0]
        book_path = args[1]
        epub_out = args[2]
    else:
        print 'unrecognized extra arguments ' + args[3:]
        usage()
        sys.exit(-1)

    if epub_out is None:
        epub_out = book_id + '.epub'

# probably busted due to getopt
#     if epub_out == '-':
#         epub_out = sys.stdout

    iabook = iarchive.Book(book_id, book_path)
    ebook = epub.Book(epub_out, include_page_map=include_page_map)

    process_abbyy.process_book(iabook, ebook)

    meta_info_items = process_abbyy.get_meta_items(iabook)
    ebook.finish(meta_info_items)

    if debug_output:
        epubcheck = os.path.join(sys.path[0], 'epubcheck-1.0.3.jar')
        output = os.popen('java -jar ' + epubcheck + ' ' + epub_out)
        print output.read()

if __name__ == '__main__':
    main(sys.argv[1:])
