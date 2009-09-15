#!/usr/bin/python

import sys
import getopt
import re
import gzip
import os
import zipfile

from lxml import etree
from lxml import objectify

from debug import debug, debugging, assert_d

class Book(object):
    def __init__(self, book_id, book_path):
        self.book_id = book_id
        self.book_path = book_path
        if not os.path.exists(book_path):
            raise Exception('Can\'t find book path "' + book_path + '"')
        self.scandata = None

    def get_book_id(self):
        return self.book_id

    def get_book_path(self):
        return self.book_path

    def get_scandata_path(self):
        paths = [
            os.path.join(self.book_path, self.book_id + '_scandata.xml'),
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
                scandata_pages = self.scandata.pageData.page
            else:
                self.scandata = objectify.parse(self.
                                                get_scandata_path()).getroot()
                scandata_pages = self.scandata.xpath('/book/pageData/page')
            self.leaves = {}
            for page in scandata_pages:
                self.leaves[int(page.get('leafNum'))] = page
        return self.scandata

    def get_page_data(self, leaf):
        if leaf in self.leaves:
            return self.leaves[leaf]
        else:
            return None

    def get_metadata_path(self):
        return os.path.join(self.book_path, self.book_id + '_meta.xml')

    def get_abbyy(self):
        return gzip.open(os.path.join(self.book_path,
                                      self.book_id + '_abbyy.gz'), 'rb')

    # get python string with image data - from .jp2 image in zip
    def get_image(self, i, width=700, height=900,
                  quality=90,
                  region='{0.0,0.0},{1.0,1.0}',
                  img_type='jpg'):
        zipf = os.path.join(self.book_path,
                            self.book_id + '_jp2.zip')
        image_path = (self.book_id + '_jp2/' + self.book_id + '_'
                      + str(i).zfill(4) + '.jp2')
        try:
            z = zipfile.ZipFile(zipf, 'r')
            info = z.getinfo(image_path) # for to check it exists
            z.close()
        except KeyError:
            return None
        return image_from_zip(zipf, image_path,
                              width, height, quality, region, img_type)

if not os.path.exists('/tmp/stdout.ppm'):
    os.symlink('/dev/stdout', '/tmp/stdout.ppm')
 
# get python string with image data - from .jp2 image in zip
def image_from_zip(zipf, image_path,
                   width, height, quality, region, img_type):
    if not os.path.exists(zipf):
        raise Exception('Zipfile missing')

    if img_type == 'jpg':
        output = os.popen('unzip -p ' + zipf + ' ' + image_path
                      + ' | kdu_expand -region "' + region + '"'
                      +   ' -reduce 2 '
                      +   ' -no_seek -i /dev/stdin -o /tmp/stdout.ppm'
                      + ' | pamscale -xyfit ' + str(width) + ' ' + str(height)
                      + ' | pnmtojpeg -quality ' + str(quality))
    elif img_type == 'ppm':
        output = os.popen('unzip -p ' + zipf + ' ' + image_path
                      + ' | kdu_expand -region "' + region + '"'
                      +   ' -reduce 2 '
                      +   ' -no_seek -i /dev/stdin -o /tmp/stdout.ppm'
                      + ' | pamscale -xyfit ' + str(width) + ' ' + str(height))
    else:
        raise 'unrecognized image type'
    return output.read()

# ' | pnmscale -xysize ' + str(width) + ' ' + str(height)

if __name__ == '__main__':
    sys.stderr.write('I\'m a module.  Don''t run me directly!')
    sys.exit(-1)
