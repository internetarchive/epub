#!/usr/bin/python

import sys
import getopt
import re

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

def usage():
    print 'usage: pytemplate.py a b c'

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hf:b",
                                   ["help", "food="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt == "-b":
            print "beautiful"
        elif opt in ("-f", "--food"):
            print "food: " + arg
    for name in args:
        print "arg: " + name

    if len(args) != 3:
        usage()
        sys.exit(-1)

    a = args[0]
    b = args[1]
    c = args[2]

    do_stuff(a, b, c)

def do_stuff(a, b, c):
    pass

if __name__ == '__main__':
    main(sys.argv[1:])

