"""Rebuild the offline gallery from manifest.json (Python standard library)."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = '''
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#151a1d;color:#e8e9df;font:16px/1.5 system-ui,sans-serif}
header,main,footer{max-width:1500px;margin:auto;padding:28px}header{padding-top:46px}h1{font-size:clamp(32px,5vw,58px);line-height:1.05;margin:12px 0 22px;letter-spacing:-2px}.eyebrow{letter-spacing:3px;color:#b6c195;font-size:12px}
.intro{max-width:880px;color:#c3c9c6}.note{border-left:3px solid #a4b786;padding:12px 18px;background:#242c29;max-width:1060px}
nav{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}a{color:#cedfa9}nav a{border:1px solid #4d5a45;padding:8px 13px;text-decoration:none;border-radius:6px}a:focus-visible,summary:focus-visible{outline:2px solid #cedfa9;outline-offset:4px}
section{margin-bottom:48px;scroll-margin-top:20px}.group-heading{font-size:26px;margin:0 0 18px;border-bottom:1px solid #465044;padding-bottom:12px}.range{color:#bdcaa9;font-size:16px;font-weight:400;margin-left:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(270px,100%),1fr));gap:20px}article{background:#252b2e;border-radius:12px;overflow:hidden;border:1px solid #333e3e}article img{display:block;width:100%;height:330px;object-fit:contain;background:#363c41}.details{padding:16px}h3{font-size:20px;margin:0 0 7px}.tag{font-size:12px;letter-spacing:.6px;color:#bdcaa9}code{font-size:12px;word-break:break-word;color:#d3d8d2}.timing,summary{font-size:12px;color:#a9b3ad}summary{cursor:pointer}footer{color:#a9b3ad;font-size:13px}
'''


def main():
    data = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    clips = data['clips']
    groups = data['gallery_groups']
    esc = html.escape
    sections = []
    navigation = []
    for group in groups:
        members = [c for c in clips if c['gallery_group'] == group['id']]
        number_range = members[0]['label'].split()[0] + '–' + members[-1]['label'].split()[0]
        navigation.append(f'<a href="#{group["id"]}">{esc(group["title"])}</a>')
        cards = []
        for clip in members:
            gif = clip['slug'] + '.gif'
            tag = 'LOOP' if clip['loop'] else 'ONE-SHOT'
            cards.append(f'''<article><a href="{gif}"><img loading="lazy" src="{gif}" alt="{esc(clip['label'])} animation"></a>
<div class="details"><h3>{esc(clip['label'])}</h3><p class="tag">{tag} · {clip['duration_frames']/clip['fps']:.2f}s · {esc(clip['category'])}</p>
<p class="timing">Frames 1–{clip['duration_frames']+1} · {clip['nominal_speed_units_per_s']:.3f} units/s</p>
<details><summary>Original Blender Action</summary><code>{esc(clip['action'])}</code></details></div></article>''')
        sections.append(f'<section id="{group["id"]}" aria-labelledby="heading-{group["id"]}"><h2 class="group-heading" id="heading-{group["id"]}">{esc(group["title"])}<span class="range">{number_range}</span></h2><div class="grid">'+''.join(cards)+'</div></section>')
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HELLCAT Animation Library</title><style>{CSS}</style></head>
<body><header><div class="eyebrow">M18 HELLCAT GHOST / MOTION STUDIES</div><h1>Animation library</h1>
<p class="intro">{len(clips)} animation previews, grouped by movement and numbered in viewing order. Choose a group below to jump to it.</p>
<p class="note"><strong>Game controller setup:</strong> gameplay Actions retain a stationary root. Preview travel comes from a temporary controller simulation. Hill clips use an 8° reference slope; terrain clips are authored examples to blend with runtime foot IK.</p>
<p class="note"><strong>Weapon aiming:</strong> the cannon and each armored pod have ±20° elevation relative to the hull. Clips 36–37 show continued tracking after the hull reaches its ±5° aiming allocation; clip 38 shows independent targets. These three previews show the updated pod spacing; earlier motion previews retain their prior model revision.</p>
<nav aria-label="Animation groups">{''.join(navigation)}</nav>
<nav aria-label="Project files"><a href="contact_sheet.png">Contact sheet</a><a href="README.md">Integration notes</a><a href="manifest.json">Manifest + verification</a></nav></header>
<main>{''.join(sections)}</main><footer>Gallery numbers follow the grouped viewing order. Original Blender Action identifiers remain available in each card and the manifest. Direction labels are from the mech's perspective.</footer></body></html>'''
    for name in ['index.html', f"revision_{data['revision']}.html"]:
        (ROOT / name).write_text(page, encoding='utf-8')
    print(f"Built {len(clips)} clips in {len(groups)} groups.")


if __name__ == '__main__':
    main()
