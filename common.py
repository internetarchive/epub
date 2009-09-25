#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
from lxml import etree

def get_book_id():
    files=os.listdir(".")
    #ignore files starting with '.' using list comprehension
    files=[filename for filename in files if filename[0] != '.']
    for fname in files:
        if re.match('.*_abbyy.gz$', fname):
            return re.sub('_abbyy.gz$', '', fname)
    print "couldn't get book id"

def tree_to_str(tree, xml_declaration=True):
    return etree.tostring(tree,
                          pretty_print=True,
                          xml_declaration=xml_declaration,
                          encoding='utf-8')

if __name__ == '__main__':
    sys.stderr.write("I'm a module.  Don't run me directly!")
    sys.exit(-1)
