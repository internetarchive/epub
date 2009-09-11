# remove me for faster execution
import os
debugging = os.environ.get('DEBUG')

if debugging:
    from  pydbgr.api import debug
    def assert_d(expr):
        if not expr:
            debug()
else:
    def debug():
        pass
    def assert_d(expr):
        pass
