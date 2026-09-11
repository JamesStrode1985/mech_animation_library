"""Rebuild the offline gallery from manifest.json (Python standard library)."""
import html
import json
from string import Template
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]



def main():
    data = json.loads((ROOT / 'data/manifest.json').read_text(encoding='utf-8'))
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
            gif = 'assets/animations/' + clip['slug'] + '.gif'
            tag = 'LOOP' if clip['loop'] else 'ONE-SHOT'
            cards.append(f'''<article><a href="{gif}"><img loading="lazy" src="{gif}" alt="{esc(clip['label'])} animation"></a>
<div class="details"><h3>{esc(clip['label'])}</h3><p class="tag">{tag} · {clip['duration_frames']/clip['fps']:.2f}s · {esc(clip['category'])}</p>
<p class="timing">Frames 1–{clip['duration_frames']+1} · {clip['nominal_speed_units_per_s']:.3f} units/s</p>
<details><summary>Original Blender Action</summary><code>{esc(clip['action'])}</code></details></div></article>''')
        sections.append(f'<section id="{group["id"]}" aria-labelledby="heading-{group["id"]}"><h2 class="group-heading" id="heading-{group["id"]}">{esc(group["title"])}<span class="range">{number_range}</span></h2><div class="grid">'+''.join(cards)+'</div></section>')
    template = Template((ROOT / 'templates/gallery.html').read_text(encoding='utf-8'))
    page = template.substitute(clip_count=len(clips), navigation=''.join(navigation), sections=''.join(sections))
    for name in ['index.html', f"revision_{data['revision']}.html"]:
        (ROOT / name).write_text(page, encoding='utf-8')
    print(f"Built {len(clips)} clips in {len(groups)} groups.")


if __name__ == '__main__':
    main()
