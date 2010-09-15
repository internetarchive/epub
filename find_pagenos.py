import iarchive
import sys
import re

from collections import namedtuple

from lxml.etree import iterparse
from lxml import etree

from tuples import *

import OnlineCluster
import common

ns = '{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'

def guess_best_pageno(pageinfo, pages):
    """ Select the best candidate pagenumber for the given page,
    with reference to neighboring pages.
    """
    #    print 'pageinfo.leafno: %s' % pageinfo.leafno
    def tally(pageinfo, current_leafno, sofar, weight, oc):
        for c in pageinfo.info['pageno_candidates']:
            # for pagecoord in c.coords:
            #     oc.cluster(numpy.array(pagecoord.findcenter()))
            if c.offset >= current_leafno:
                continue
            if c.offset not in sofar[c.type]:
                sofar[c.type][c.offset] = weight
            else:
                sofar[c.type][c.offset] += weight
    sofar = {'roman':{},'arabic':{}}
    oc = OnlineCluster.OnlineCluster(6)
    tally(pageinfo, pageinfo.leafno, sofar, 2, oc)
    #    print pageinfo
    for neighbor_info in pages.neighbors():
        tally(neighbor_info, pageinfo.leafno, sofar, 1, oc)
    # clusters=oc.trimclusters()
    # for c in clusters:
    #     print c
    #     print "cluster x: %s  y: %s" % (c.center[0], c.center[1])

    def thin(obj):
        kys = [k for k in obj]
        for k in kys:
            if obj[k] < 2:
                del obj[k]
    thin(sofar['roman'])
    thin(sofar['arabic'])

    mostsofar = None
    votes = 0
    for k in sofar['roman']:
        if sofar['roman'][k] > votes:
            votes = sofar['roman'][k]
            mostsofarmsg = 'roman:  %s' % k
            mostsofar = k
    for k in sofar['arabic']:
        if sofar['arabic'][k] > votes:
            votes = sofar['arabic'][k]
            mostsofarmsg = 'arabic:  %s' % k
            mostsofar = k

    pageno_guess = None
    if mostsofar:
        print 'leafno %s: page guess %s' % (pageinfo.leafno, pageinfo.leafno - int(mostsofar))
        pageno_guess = pageinfo.leafno - int(mostsofar)
    return pageno_guess

#     print 'roman:  %s' % json.dumps(sofar['roman'])
#     print 'arabic: %s' % json.dumps(sofar['arabic'])

re_roman = re.compile(r'\b[xvi]+\b')
re_arabic = re.compile(r'\b\d+\b')

def pageno_candidates(page, leafno):
    seen = {}

    # find margin % of top/bottom of text bounding box
    pagebounds = find_text_bounds(page)
    page_height = int(page.attrib['height'])
    margin = .05
    top_margin = pagebounds.t + page_height * margin
    bottom_margin = pagebounds.b - page_height * margin

    findexpr = './/'+ns+'formatting'
    for fmt in page.findall(findexpr):

        # move on if not near page top/bottom
        line = fmt.getparent()
        t = int(line.attrib['t'])
        b = int(line.attrib['b'])

        if t > top_margin and t < bottom_margin:
            continue

        fmt_text = etree.tostring(fmt,
                                  method='text',
                                  encoding=unicode).lower();
        def find_coords(m):
            # l t r b
            start, end = m.span()
            if end >= len(fmt):
                end = len(fmt) - 1
            return Coord(fmt[start].attrib['l'], t, fmt[end].attrib['r'], b)
        
        # look for roman numerals
        # fix some common OCR errors
        # XXX RESTORE adjusted_text = (fmt_text.replace('u', 'ii')
        #                  .replace('n', 'ii')
        #                  .replace('l', 'i')
        #                  .replace(r"\'", 'v'))
        adjusted_text = fmt_text

        # collapse space between potential roman numerals
        # XXX RESTORE adjusted_text = re.sub(r'\b([xvi]+)\b +\b([xvi]+)\b', r'\1\1', adjusted_text)
        for m in re_roman.finditer(adjusted_text):
            num_str = m.group()
            if not num_str in seen:
                
                i = common.rnum_to_int(num_str)
                if i > leafno and i != 0:
                    continue
                seen[num_str] = Pageno('roman', num_str, i, leafno - i,
                                       [find_coords(m)])
            else:
                seen[num_str].coords.append(find_coords(m))
            yield seen[num_str]

        # look for arabic numerals
        # fix some common OCR errors
        # XXX RESTORE adjusted_text = fmt_text.replace('i', '1').replace('o', '0').replace('s', '5').replace('"', '11')
        # collapse spaces
        # XXX RESTORE adjusted_text = re.sub(r'\b(\d+)\b +\b(\d+)\b', r'\1\1', adjusted_text)
        for m in re_arabic.finditer(adjusted_text):
            num_str = m.group()
            if not num_str in seen:
                i = int(num_str)
                if i > leafno and i != 0:
                    continue
                seen[num_str] = Pageno('arabic', num_str, i, leafno - i,
                                       [find_coords(m)])
            else:
                seen[num_str].coords.append(find_coords(m))
            yield seen[num_str]



def find_text_bounds(page):
    l = t = 100000
    r = b = 0
    textfound = False
    for block in page.findall('.//'+ns+'block'):
        if block.attrib['blockType'] != 'Text':
            continue
        textfound = True
        bl = int(block.attrib['l'])
        if bl < l: l = bl

        bt = int(block.attrib['t'])
        if bt < t: t = bt

        br = int(block.attrib['r'])
        if br > r: r = br

        bb = int(block.attrib['b'])
        if bb > b: b = bb

    if not textfound:
        l = 0
        t = 0
        r = int(page.attrib['width'])
        b = int(page.attrib['height'])
    return Coord(l, t, r, b)
