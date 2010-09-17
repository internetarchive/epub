from collections import namedtuple

# coords is an array of fmt, coord tuples
Pageno = namedtuple('Pageno', 'type string value offset coords')
PageInfo = namedtuple('PageInfo', 'page leafno info')
class Coord(namedtuple('Coord', 'l t r b')):
    def findcenter(self):
        return (float(self.l) + (float(self.r) - float(self.l)) / 2,
                float(self.t) - (float(self.b) - float(self.t)) / 2)
