#!/usr/bin/python
# -*- coding: utf-8 -*-

from lxml import etree
from lxml import objectify

import common

# remove me for faster execution
debugme = True
if debugme:
    from  pydbgr.api import debug
else:
    def debug():
        pass

def make_container_info():
    root = etree.Element('container',
                         version='1.0',
                         xmlns='urn:oasis:names:tc:opendocument:xmlns:container')
    rootfiles = etree.SubElement(root, 'rootfiles')
    etree.SubElement(rootfiles, 'rootfile',
                     { 'full-path' : 'OEBPS/content.opf',
                       'media-type' : 'application/oebps-package+xml' } )
    return common.tree_to_str(root)

dc = 'http://purl.org/dc/elements/1.1/'
dcb = '{' + dc + '}'
def make_opf(meta_info_items,
             manifest_items,
             spine_items,
             guide_items):
    root = etree.Element('package',
                         { 'xmlns' : 'http://www.idpf.org/2007/opf',
                           'unique-identifier' : 'bookid',
                           'version' : '2.0' },
                         nsmap={'dc' : dc })
    metadata = etree.SubElement(root, 'metadata')
    for item in meta_info_items:
        el = etree.SubElement(metadata, item['item'], item['atts'] if 'atts' in item else None)
        if 'text' in item:
            el.text = item['text']
    manifest = etree.SubElement(root, 'manifest')
    for item in manifest_items:
        etree.SubElement(manifest, 'item', item)
    if len(spine_items) > 0:    
        spine = etree.SubElement(root, 'spine', toc='ncx')
    for item in spine_items:
        etree.SubElement(spine, 'itemref', item)
    if len(guide_items) > 0:
        guide = etree.SubElement(root, 'guide')
    for item in guide_items:
        etree.SubElement(guide, 'reference', item)
    return common.tree_to_str(root)

navpoints = [
    { 'id' : 'navpoint-1', 'playOrder' : '1', 'text' : 'Book', 'content' : 'book.html' },

#     { 'id' : 'navpoint-1', 'playOrder' : '1', 'text' : 'Book Cover', 'content' : 'title.html' },
#     { 'id' : 'navpoint-2', 'playOrder' : '2', 'text' : 'Contents', 'content' : 'content.html' },
    ]
def make_ncx(navpoints):
    import StringIO
    xml = """<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"/>
"""
    tree = etree.parse(StringIO.StringIO(xml))
    root = tree.getroot()
    head = etree.SubElement(root, 'head')
    metas = [
        { 'name' : 'dtb:uid', 'content' : 'test id' },
        { 'name' : 'dtb:depth', 'content' : '1' },
        { 'name' : 'dtb:totalPageCount', 'content' : '0' },
        { 'name' : 'dtb:maxPageNumber', 'content' : '0' },
        ]
    for item in metas:
        etree.SubElement(head, 'meta', item)
    doctitle = etree.SubElement(root, 'docTitle')
    etree.SubElement(doctitle, 'text').text = 'Hello World';
    navmap = etree.SubElement(root, 'navMap')
    for item in navpoints:
        navpoint = etree.SubElement(navmap, 'navPoint', id=item['id'], playOrder=item['playOrder'])
        navlabel = etree.SubElement(navpoint, 'navLabel')
        etree.SubElement(navlabel, 'text').text = item['text']
        etree.SubElement(navpoint, 'content', src=item['content'])
    tree = etree.ElementTree(root)
    return common.tree_to_str(tree)
