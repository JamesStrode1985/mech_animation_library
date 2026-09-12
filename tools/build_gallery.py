"""Rebuild the offline gallery from manifest.json (Python standard library)."""
import html
from string import Template
from gallery_data import ROOT, libraries, pages_for


def build(mech, data, catalog):
    clips = data['clips']
    groups = data['gallery_groups']
    esc = html.escape
    sections = []
    navigation = []
    for group in groups:
        members = [c for c in clips if c['gallery_group'] == group['id']]
        if not members:
            continue
        number_range = members[0]['label'].split()[0] + '–' + members[-1]['label'].split()[0]
        navigation.append(f'<a href="#{group["id"]}">{esc(group["title"])}</a>')
        cards = []
        for clip in members:
            gif = mech['animation_dir'] + '/' + clip['slug'] + '.gif'
            tag = 'LOOP' if clip['loop'] else 'ONE-SHOT'
            travel_note = (f'<p class="timing">{clip["controller_distance_units"]:g} units of controller travel shown</p>'
                           if clip.get('controller_preview_travel') and 'controller_distance_units' in clip else '')
            cards.append(f'''<article><a href="{gif}"><img loading="lazy" src="{gif}" alt="{esc(clip['label'])} animation"></a>
<div class="details"><h3>{esc(clip['label'])}</h3><p class="tag">{tag} · {clip['duration_frames']/clip['fps']:.2f}s · {esc(clip['category'])}</p>
<p class="timing">Frames 1–{clip['duration_frames']+1} · {clip['nominal_speed_units_per_s']:.3f} units/s</p>{travel_note}
<details><summary>Original Blender Action</summary><code>{esc(clip['action'])}</code></details></div></article>''')
        sections.append(f'<section id="{group["id"]}" aria-labelledby="heading-{group["id"]}"><h2 class="group-heading" id="heading-{group["id"]}">{esc(group["title"])}<span class="range">{number_range}</span></h2><div class="grid">'+''.join(cards)+'</div></section>')
    template = Template((ROOT / 'templates/gallery.html').read_text(encoding='utf-8'))
    mech_navigation = []
    for other, inventory in catalog:
        current = ' aria-current="page"' if other['id'] == mech['id'] else ''
        count = len(inventory['clips'])
        status = f'{count} previews' if count else 'Awaiting previews'
        mech_navigation.append(f'<a href="{esc(other["page"])}"{current}><strong>{esc(other["name"])}</strong><span>{status}</span></a>')
    project_links = [f'<a href="{esc(mech["manifest"])}">Manifest + verification</a>']
    if clips:
        project_links.insert(0, f'<a href="{esc(mech["contact_sheet"])}">Contact sheet</a>')
    if mech.get('guide'):
        project_links.append(f'<a href="{esc(mech["guide"])}">Integration notes</a>')
    project_links.append('<a href="docs/adding-a-mech.md">Adding animations</a>')
    notes = (ROOT / mech['notes_template']).read_text(encoding='utf-8') if mech.get('notes_template') else ''
    intro = f'{len(clips)} animation previews, grouped by movement and numbered in viewing order. Choose a group below to jump to it.' if clips else 'A dedicated animation library for this mech.'
    if not clips:
        sections.append('<div class="empty-state"><div class="eyebrow">LIBRARY READY</div><h2>No animation previews yet</h2><p>This mech has its own screen. Its exported animations will appear here when they are added.</p><p class="muted">Each mech keeps its own clips, numbering, and source Actions.</p></div>')
    page = template.substitute(
        mech_name=esc(mech['name']), mech_navigation=''.join(mech_navigation),
        intro=intro, notes=notes, project_links=''.join(project_links),
        group_navigation='<nav aria-label="Animation groups">'+''.join(navigation)+'</nav>' if navigation else '',
        sections=''.join(sections))
    for name in pages_for(mech, data):
        (ROOT / name).write_text(page, encoding='utf-8')
    print(f"Built {mech['name']}: {len(clips)} clips in {len(groups)} groups.")


def main():
    catalog = libraries()
    for mech, data in catalog:
        build(mech, data, catalog)


if __name__ == '__main__':
    main()
