#!/usr/bin/python

import sys
# import getopt
import re
# import gzip
# import os
# import zipfile

import common

from lxml import etree
# try:
#     from lxml import etree
# except ImportError:
#     sys.path.append('/petabox/sw/lib/lxml/lib/python2.5/site-packages') 
#     from lxml import etree
# from lxml import objectify

from debug import debug, debugging, assert_d


aby_ns="{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}"



# missing here:
# multiple potential indicators per page
# needed gaps/discrepancies in pagenum mapping - raj mentioned
# re_implement inference from assertions?
# -> at least review get_page_scandata

# Big missing: analyze headers_footers

# stepstone there: current debug output of epub page trimmr.

def par_is_pageno_header_footer(par):
    # if:
    #   it's the first on the page
    #   there's only one line
    #   on that line, there's a formatting tag, s.t.
    #   - it has < 6 charParam kids
    #   - each is wordNumeric
    # then:
    #   Skip it!
    if len(par) != 1:
        return False
    line = par[0]

    if len(par) != 1:
        return False
    line = par[0]
    line_text = etree.tostring(line,
                               method='text',
                               encoding=unicode)
    line_text = line_text.lower()

    print line_text

    # roman numeral?
    mo = re.match('(preface)* *([ivxl]*) *(preface)*',
                line_text)
    if mo and mo.group(2):
#         debug()
        return common.rnum_to_int(mo.group(2))


    line_text = line_text.replace('i', '1').replace('o', '0')
    mo = re.match('[\[li] *[afhiklmnouvx^]*([0-9])[afhiklmnouvx^]* *[\]ijl1]',
                  line_text)
    if mo:
        return mo.group(1)
    mo = re.match('[\[li] *([xiv]*) *[\]ijl1]',
                line_text)
    if mo and mo.group(1):
        debug()
        return common.rnum_to_int(mo.group(1))

    for fmt in line:
        if len(fmt) > 6:
            continue
        saw_non_num = False
        for cp in fmt:
            if cp.get('wordNumeric') != 'true':
                saw_non_num = True
                break
        fmt_text = etree.tostring(fmt,
                              method='text',
                              encoding=unicode)
        if not saw_non_num:
            return fmt_text
        fmt_text = fmt_text.lower()
        r = common.rnum_to_int(fmt_text)
        if r:
            return fmt_text
        fmt_text = fmt_text.replace('i', '1').replace('o', '0')
        if re.match('[0-9]+', fmt_text):
            return int(fmt_text)
        # common OCR errors
        if re.match('[0-9afhiklmnouvx^]*[0-9][0-9afhiklmnouvx^]*',
                    fmt_text):
            return fmt_text
    return ''

def get_hf_pagenos(page):
    first_par = True
    result = []
    try:
        for block in page:
            for el in block:
                if el.tag == aby_ns+'text':
                    for par in el:
                        
                        # skip if its the first line and it could be a header
                        if first_par: # replace with xpath??
                            hdr = par_is_pageno_header_footer(par)
                            if hdr:
                                result.append(int(hdr))
                                return result
                            first_par = False
                            
                        if (block == page[-1]
                            and el == block[-1]
                            and par == el[-1]):
                            ftr = par_is_pageno_header_footer(par)
                            if ftr:
                                result.append(int(ftr))
                                return result
    except ValueError:
        pass

    return result


def analyze(aby_file, iabook):
    context = etree.iterparse(aby_file,
                              tag=aby_ns+'page',
                              resolve_entities=False)
    i = 0

    pages = []
    for event, page in context:
        page_struct = {}
        page_struct['number'] = i
        page_struct['picture'] = []
        page_struct['texts'] = []
        for block in page:
            if block.get('blockType') == 'Picture':
                page_struct['picture'].append(((int(block.get('l')),
                                   int(block.get('t'))),
                                  (int(block.get('r')),
                                   int(block.get('b')))))
            if block.get('blockType') == 'Text':
                bstr = etree.tostring(block,
                                      method='text',
                                      encoding=unicode)
                
                page_struct['texts'].append(bstr)

        pages.append(page_struct)

        page.clear()
        i += 1

    print pages
    return 'hi'





def analyze_pages(aby_file, iabook):
    context = etree.iterparse(aby_file,
                              tag=aby_ns+'page',
                              resolve_entities=False)

    page_offsets = {}
    i = 0
    for event, page in context:
        page_scandata = iabook.get_page_scandata(i)
        pageno = None
        max_score = 0
        if page_scandata is not None:
#             if i > 40:
#                 debug()
            found_pagenos = get_hf_pagenos(page)
#             pageno = page_scandata.find(iabook.get_scandata_ns()
#                                         + 'pageNumber')
            for pageno in found_pagenos:
                import common
#                 r = common.rnum_to_int(pageno.text)
#                 if r > 0:
#                     pageno_val = r
#                 else:
#                     pageno_val = int(pageno.text)
                pageno_val = int(pageno)
                    
                # offset of 0th page in group, as indicated by this pageno
                cur_off = i - pageno_val
                if cur_off > 0:
                    if not cur_off in page_offsets:
                        page_offsets[cur_off] = 0
                    page_offsets[cur_off] += 1
                    if page_offsets[cur_off] > max_score:
                        max_score = page_offsets[cur_off]
#                     if max_score > 100:
#                         return str(cur_off) + ' with max'
        page.clear()
        i += 1

    offset_with_highest = None
    highest_seen = 0
    for offset in page_offsets:
        print 'offset' + str(offset) + ': ' + str(page_offsets[offset]) + ' votes'
        if page_offsets[offset] > highest_seen:
            highest_seen = page_offsets[offset]
            offset_with_highest = offset
    return str(offset_with_highest)
