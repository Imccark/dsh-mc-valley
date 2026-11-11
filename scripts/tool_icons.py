"""Draw original B1/B6/B7 item glyphs on a 16px grid; no reference pixels are read.

Local vanilla references inform silhouette/material only. These deliberately
different drawings use rectangular clusters, stepped diagonals and hard light.
Run with uv/base; --sheet also creates a local inspection PNG using Pillow.
"""
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parent.parent
PALETTE = {
    'o': '#30291f', 'd': '#65402b', 'b': '#956039', 'w': '#bc884e', 'h': '#e2bb78',
    'p': '#eadbb0', 'l': '#fff2d2', 's': '#59605c', 'i': '#949b91', 'a': '#cdd4c5',
    'g': '#547d35', 'G': '#93b95a', 'r': '#913a35', 'R': '#da6250',
    'v': '#68407d', 'V': '#ad78bf', 't': '#306b78', 'T': '#79cad0', 'k': '#181d1c',
    'n': '#ae7953', 'N': '#d4a879',
    'c': '#8db3c0', 'C': '#d8eff0', 'H': '#dd4263', 'J': '#ff96b0',
    'D': '#422340', 'Q': '#984d96',
}

class Glyph:
    def __init__(self): self.pixels = [['.' for _ in range(16)] for _ in range(16)]
    def rect(self, x, y, w, h, color):
        assert color in PALETTE and 0 <= x < x+w <= 16 and 0 <= y < y+h <= 16
        for row in self.pixels[y:y+h]: row[x:x+w] = [color]*w
        return self
    def steps(self, x, y, count, dx, dy, w, h, color):
        for i in range(count): self.rect(x+i*dx, y+i*dy, w, h, color)
        return self
    def svg(self):
        paths = {}
        for y,row in enumerate(self.pixels):
            x=0
            while x<16:
                color=row[x]; end=x+1
                while end<16 and row[end]==color: end+=1
                if color!='.': paths.setdefault(color,[]).append(f'M{x} {y}h{end-x}v1H{x}z')
                x=end
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" shape-rendering="crispEdges"><!-- Original pixel item; tool_icons.py. -->'+''.join(f'<path fill="{PALETTE[c]}" d="{"".join(parts)}"/>' for c,parts in paths.items())+'</svg>\n'

def book(cover='r'):
    g=Glyph()
    g.rect(3,2,10,1,'o').rect(2,3,12,10,'o').rect(3,13,10,1,'o')
    g.rect(3,4,10,7,cover).rect(4,3,8,1,'h').rect(3,11,10,2,'p')
    g.rect(4,11,8,1,'l').rect(3,5,1,6,'d').rect(5,5,6,1,'w')
    return g

def splash_potion(harming=False):
    """Original offset cork/stepped neck and round flask; no vanilla pixels."""
    dark, light = ('D', 'Q') if harming else ('H', 'J')
    g = Glyph().rect(10,1,4,3,'d').rect(10,1,3,1,'h').rect(10,2,3,1,'w')
    g.rect(9,4,4,2,'c').rect(8,6,4,2,'c').rect(6,8,6,1,'c')
    g.rect(3,9,10,1,'c').rect(2,10,12,4,'c').rect(3,14,10,1,'c').rect(5,15,6,1,'s')
    g.rect(10,4,2,2,'C').rect(9,6,2,2,'C').rect(7,8,4,1,'C')
    g.rect(4,9,8,1,'C').rect(3,10,10,4,'C').rect(4,14,8,1,'a')
    g.rect(5,10,6,1,light).rect(4,11,8,3,dark).rect(4,11,4,1,light)
    g.rect(4,10,1,3,'l').rect(5,9,2,1,'l').rect(10,13,2,1,light)
    return g


def glyphs():
    icons={}
    icons['written_book']=book('b').rect(10,3,2,7,'d').rect(4,6,4,1,'h')
    icons['writable_book']=book().steps(6,8,5,1,-1,2,3,'s').steps(7,7,5,1,-1,2,2,'a').rect(11,2,2,2,'l').rect(5,11,2,2,'d')
    icons['enchanted_book']=book('v').rect(5,4,1,7,'V').rect(9,4,2,8,'h').rect(8,12,3,2,'r').rect(1,2,1,1,'V').rect(14,6,1,1,'V')
    g=Glyph().rect(2,2,12,3,'o').rect(3,3,10,1,'a').rect(3,5,10,2,'s').rect(5,7,6,2,'o').rect(6,7,4,5,'s').rect(7,8,2,3,'i').rect(4,12,8,2,'o').rect(5,12,6,1,'i').rect(3,14,10,1,'o')
    icons['anvil']=g
    g=Glyph().rect(2,3,12,10,'o').rect(4,1,8,2,'o').rect(3,3,10,3,'h').rect(4,2,8,1,'w').rect(3,6,5,6,'w').rect(8,6,5,6,'b').rect(3,12,10,2,'d')
    g.rect(4,3,8,1,'b').rect(5,4,1,2,'d').rect(9,4,1,2,'d').rect(3,7,2,4,'h').rect(6,7,1,5,'d').rect(9,7,3,1,'d').rect(10,8,1,4,'s').rect(10,8,2,1,'a')
    icons['crafting_table']=g
    g=Glyph().rect(2,3,12,10,'o').rect(4,1,8,2,'o').rect(3,3,10,2,'h').rect(3,5,10,7,'w').rect(3,12,10,2,'b').rect(5,5,6,6,'s').rect(6,6,4,4,'a').rect(7,7,2,2,'r')
    for x,y in [(3,6),(3,10),(11,6),(11,10),(5,2),(9,2)]: g.rect(x,y,1,1,'p')
    icons['command_block']=g
    g=Glyph().steps(2,11,5,2,-2,3,3,'o').steps(3,11,4,2,-2,2,2,'b').steps(5,9,3,2,-2,2,2,'w').rect(10,1,4,5,'o').rect(11,2,3,3,'h').rect(12,2,2,2,'T').rect(10,5,2,2,'h').rect(9,6,2,2,'d')
    icons['spyglass']=g
    g=Glyph().rect(4,1,8,1,'o').rect(2,3,12,10,'o').rect(3,2,10,12,'s').rect(4,3,8,9,'k').rect(5,13,6,2,'o').rect(3,10,2,2,'a').rect(5,12,6,1,'a').rect(11,10,2,2,'i').rect(7,5,2,3,'R').rect(8,8,2,3,'a').rect(8,4,1,2,'r')
    icons['compass']=g
    g=Glyph().rect(2,2,12,12,'o').rect(3,3,10,10,'p').rect(3,3,2,9,'h').rect(12,4,1,9,'h').rect(5,4,6,8,'l').rect(4,4,3,3,'g').rect(8,8,4,4,'g').rect(7,5,2,7,'t').rect(6,7,2,5,'T').rect(4,9,2,3,'G').rect(10,4,2,3,'G').rect(1,5,1,6,'o').rect(14,6,1,6,'o')
    icons['map']=g
    icons['paper']=Glyph().rect(4,1,7,1,'o').rect(3,2,10,12,'o').rect(4,2,7,11,'l').rect(11,4,1,9,'p').rect(4,13,7,2,'o').rect(4,4,5,1,'p').rect(4,7,6,1,'p').rect(4,10,4,1,'p')
    icons['sign']=Glyph().rect(1,3,14,8,'o').rect(2,4,12,6,'w').rect(2,4,12,1,'h').rect(3,6,4,1,'d').rect(9,6,3,1,'d').rect(3,8,9,1,'b').rect(7,11,3,4,'o').rect(8,11,1,3,'w')
    icons['villager']=Glyph().rect(4,1,8,13,'o').rect(3,3,10,8,'o').rect(4,2,8,3,'b').rect(4,5,8,7,'n').rect(5,5,6,2,'d').rect(5,6,2,1,'l').rect(9,6,2,1,'l').rect(6,6,1,1,'g').rect(9,6,1,1,'g').rect(7,7,2,5,'d').rect(7,7,1,4,'N').rect(5,12,6,2,'s').rect(3,14,10,2,'b')
    g=Glyph().rect(2,8,12,5,'o').rect(3,9,10,3,'p').rect(4,12,8,2,'i').rect(5,5,2,5,'d').rect(10,3,2,7,'d').rect(5,4,2,2,'R').rect(10,2,2,2,'R').rect(7,10,4,1,'r').rect(2,10,2,1,'a')
    icons['repeater']=g
    icons['chest']=Glyph().rect(2,3,12,11,'o').rect(3,4,10,3,'w').rect(3,4,10,1,'h').rect(3,7,10,2,'d').rect(3,9,10,4,'b').rect(3,10,1,3,'w').rect(12,10,1,3,'d').rect(7,7,2,4,'o').rect(7,8,2,2,'h')
    icons['item_frame']=Glyph().rect(2,2,12,12,'o').rect(3,3,10,10,'h').rect(4,4,8,8,'b').rect(5,5,6,6,'d').rect(7,6,2,4,'p').rect(6,7,4,2,'p').rect(3,12,10,1,'w')
    # Thinking: open book over a red-topped obsidian table, cyan corners.
    icons['enchanting_table']=Glyph().rect(2,8,12,6,'o').rect(3,9,10,4,'k').rect(3,8,10,2,'r').rect(3,13,10,1,'s').rect(2,10,2,3,'t').rect(12,10,2,3,'t').rect(3,10,1,2,'T').rect(12,10,1,2,'T').rect(3,2,4,1,'o').rect(9,2,4,1,'o').rect(2,3,12,4,'o').rect(3,3,4,3,'l').rect(9,3,4,3,'p').rect(4,6,3,1,'p').rect(9,6,3,1,'h').rect(7,4,2,4,'d').rect(5,4,2,1,'h').rect(9,4,2,1,'h')
    # B7 refusal: original stepped red barrier, distinct from a retry arrow.
    icons['barrier']=Glyph().rect(4,1,8,2,'r').rect(2,3,12,2,'r').rect(1,5,3,6,'r').rect(12,5,3,6,'r').rect(2,11,12,2,'r').rect(4,13,8,2,'r').steps(3,10,5,2,-2,3,3,'R').rect(4,1,7,1,'R').rect(1,5,1,5,'R')
    icons['splash_healing_potion'] = splash_potion()
    icons['splash_harming_potion'] = splash_potion(harming=True)
    return icons

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sheet',action='store_true')
    args=parser.parse_args()
    icons=glyphs()
    for name,glyph in icons.items():
        (ROOT/'skin/sprites'/f'tool_item_{name}.svg').write_text(glyph.svg(),encoding='utf-8',newline='\n')
    if args.sheet:
        from PIL import Image, ImageDraw
        sheet=Image.new('RGB',(640,((len(icons)+4)//5)*150),'#e3dfd3'); draw=ImageDraw.Draw(sheet)
        for i,(name,glyph) in enumerate(icons.items()):
            im=Image.new('RGBA',(16,16))
            for y,row in enumerate(glyph.pixels):
                for x,c in enumerate(row):
                    if c!='.': im.putpixel((x,y),tuple(bytes.fromhex(PALETTE[c][1:]))+(255,))
            im=im.resize((96,96),Image.Resampling.NEAREST);x=(i%5)*128;y=(i//5)*150
            sheet.paste(im,(x+16,y+12),im);draw.text((x+4,y+116),name,fill='#30291f')
        (ROOT/'.tmp').mkdir(exist_ok=True);sheet.save(ROOT/'.tmp/b1-original-icons.png')
    print(f'{len(icons)} original 16px item glyphs generated')

if __name__=='__main__': main()
