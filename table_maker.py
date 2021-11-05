# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont 
import textwrap
import os
from ast import literal_eval

path = os.path.abspath('lessons9.json')

with open(path, 'r', encoding='utf-8') as g:
    shedule = literal_eval(g.read())
    width = (len(shedule[0]["lessons"]) + 1) * 200
    height = len(shedule)*100
    
    new_img = Image.new('RGB', (width, height), 'white')
    pencil = ImageDraw.Draw(new_img)
    unicode_font = ImageFont.truetype("calibri.ttf", 12)
    
    for y, row in enumerate(shedule):
        pencil.text((10, y*100 + 25), str(row["begin"]),  font=unicode_font, fill='black')
        pencil.text((10, y*100 + 50), str(row["end"]),  font=unicode_font, fill='black')
        pencil.line((0, y*100, width, y*100), fill='black', width=5)
        pencil.line((100, y*100, 100, (y+1)*100), fill='black', width=5)
        for x, lesson in enumerate(row["lessons"]):
            if lesson != []:
                for _y, i in enumerate(lesson):
                    txt = "\n".join(textwrap.wrap(i["lesson"][1:], width=30))
                    print(txt)
                    pencil.text(((x+1)*200 + 10, y*100 + 25 + _y*25), txt,  font=unicode_font, fill='black')
            pencil.line(((x+1)*200, y*100, (x+1)*200, (y+1)*100), fill='black', width=5)
    new_img.save("text.jpg")    
    
