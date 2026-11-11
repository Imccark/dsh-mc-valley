"""Original C1 pixel bookshelf and six-pixel amethyst frame; no reference reads."""
from pathlib import Path
import re

OUT = Path(__file__).resolve().parent.parent / 'skin/sprites'


def bookshelf():
    rects = []
    def r(x, y, w, h, fill):
        rects.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')
    r(0, 0, 32, 20, '#62442c')
    for y in (0, 9, 18):
        r(0, y, 32, 2, '#b1854d'); r(0, y, 32, 1, '#d4aa6b')
    for y, offset in ((2, 0), (11, 2)):
        for i, (dark, light) in enumerate((('#356777','#6aa5ac'),('#8d3e36','#c4704b'),('#827137','#c3ab57'),('#45623b','#7d9760'),('#5e4979','#9681ae'),('#8b6039','#c0915d'))):
            x = (i * 5 + offset) % 30
            r(x, y + i % 2, 4, 7 - i % 2, dark)
            r(x + 1, y + i % 2, 1, 7 - i % 2, light)
            r(x + 1, y + 4, 2, 1, '#c3af77')
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 20" shape-rendering="crispEdges">' + ''.join(rects) + '</svg>\n'


def amethyst_frame():
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" shape-rendering="crispEdges">
<!-- Original six-pixel nine-slice; transparent center and stepped corners. -->
<path fill="#342a3e" fill-rule="evenodd" d="M2 0h20v2h2v20h-2v2H2v-2H0V2h2zM6 6v12h12V6z"/>
<path fill="#9777ac" d="M2 1h20v2H3v19H1V2h1z"/>
<path fill="#564064" d="M21 3h2v19h-1v1H3v-2h18z"/>
<path fill="#b79bc8" d="M3 3h3v1H4v2H3zm15 0h3v3h-1V4h-2zM3 18h1v2h2v1H3zm17 0h1v3h-3v-1h2z"/>
<path fill="#6d4c81" d="M4 4h2v2H4zm14 0h2v2h-2zM4 18h2v2H4zm14 0h2v2h-2z"/>
</svg>\n'''


def theme_cubes():
    day = (OUT / 'grass_cube.svg').read_text(encoding='utf-8')
    night = day
    for a,b in {'#805329':'#3f3c55','#57391f':'#292940','#57902a':'#425b70','#a07139':'#55536c','#624020':'#34334d','#3e741f':'#34445e','#79532b':'#43415a','#402d1b':'#24263c','#80b838':'#384e7c','#9bcc48':'#516798','#6fa52d':'#30436c','#31451d':'#20253c','#354720':'#252940'}.items():
        night = night.replace(a,b)
    night = night.replace('</svg>', '<g clip-path="url(#top)" fill="#f8edbd"><path d="M17 4h3v2h-2v3h3v2h-4V9h-2V6h2z"/><path d="M8 9h1v1H8zm17-2h1v1h-1z"/></g></svg>')
    inner = re.sub(r'^<svg[^>]*>', '', night).replace('</svg>', '')
    inner = inner.replace('id="','id="night-').replace('url(#','url(#night-')
    system = day.replace('</svg>', '<defs><clipPath id="night-half"><path d="M18 0h18v40H18z"/></clipPath></defs><g clip-path="url(#night-half)">'+inner+'</g></svg>')
    return night, system


if __name__ == '__main__':
    night, system = theme_cubes()
    for name, svg in [('settings_bookshelf.svg', bookshelf()), ('amethyst_frame.svg', amethyst_frame()), ('theme_night_cube.svg', night), ('theme_system_cube.svg', system)]:
        (OUT / name).write_text(svg, encoding='utf-8', newline='\n')
        print(OUT / name)
