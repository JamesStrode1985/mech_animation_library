"""Rebuild the numbered contact sheet from final GIFs. Requires Pillow."""
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def main():
    data = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    groups = [(g, [c for c in data['clips'] if c['gallery_group'] == g['id']]) for g in data['gallery_groups']]
    height = 100 + sum(48 + math.ceil(len(clips)/5)*275 for _, clips in groups)
    sheet = Image.new('RGB', (1280, height), '#151a1d')
    draw = ImageDraw.Draw(sheet)
    def font(size):
        for name in ('arial.ttf', 'DejaVuSans.ttf'):
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                pass
        return ImageFont.load_default()
    draw.text((24, 18), 'HELLCAT / ANIMATION LIBRARY', font=font(30), fill='#e8e9df')
    draw.text((24, 60), f"{len(data['clips'])} IN-PLACE ANIMATIONS / GROUPED BY MOVEMENT / 24 FPS", font=font(14), fill='#b6c195')
    y = 100
    for group, clips in groups:
        draw.text((24, y+8), group['title'].upper(), font=font(22), fill='#cedfa9')
        y += 48
        for i, clip in enumerate(clips):
            x, cy = (i%5)*256+6, y+(i//5)*275
            draw.rounded_rectangle((x,cy,x+244,cy+263), radius=9, fill='#252b2e')
            with Image.open(ROOT / (clip['slug']+'.gif')) as gif:
                gif.seek(gif.n_frames//3)
                thumb = gif.convert('RGB')
                thumb.thumbnail((244,220), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (x+(244-thumb.width)//2,cy+(220-thumb.height)//2))
            label_font = font(16)
            if draw.textlength(clip['label'], font=label_font)>228:
                label_font = font(14)
            draw.text((x+8,cy+223),clip['label'],font=label_font,fill='#edeedf')
            tag = 'LOOP' if clip['loop'] else 'ONE-SHOT'
            draw.text((x+8,cy+245),tag,font=font(12),fill='#b6c195')
        y += math.ceil(len(clips)/5)*275
    sheet.save(ROOT/'contact_sheet.png')
    print(f'Built grouped contact sheet: 1280 x {height}.')


if __name__ == '__main__':
    main()
