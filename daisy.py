#!/usr/bin/python

from lxml import etree
from lxml import objectify

import common
import zipfile
from datetime import datetime
import os
import sys
import StringIO

from debug import debug, debugging

class Book(object):

    def __init__(self, epub_out, book_id='book', content_dir=''):
        self.dt = datetime.now()
        self.z = zipfile.ZipFile(epub_out, 'w')
        self.content_dir = content_dir
        self.book_id = book_id
        self.nav_number = 1

        # style sheet
        for content in ['daisy.css', 'daisyTransform.xsl',
                        'dtbook-2005-3.dtd', 'html.css']:
            content_src = os.path.join(sys.path[0], 'daisy', content)
            content_str = open(content_src, 'r').read()
            self.add(self.content_dir + content, content_str)

        self.manifest_items = [
            { 'id':'xml',
              'href':book_id + '_daisy.xml',
              'media-type':'application/x-dtbook+xml'
              },
            { 'id':'opf',
              'href':book_id + '_daisy.opf',
              'media-type':'text/xml'
              },
            { 'id':'ncx',
              'href':book_id + '_daisy.ncx',
              'media-type':'application/x-dtbncx+xml'
              },
            { 'id':'smil',
              'href':book_id + '_daisy.smil',
              'media-type':'application/smil'
              },
            { 'id':'daisyTransform',
              'href':'daisyTransform.xsl',
              'media-type':'text/xsl'
              },
            { 'id':'daisyCss',
              'href':'daisy.css',
              'media-type':'text/css'
              },
            { 'id':'htmlCss',
              'href':'html.css',
              'media-type':'text/css'
              },
            ]

        self.page_items = []
        self.navpoints = []

    def add_navpoint(self, text, content):
        # text='text':'Title Page',
        # content='title.html' }
        # navpoints added thru this interface are sequential -
        # id and playOrder are generated.
        self.navpoints.append({ 'text':text, 'content':content,
                                'playOrder':self.nav_number })
        self.nav_number += 1

    def add_page_item(self, name, value, href, type='normal'):
        # name='iii', value='3', href='part032.html#pgiii', type='front'
        # name='3', value='3', href='part042.html#pg3', type='normal'
        self.page_items.append({ 'name':name, 'value':value, 'href':href,
                                 'type':type, 'playOrder':self.nav_number })
        self.nav_number += 1

    def add(self, path, content_str, deflate=True):
        info = zipfile.ZipInfo(path)
        info.compress_type = (zipfile.ZIP_DEFLATED if deflate
                              else zipfile.ZIP_STORED)
        info.external_attr = 0666 << 16L # fix access
        info.date_time = (self.dt.year, self.dt.month, self.dt.day,
                          self.dt.hour, self.dt.minute, self.dt.second)
        self.z.writestr(info, content_str)

    def finish(self, metadata):
        tree_str = make_opf(metadata,
                            self.manifest_items)
        self.add(self.content_dir + self.book_id + '_daisy.opf', tree_str)

        tree_str = make_ncx(self.navpoints, self.page_items)
        self.add(self.content_dir + self.book_id + '_daisy.ncx', tree_str)

        self.z.close()

dc = 'http://purl.org/dc/elements/1.1/'
dcb = '{' + dc + '}'
def make_opf(metadata,
             manifest_items):
    xml = """<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE package PUBLIC "+//ISBN 0-9673008-1-9//DTD OEB 1.2 Package//EN"
"http://openebook.org/dtds/oeb-1.2/oebpkg12.dtd">
<package xmlns="http://openebook.org/namespaces/oeb-package/1.0/"
unique-identifier="bookid"/>
"""
    tree = etree.parse(StringIO.StringIO(xml))
    root_el = tree.getroot()
    metadata_el = etree.SubElement(root_el, 'metadata')
    dc_metadata_el = etree.SubElement(metadata_el, 'dc-metadata',
        nsmap={ 'dc':dc,
            'oebpackage':'http://openebook.org/namespaces/oeb-package/1.0/' })
    el = etree.SubElement(dc_metadata_el, dcb + 'Format')
    el.text = 'ANSI/NISO Z39.86-2005'
    for tagname in [ 'title', 'creator', 'subject', 'description',
                     'publisher', 'contributor', 'date', 'type',
                     'format', 'identifier', 'source', 'language',
                     'relation','coverage', 'rights' ]:
        # XXX should make sure req'd is present somehow
        if not tagname in metadata:
            continue
        dctag = dcb + tagname[:1].upper() + tagname[1:]

        if tagname == 'identifier':
            dt = datetime.now()
            xtra = (str(dt.year) + str(dt.month) + str(dt.day) +
                    str(dt.hour) + str(dt.minute) + str(dt.second))
            el = etree.SubElement(dc_metadata_el, dctag,
                                  { 'id':'bookid' })
            el.text = metadata[tagname] + xtra
        else:
            el = etree.SubElement(dc_metadata_el, dctag)
            el.text = metadata[tagname]
    x_metadata_el = etree.SubElement(metadata_el, 'x-metadata')
    el = etree.SubElement(x_metadata_el, 'meta',
                          { 'name':'dtb:multimediaType', 'content':'textNCX' })
    el = etree.SubElement(x_metadata_el, 'meta',
                          { 'name':'dtb:multimediaContent', 'content':'text' })
    # XXX more x-metadata here?

    manifest_el = etree.SubElement(root_el, 'manifest')
    for item in manifest_items:
        etree.SubElement(manifest_el, 'item', item)

    spine_el = etree.SubElement(root_el, 'spine')
    etree.SubElement(spine_el, 'itemref',
                     { 'idref':'smil' })

    tree = etree.ElementTree(root_el)
    return common.tree_to_str(tree)

def make_ncx(navpoints, page_items):
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

    # navMap element
    navmap = etree.SubElement(root, 'navMap')
    for item in navpoints:
        navpoint = etree.SubElement(navmap, 'navPoint',
                                    { 'id':'navpoint-' + str(item['playOrder']),
                                      'playOrder':str(item['playOrder']) })
        navlabel = etree.SubElement(navpoint, 'navLabel')
        etree.SubElement(navlabel, 'text').text = item['text']
         # XXX 'content' should be 'href'
        etree.SubElement(navpoint, 'content', src=item['content'])

    # pageList element
    if len(page_items) > 0:
        pagelist = etree.SubElement(root, 'pageList',
                                    { 'id':'page-mapping', 'class':'pagelist' })
        navlabel = etree.SubElement(pagelist, 'navLabel')
        text = etree.SubElement(navlabel, 'text')
        text.text = 'Pages'
        for item in page_items:
            id = 'page-' + item['name']
            pagetarget = etree.SubElement(pagelist, 'pageTarget',
                                          { 'id':id, 'value':str(item['value']),
                                            'type':item['type'],
                                            'playOrder':str(item['playOrder']) })
            navlabel = etree.SubElement(pagetarget, 'navLabel')
            etree.SubElement(navlabel, 'text').text = 'Page ' + item['name']
            etree.SubElement(pagetarget, 'content', src=item['href'])

    tree = etree.ElementTree(root)
    return common.tree_to_str(tree)

if __name__ == '__main__':
    sys.stderr.write('I\'m a module.  Don\'t run me directly!')
    sys.exit(-1)
