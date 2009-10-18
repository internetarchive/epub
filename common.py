#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re

from datetime import datetime
from debug import debug, debugging

import sys

from lxml import etree



def tree_to_str(tree, xml_declaration=True):
    return etree.tostring(tree,
                          pretty_print=True,
                          xml_declaration=xml_declaration,
                          encoding='utf-8')


def get_metadata_tag_data(metadata, tag):
    for el in metadata:
        if el['tag'] == tag:
            return el['text']
    return 'Unknown'


def get_dt_str():
    dt = datetime.now()
    return (str(dt.year) + str(dt.month) + str(dt.day) +
            str(dt.hour) + str(dt.minute) + str(dt.second))

if __name__ == '__main__':
    sys.stderr.write("I'm a module.  Don't run me directly!")
    sys.exit(-1)
