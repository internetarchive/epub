#!/usr/bin/python

import sys
import getopt
import re
import gzip

from lxml import etree
from lxml import objectify

# remove me for faster execution
import os
debugme = os.environ.get('DEBUG')
if debugme:
    from  pydbgr.api import debug
    def assert_d(expr):
        if not expr:
            debug()
else:
    def debug():
        pass
    def assert_d(expr):
        pass

class Book(object):
    def __init__(self, book_id, book_path):
        self.book_id = book_id
        self.book_path = book_path

    def get_book_id(self):
        return self.book_id

    def get_book_path(self):
        return self.book_path

    def get_scandata(self):
        return os.path.join(self.book_path, self.book_id + '_scandata.xml')

    def get_metadata(self):
        return os.path.join(self.book_path, self.book_id + '_meta.xml')

    def get_abbyy(self):
        return gzip.open(os.path.join(self.book_path,
                                      self.book_id + '_abbyy.gz'), 'rb')

    def get_image(self, i, region='{0.0,0.0},{1.0,1.0}',
                  width=600, height=780, quality=90):
        zipf = os.path.join(self.book_path,
                            self.book_id + '_jp2.zip')
        image_path = (self.book_id + '_jp2/' + self.book_id + '_'
                      + str(i).zfill(4) + '.jp2')
        return image_from_zip(zipf, image_path, region,
                              height, width, quality)

if not os.path.exists('/tmp/stdout.ppm'):
    os.symlink('/dev/stdout', '/tmp/stdout.ppm')
 
# get python string with image data - from .jp2 image in zip
def image_from_zip(zipf, image_path, region,
                   height=600, width=780, quality=90):
    output = os.popen('unzip -p ' + zipf + ' ' + image_path
        + ' | kdu_expand -region "' + region + '"'
        +   ' -reduce 2 '
        +   ' -no_seek -i /dev/stdin -o /tmp/stdout.ppm'
        + ' | pamscale -xyfit ' + str(width) + ' ' + str(height)
#         ' | pnmscale -xysize ' + str(width) + ' ' + str(height) + # or pamscale
        + ' | pnmtojpeg -quality ' + str(quality))
    return output.read()

if __name__ == '__main__':
    sys.stderr.write('I''m a module.  Don''t run me directly!')
    sys.exit(-1)
