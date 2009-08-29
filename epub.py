#!/usr/bin/python
# -*- coding: utf-8 -*-

from lxml import etree
from lxml import objectify

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
    return root

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
def make_opf(meta_info_items=meta_info_items,
             manifest_items=manifest_items,
             spine_items=spine_items,
             guide_items=guide_items):
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
    
#     etree.SubElement(metadata, dcb+'title').text = 'test title'
#     etree.SubElement(metadata, dcb+'creator').text = 'test creator'
#     etree.SubElement(metadata, dcb+'identifier', id='bookid').text = 'test id'
#     etree.SubElement(metadata, dcb+'language').text = 'en-US';
#     etree.SubElement(metadata, 'meta', name='cover', content='cover-image')

    manifest = etree.SubElement(root, 'manifest')
    for item in manifest_items:
        etree.SubElement(manifest, 'item', item)
    spine = etree.SubElement(root, 'spine', toc='ncx')
    for item in spine_items:
        etree.SubElement(spine, 'itemref', item)
    if len(guide_items) > 0:
        guide = etree.SubElement(root, 'guide')
        guide = etree.SubElement(root, 'donkey')
    for item in guide_items:
        etree.SubElement(guide, 'reference', item)
    return root

navpoints = [
    { 'id' : 'navpoint-1', 'playOrder' : '1', 'text' : 'Book', 'content' : 'book.html' },

#     { 'id' : 'navpoint-1', 'playOrder' : '1', 'text' : 'Book Cover', 'content' : 'title.html' },
#     { 'id' : 'navpoint-2', 'playOrder' : '2', 'text' : 'Contents', 'content' : 'content.html' },
    ]
def make_ncx(navpoints=navpoints):
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
    return tree
