font_dir = '/home/mike/s/archive/epub/ttf/'
font_mapping = { "Times New Roman" : "TimesRoman.ttf",
                 "Georg" : "TimesRoman.ttf",
                 "georg" : "TimesRoman.ttf",
                 "Arial" : "Helvetica.ttf",
                 "Verda" : "Geneva.ttf",
                 "verda" : "Geneva.ttf",
                 "PalatinoLinotype" : "Helvetica.ttf",
                 "palatinolinotype" : "Helvetica.ttf",
                 "Tahoma" : "Geneva.ttf",
                 "Courier" : "Courier.ttf",
                 "Courier New" : "Courier.ttf"
                 }
italic_font_mapping = {
                 "Times New Roman" : "TimesItalic.ttf",
                 "Georg" : "TimesItalic.ttf",
                 "georg" : "TimesItalic.ttf",
                 "Arial" : "HelveticaOblique.ttf",
                 "PalatinoLinotype" : "HelveticaOblique.ttf",
                 "palatinolinotype" : "HelveticaOblique.ttf",
                 "Tahoma" : "GenevaItalic.ttf",
                 "Courier" : "CourierOblique.ttf",
                 "Courier New" : "CourierOblique.ttf"
                 }
fonts = {}

import Image
import ImageDraw
import ImageFont 

def get_font(name, dpi, size, italic=False):
    size *= dpi/72
    if not name in fonts:
        fonts[name] = {}
    family = fonts[name];
    if not size in family:
        try:
            if italic:
                mapped = italic_font_mapping[name]
            else:
                mapped = font_mapping[name]
        except KeyError:
            if italic:
                mapped = "HelveticaOblique.ttf"
            else:
                mapped = "Helvetica.ttf"
        font = ImageFont.truetype(font_dir + mapped, size)
        family[size] = font
    font = family[size]
    return font


#         f = ImageFont.load_default()
# http://www.ampsoft.net/webdesign-l/WindowsMacFonts.html
