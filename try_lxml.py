import sys
try:
    from lxml import html
    sys.exit(0)
except ImportError:
    sys.exit(-1)
