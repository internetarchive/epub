#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import getopt
import os

try:
    import json
except:
    import simplejson as json

import epub
import daisy
import iabook_to_daisy
import iabook_to_epub
import iarchive

from debug import debug, debugging, assert_d

def usage():
    sys.stderr.write("\n")
    sys.stderr.write("Usage: convert_iabook.py book_id path_to_book_files [out.epub]\n")
    sys.stderr.write("  Output defaults to book_id.epub.\n")
    sys.stderr.write("\n")
    sys.stderr.write("  -d calls epubcheck-1.0.3.jar to check output.\n")
    sys.stderr.write("  (epubcheck jar is assumed to be in the script directory)\n")

def main(argv):
    out_name = None
    import getopt
    try:
        opts, args = getopt.getopt(argv,
                                   'dho:',
                                   ['debug', 'help', 'outfile=',
                                    'document=',
                                    'daisy', 'epub', 'test', 'report', 'hocr',
                                    'toc='])
    except getopt.GetoptError:
        usage()
        sys.exit(-1)
    debug_output = False
    found_output_opt = False
    make_epub = False
    make_daisy = False
    make_test = False
    make_report = False
    make_hocr = False
    toc = None
    doc = ''
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-d', '--debug'):
            debug_output = True
        elif opt in ('--daisy'):
            make_daisy = True
            found_output_opt = True
        elif opt in ('--epub'):
            make_epub = True
            found_output_opt = True
        elif opt in ('--test'):
            make_test = True
            found_output_opt = True
        elif opt in ('--report'):
            make_report = True
            found_output_opt = True
        elif opt in ('--hocr'):
            make_hocr = True
            found_output_opt = True
        elif opt in ('-o', '--outfile'):
            out_name = arg
        elif opt in ('--document'):
            doc = arg
        elif opt in ('--toc'):
            if len(arg) > 0:
                toc = json.loads(arg)
                if toc is not None and len(toc) > 0:
                    # accept openlibrary toc format (array of tocitems)
                    # or original bespoke format: hash of pagenum -> title
                    try:
                        item0 = toc[0]
                        oldtoc = toc
                        toc = {}
                        for tocitem in oldtoc:
                            toc[tocitem['pagenum']] = '%s - %s' % (tocitem['label'],
                                                                   tocitem['title'])
                    except TypeError:
                        toc = None

                    except KeyError:
                        # there must be a better way to detect an array...
                        toc = None
        if not found_output_opt:
            make_epub = True
    if len(args) == 0:
        book_id = iarchive.infer_book_id()
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
        if out_name is not None:
            print 'outfile found as 3rd argument, but outfile is already specified via -o'
            usage()
            sys.exit(-1)
        book_id = args[0]
        book_path = args[1]
        out_name = args[2]
    else:
        print 'unrecognized extra arguments ' + args[3:]
        usage()
        sys.exit(-1)

    if out_name is None:
        if len(doc) > 0:
            out_root = os.path.basename(doc)
        else:
            out_root = book_id
        if make_daisy:
            out_name = out_root + '_daisy.zip'
        elif make_test:
            out_name = out_root + '.test'
        elif make_report:
            out_name = out_root + '.report'
        elif make_hocr:
            out_name = out_root + '.html'
        else:
            out_name = out_root + '.epub'

    iabook = iarchive.Book(book_id, doc, book_path, toc=toc)
    metadata = iabook.get_metadata()
    if make_daisy:
        ebook = daisy.Book(out_name, metadata)

        alt_booktext = "This is a protected daisy format book.  If you are hearing this message, then your device is missing the appropriate key to read this book.  For more information, see the archive.org daisy faq."
#         iabook_to_daisy.process_book(iabook, ebook, alt_booktext)
        iabook_to_daisy.process_book(iabook, ebook)
    elif make_test:
        print iabook.analyze()
        sys.exit(0)
    elif make_report:
        print iabook.report()
        sys.exit(0)
    elif make_hocr:
        raise 'NYI'
        iabook_to_hocr.process_book(iabook)
    else:
        ebook = epub.Book(out_name, metadata)
        iabook_to_epub.process_book(iabook, ebook)

    ebook.finish(metadata)

    if debug_output:
        if make_daisy:
            output = os.popen('rm -rf daisy_debug')
            output.read()
            output = os.popen('unzip -d daisy_debug ' + out_name)
            output.read()
            zedval = os.path.join(sys.path[0], 'Zedval/ZedVal.jar')
            opf_file = os.path.join('daisy_debug',
                                    iabook.get_book_id() + '_daisy.opf')
            output = os.popen('java -Xms128m -Xmx256m -jar '
                              + zedval + ' ' + opf_file)
        else:
            epubcheck = os.path.join(sys.path[0], 'epubcheck-1.0.3.jar')
            output = os.popen('java -jar ' + epubcheck + ' ' + out_name)
        print output.read()

if __name__ == '__main__':
    main(sys.argv[1:])


# freezing sensa-tions, "indigestive-style
