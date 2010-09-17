import sys
font_dir = sys.path[0] + '/fonts/'
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
fallback = "Helvetica.ttf"

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
fallback_italic = "HelveticaOblique.ttf"

droid_font_mapping = { "Times New Roman" : "DroidSerif-Regular.ttf",
                       "Georg" : "DroidSerif-Regular.ttf",
                       "georg" : "DroidSerif-Regular.ttf",
                       "Arial" : "DroidSans.ttf",
                       "Verda" : "DroidSans.ttf",
                       "verda" : "DroidSans.ttf",
                       "PalatinoLinotype" : "DroidSans.ttf",
                       "palatinolinotype" : "DroidSans.ttf",
                       "Tahoma" : "DroidSans.ttf",
                       "Courier" : "DroidSansMono.ttf",
                       "Courier New" : "DroidSansMono.ttf"
                 }
droid_fallback = "DroidSerif-Regular.ttf"

droid_italic_font_mapping = {
                 "Times New Roman" : "DroidSerif-Italic.ttf",
                 "Georg" : "DroidSerif-Italic.ttf",
                 "georg" : "DroidSerif-Italic.ttf",
                 "Arial" : "DroidSans.ttf",
                 "PalatinoLinotype" : "DroidSans.ttf",
                 "palatinolinotype" : "DroidSans.ttf",
                 "Tahoma" : "DroidSans.ttf",
                 "Courier" : "DroidSansMono.ttf",
                 "Courier New" : "DroidSansMono.ttf"
                 }
droid_fallback_italic = "DroidSerif-Italic.ttf"

if True:
    font_mapping = droid_font_mapping
    italic_font_mapping = droid_italic_font_mapping
    fallback = droid_fallback
    fallback_italic = droid_fallback_italic


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
                mapped = fallback_italic
            else:
                mapped = fallback
        font = ImageFont.truetype(font_dir + mapped, size)
        family[size] = font
    font = family[size]
    return font
