#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re

def get_book_id():
    files=os.listdir(".")
    #ignore files starting with '.' using list comprehension
    files=[filename for filename in files if filename[0] != '.']
    for fname in files:
        if re.match('.*_abbyy.gz$', fname):
            return re.sub('_abbyy.gz$', '', fname)
    print 'couldn''t get book id'
    debug()
