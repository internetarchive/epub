#!/usr/bin/python

import sys
import getopt
import re
import gzip
import os
import zipfile

try:
    from lxml import etree
except ImportError:
    sys.path.append('/petabox/sw/lib/lxml/lib/python2.5/site-packages') 
    from lxml import etree
from lxml import objectify

from debug import debug, debugging, assert_d

class Book(object):
    def __init__(self, book_id, doc, book_path):
        self.book_id = book_id
        self.doc = doc
        if len(self.doc) == 0:
            self.doc = self.book_id
        self.book_path = book_path
        if not os.path.exists(book_path):
            raise Exception('Can\'t find book path "' + book_path + '"')
        self.scandata = None
        self.images_type = 'unknown'
        if os.path.exists(os.path.join(book_path, doc + '_jp2.zip')):
            self.images_type = 'jp2.zip'
        elif os.path.exists(os.path.join(book_path, doc + '_tif.zip')):
            self.images_type = 'tif.zip'
#         else:
#             raise Exception('Can\'t find book images')
        

    def get_book_id(self):
        return self.book_id

    def get_book_path(self):
        return self.book_path

    def get_doc(self):
        return self.doc

    def get_scandata_path(self):
        paths = [
            os.path.join(self.book_path, self.doc + '_scandata.xml'),
            os.path.join(self.book_path, 'scandata.xml'),
            os.path.join(self.book_path, 'scandata.zip'),
            ]
        for sd_path in paths:
            if os.path.exists(sd_path):
                return sd_path
        raise Exception('No scandata found')

    def get_scandata(self):
        if self.scandata is None:
            scandata_path = self.get_scandata_path()
            (base, ext) = os.path.splitext(scandata_path)
            if ext.lower() == '.zip':
                z = zipfile.ZipFile(scandata_path, 'r')
                scandata_str = z.read('scandata.xml')
                z.close()
                self.scandata = objectify.fromstring(scandata_str)
                self.scandata_pages = self.scandata.pageData.page
            else:
                self.scandata = objectify.parse(self.
                                                get_scandata_path()).getroot()
                self.scandata_pages = self.scandata.xpath('/book/pageData/page')
            self.leaves = {}
            for page in self.scandata_pages:
                self.leaves[int(page.get('leafNum'))] = page
        return self.scandata

    def get_scandata_pages(self):
        self.get_scandata()
        return self.scandata_pages

    def get_page_scandata(self, i):
        self.get_scandata()
        return self.scandata_pages[int(i)]
#     scandata_pages = scandata.xpath('/book/pageData/page')
#     if scandata_pages is None or len(scandata_pages) == 0:
#         scandata_pages = scandata.pageData.page

    def get_page_data_from_leafno(self, leaf):
        if leaf in self.leaves:
            return self.leaves[leaf]
        else:
            return None

    def get_leafno_for_page(self, i):
        return int(self.get_page_scandata(i).get('leafNum'))

    def get_metadata(self):
        # metadata is by book_id, not by doc
        md_path = os.path.join(self.book_path, self.book_id + '_meta.xml')
        md = objectify.parse(md_path).getroot()
        result = []
        for el in md.iterchildren():
            if el.tag == 'language':
                result_text = iso_639_23_to_iso_639_1(el.text)
            else:
                result_text = el.text
            result.append({ 'tag':el.tag, 'text':result_text })
        return result

    def get_toc(self):
        toc_path = os.path.join(self.book_path, self.doc + '_toc.xml')
        if not os.path.exists(toc_path):
            return None
        toc = objectify.parse(toc_path).getroot()
        result = {}
        for el in toc.iterchildren():
            result[el.get('page')] = el.get('title')
        return result

    def get_abbyy(self):
        abbyy_gz = os.path.join(self.book_path, self.doc + '_abbyy.gz')
        if os.path.exists(abbyy_gz):
            return gzip.open(abbyy_gz, 'rb')
        abbyy_zip = os.path.join(self.book_path, self.doc + '_abbyy.zip')
        if os.path.exists(abbyy_zip):
            return os.popen('unzip -p ' + abbyy_zip + ' ' + self.doc + '_abbyy.xml')
#             z = zipfile.ZipFile(abbyy_zip, 'r')
#             return z.open(self.doc + '_abbyy.xml') # only in 2.6
        abbyy_xml = os.path.join(self.book_path, self.doc + '_abbyy.xml')
        if os.path.exists(abbyy_xml):
            return open(abbyy_xml, 'r')
        raise 'No abbyy file found'

    # get python string with image data - from .jp2 image in zip
    # finds appropriate leaf number for supplied page index
    def get_page_image(self, i, width=700, height=900,
                       quality=90,
                       region='{0.0,0.0},{1.0,1.0}',
                       out_img_type='jpg'):
        leafno = self.get_leafno_for_page(i)
#         debug()
        if self.images_type == 'jp2.zip':
            zipf = os.path.join(self.book_path,
                                self.doc + '_jp2.zip')
            image_path = (self.doc + '_jp2/' + self.doc + '_'
                          + str(leafno).zfill(4) + '.jp2')
            in_img_type = 'jp2'
        elif self.images_type == 'tif.zip':
            zipf  = os.path.join(self.book_path,
                                 self.doc + '_tif.zip')
            image_path = (self.doc + '_tif/' + self.doc + '_'
                          + str(leafno).zfill(4) + '.tif')
            in_img_type = 'tif'
        else:
            return None
        try:
            z = zipfile.ZipFile(zipf, 'r')
            info = z.getinfo(image_path) # for to check it exists
            z.close()
        except KeyError:
            return None
        return image_from_zip(zipf, image_path,
                              width, height, quality, region,
                              in_img_type, out_img_type)

if not os.path.exists('/tmp/stdout.ppm'):
    os.symlink('/dev/stdout', '/tmp/stdout.ppm')
if not os.path.exists('/tmp/stdout.bmp'):
    os.symlink('/dev/stdout', '/tmp/stdout.bmp')
 
# get python string with image data - from .jp2 image in zip
def image_from_zip(zipf, image_path,
                   width, height, quality, region,
                   in_img_type, out_img_type):
    if not os.path.exists(zipf):
        raise Exception('Zipfile missing')
    if region != '{0.0,0.0},{1.0,1.0}':
        raise Exception('Um, only whole image grabbage supported 4 now')

    scale = ' | pnmscale -quiet -xysize ' + str(width) + ' ' + str(height)
#     scale = ' | pamscale -quiet -xyfit ' + str(width) + ' ' + str(height)
    if out_img_type == 'jpg':
        cvt_to_out = ' | pnmtojpeg -quiet -quality ' + str(quality)
    elif out_img_type == 'ppm':
        cvt_to_out = ' | ppmtoppm -quiet'
    else:
        raise Exception('unrecognized out img type')
    if in_img_type == 'jp2':
        output = os.popen('unzip -p ' + zipf + ' ' + image_path
                        + ' | kdu_expand -region "' + region + '"'
                        +   ' -reduce 2 '
                        +   ' -no_seek -i /dev/stdin -o /tmp/stdout.bmp'
                        + ' | bmptopnm -quiet '
                        + ' | pnmscale -quiet '
                        +   ' -xysize ' + str(width) + ' ' + str(height)
                        + scale
                        + cvt_to_out)
    elif in_img_type == 'tif':
        import tempfile
        t_handle, t_path = tempfile.mkstemp()
#         t_handle.close()
        output = os.popen('unzip -p ' + zipf + ' ' + image_path
                        + ' > ' + t_path)
        output.read()
        output = os.popen('tifftopnm -quiet ' + t_path
#                         + ' | pamcut <blah> '
                        + scale
                        + cvt_to_out)
    else:
        raise Exception('unrecognized in img type')
    return output.read()

# ' | pnmscale -quiet -xysize ' + str(width) + ' ' + str(height)

# Adapted from http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
def iso_639_23_to_iso_639_1(marc_code):
    import lang_mappings
    marc_code = marc_code.lower()
    for mapping in lang_mappings.mapping:
        if marc_code in mapping:
            return mapping[marc_code]
    return marc_code
        
if __name__ == '__main__':
    sys.stderr.write('I\'m a module.  Don\'t run me directly!')
    sys.exit(-1)
