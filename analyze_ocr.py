import sys
import iarchive
from lxml.etree import iterparse


from windowed_iterator import windowed_iterator
import find_pagenos

ns = '{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'

# import find_header_footer
from tuples import *


def build_pageinfo(pages):
    for leafno, page in enumerate(pages):
        pageno_candidates = [c for c in find_pagenos.pageno_candidates(page, leafno)]
        yield PageInfo(page, leafno, {'pageno_candidates':pageno_candidates})

def drop_event(iter):
    for event, page in iter:
        yield page

def get_annotated_pages(context):
    pages = drop_event(context)
    pages = build_pageinfo(pages)
    def clear_pageinfo(pageinfo):
        pageinfo.page.clear()
#        pageinfo.pageno_candidates.clear()

    windowsize = 5
    pages = windowed_iterator(pages, windowsize, clear_pageinfo)
    for pageinfo in pages:
        guess = find_pagenos.guess_best_pageno(pageinfo, pages)
        # hf = guess_hf(pageinfo, pages)
        yield pageinfo, pages, guess

def main(args):
    book_id = args[0]
    iabook = iarchive.Book(book_id, '', book_id)
    
    f = iabook.get_abbyy()

    context = iterparse(f, tag=ns+'page')
    for pageinfo, pages, guess in get_annotated_pages(context):
        print guess

if __name__ == '__main__':
    main(sys.argv[1:])
