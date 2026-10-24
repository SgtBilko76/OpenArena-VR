#!/usr/bin/env python3
"""App icon from OpenArena's own logo (the emblem in the official 0.8.8 release's Mac app,
OpenArena 0.8.8 r28.app/Contents/Resources/ioquake3.icns). Black emblem on a white tile so it
shows on the Quest's dark library. Writes res/mipmap-*/ic_launcher.png + android/art/."""
import pathlib, sys, zipfile, io
from PIL import Image

REPO = pathlib.Path(__file__).resolve().parents[2]
ZIP = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                   pathlib.Path.home() / 'workspace/openarena-src/openarena-0.8.8.zip')
RES = REPO / 'android/app/src/main/res'
ART = REPO / 'android/art'

with zipfile.ZipFile(ZIP) as z:
    data = z.read('openarena-0.8.8/OpenArena 0.8.8 r28.app/Contents/Resources/ioquake3.icns')
logo = Image.open(io.BytesIO(data)); logo.load(); logo = logo.convert('RGBA')
logo = logo.crop(logo.getbbox())

S = 512; margin = 0.12
tile = Image.new('RGBA', (S, S), (255, 255, 255, 255))
inner = int(S * (1 - 2 * margin))
scale = inner / max(logo.size)
lg = logo.resize((round(logo.width * scale), round(logo.height * scale)), Image.LANCZOS)
tile.alpha_composite(lg, ((S - lg.width) // 2, (S - lg.height) // 2))
tile = tile.convert('RGB')

ART.mkdir(parents=True, exist_ok=True)
logo.save(ART / 'openarena-logo.png'); tile.save(ART / 'icon-512.png')
for d, px in (('mdpi', 48), ('hdpi', 72), ('xhdpi', 96), ('xxhdpi', 144), ('xxxhdpi', 192)):
    out = RES / f'mipmap-{d}'; out.mkdir(exist_ok=True)
    tile.resize((px, px), Image.LANCZOS).save(out / 'ic_launcher.png')
    print(f'mipmap-{d}/ic_launcher.png {px}px')
