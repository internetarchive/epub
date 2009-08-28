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

# remove me for faster execution
debugme = True
if debugme:
    from  pydbgr.api import debug
else:
    def debug():
        pass

def usage():
#    print 'usage: abbyy_to_epub.py book_id abbyy.xml scandata.xml book_id'
    print 'usage: abbyy_to_epub.py'

def main(argv):
    book_id = get_book_id()
    z = zipfile.ZipFile(book_id + '.epub', 'w')
    info = zipfile.ZipInfo('mimetype')
    info.compress_type = zipfile.ZIP_STORED
    
    info.external_attr = 0666 << 16L # fix access
    info.date_time = (2009, 12, 25, 0, 0, 0)
    z.writestr(info, 'application/epub+zip')

    tree = make_meta_inf()
    info = zipfile.ZipInfo('META-INF/container.xml')
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0666 << 16L
    info.date_time = (2009, 12, 25, 0, 0, 0)
    z.writestr(info, etree.tostring(tree,
                                    pretty_print=True,
                                    xml_declaration=True,
                                    encoding='utf-8'))

    tree = make_opf();
    info = zipfile.ZipInfo('OEBPS/content.opf')
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0666 << 16L
    info.date_time = (2009, 12, 25, 0, 0, 0)
    z.writestr(info, etree.tostring(tree,
                                    pretty_print=True,
                                    xml_declaration=True,
                                    encoding='utf-8'))

    tree = make_ncx();
    info = zipfile.ZipInfo('OEBPS/toc.ncx')
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0666 << 16L
    info.date_time = (2009, 12, 25, 0, 0, 0)
    z.writestr(info, etree.tostring(tree,
                                    pretty_print=True,
                                    xml_declaration=True,
                                    encoding='utf-8'))

    tree = make_epub(book_id);
    info = zipfile.ZipInfo('OEBPS/book.html')
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0666 << 16L
    info.date_time = (2009, 12, 25, 0, 0, 0)
    z.writestr(info, etree.tostring(tree,
                                    pretty_print=True,
                                    xml_declaration=True,
                                    encoding='utf-8'))

    z.close()



#     sys.stdout.write(etree.tostring(tree,
#                                     pretty_print=True,
#                                     xml_declaration=True,
#                                     encoding='utf-8'))


def get_book_id():
    files=os.listdir(".")
    #ignore files starting with '.' using list comprehension
    files=[filename for filename in files if filename[0] != '.']
    for fname in files:
        if re.match('.*_abbyy.gz$', fname):
            return re.sub('_abbyy.gz$', '', fname)
    print 'couldn''t get book id'
    debug()


aby_ns="{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}"
def make_epub(book_id):
    scandata = objectify.parse(book_id + '_scandata.xml').getroot()
    metadata = objectify.parse(book_id + '_meta.xml').getroot()
    aby_file = gzip.open(book_id + '_abbyy.gz', 'rb')
    context = etree.iterparse(aby_file,  tag=aby_ns+'page', resolve_entities=False)
    tree = build_html(context, scandata, metadata)
#     sys.stdout.write(etree.tostring(tree,
#                                     pretty_print=True,
#                                     xml_declaration=True))
    return tree

def include_page(page):
    add = page.find('addToAccessFormats')
    if add is not None and add.text == 'true':
        return True
    else:
        return False

def build_html(context, scandata, metadata):
    bookData = scandata.find('bookData')
    scanLog = scandata.find('scanLog')
    scandata_pages = scandata.xpath('/book/pageData/page')

    def CLASS(*args): # class is a reserved word in Python
        return {"class":' '.join(args)}
    from lxml.builder import E
    html = E.html(
        E.head( 
           E.title('test title'), # metadata.title
           E.meta(name='generator', content='abbyy to xhtml tool'),
           E.link(rel="stylesheet",
                  href="css/main.css",
                  type="text/css"),
           E.meta({'http-equiv':"Content-Type"},
                  content="application/xhtml+xml; charset=utf-8")
        ), 
        E.body(
          E.div(CLASS('body'))
        ),
        xmlns="http://www.w3.org/1999/xhtml",
    )

    bdiv = html.xpath('/html/body/div')[0]
    i = 0
    for event, page in context:
        for block in page:
            if block.get('blockType') == 'Text':
                pass
            else:
                pass
            for el in block:
                if el.tag == aby_ns+'region':
                    for rect in el:
                        pass
                elif el.tag == aby_ns+'text':
                    for par in el:
                        lines = []
                        for line in par:
                            lines.append(etree.tostring(line, method='text', encoding=unicode))
                        bdiv.append(E.p(' '.join(lines)))
#                         par_coords = box_from_par(par)
#                         if par_coords is not None:
#                             pass
#                         for line in par:
#                             for fmt in line:
#                                 for cp in fmt:
#                                     assert_d(cp.tag == aby_ns+'charParams')
#                                     draw.text((int(cp.get('l')),
#                                                int(cp.get('b'))),
#                                               cp.text.encode('utf-8'),
#                                               font=f,
#                                               fill=color.white)
                   
                elif (el.tag == aby_ns+'row'):
                    pass
                else:
                    print('unexpected tag type' + el.tag)
                    sys.exit(-1)
        page.clear()

    htmldoc = etree.ElementTree(html);
    return htmldoc

def make_meta_inf():
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
def make_opf(manifest_items=manifest_items, spine_items=spine_items, guide_items=guide_items):
    dc = 'http://purl.org/dc/elements/1.1/'
    dcb = '{http://purl.org/dc/elements/1.1/}'
    root = etree.Element('package',
                         { 'xmlns' : 'http://www.idpf.org/2007/opf',
                           'unique-identifier' : 'bookid',
                           'version' : '2.0' },
                         nsmap={'dc' : dc })
    metadata = etree.SubElement(root, 'metadata')
    etree.SubElement(metadata, dcb+'title').text = 'test title'
    etree.SubElement(metadata, dcb+'creator').text = 'test creator'
    etree.SubElement(metadata, dcb+'identifier', id='bookid').text = 'test id'
    etree.SubElement(metadata, dcb+'language').text = 'en-US';
    etree.SubElement(metadata, 'meta', name='cover', content='cover-image')

    manifest = etree.SubElement(root, 'manifest')
    for item in manifest_items:
        etree.SubElement(manifest, 'item', item)
    spine = etree.SubElement(root, 'spine', toc='ncx')
    for item in spine_items:
        etree.SubElement(spine, 'itemref', item)
    if len(guide_items) > 0:
        guide = etree.SubElement(root, 'guide')
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

if __name__ == '__main__':
    main(sys.argv[1:])

# bad char? iso-8859-1 - '—' = 80 e2 94
