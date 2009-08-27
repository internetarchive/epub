font_dir = '/Users/mccabe/s/archive/epub/ttf/'
font_mapping = { "Times New Roman" : "TimesRoman.ttf",
                 "Arial" : "Helvetica.ttf",
                 "Tahoma" : "Geneva.ttf",
                 "Courier" : "Courier.ttf",
                 "Courier New" : "Courier.ttf"
                 }
fonts = {}

import Image
import ImageDraw
import ImageFont 

def get_font(name, size):
    size *= 400/72
    if not name in fonts:
        fonts[name] = {}
    family = fonts[name];
    if not size in family:
        mapped = font_mapping[name]
        font = ImageFont.truetype(font_dir + mapped, size)
        family[size] = font
    font = family[size]
    return font


#         f = ImageFont.load_default()
# http://www.ampsoft.net/webdesign-l/WindowsMacFonts.html
