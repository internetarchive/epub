font_dir = '/Users/mccabe/s/archive/epub/ttf/'
font_mapping = { "Times New Roman" : "TimesRoman.ttf",
                 "Arial" : "Helvetica.ttf",
                 "Tahoma" : "Geneva.ttf",
                 "Courier" : "Courier.ttf",
                 "Courier New" : "Courier.ttf"
                 }
italic_font_mapping = { "Times New Roman" : "TimesItalic.ttf",
                 "Arial" : "HelveticaOblique.ttf",
                 "Tahoma" : "GenevaItalic.ttf",
                 "Courier" : "CourierOblique.ttf",
                 "Courier New" : "CourierOblique.ttf"
                 }
fonts = {}

import Image
import ImageDraw
import ImageFont 

def get_font(name, dpi, size, italic):
    size *= dpi/72
    if not name in fonts:
        fonts[name] = {}
    family = fonts[name];
    if not size in family:
        if italic:
            mapped = italic_font_mapping[name]
        else:
            mapped = font_mapping[name]
        font = ImageFont.truetype(font_dir + mapped, size)
        family[size] = font
    font = family[size]
    return font


#         f = ImageFont.load_default()
# http://www.ampsoft.net/webdesign-l/WindowsMacFonts.html
