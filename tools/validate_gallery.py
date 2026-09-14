"""Validate the offline gallery using only the Python standard library."""
import json
import re
from html.parser import HTMLParser
from gallery_data import ROOT, libraries, pages_for
from urllib.parse import unquote, urlsplit


class GalleryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.images = []
        self.headings = []
        self.heading = None
        self.ids = []
        self.sections = []
        self.current_pages = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('aria-current') == 'page':
            self.current_pages.append(attrs.get('href'))
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if tag == 'section':
            self.sections.append(attrs.get('id'))
        for key in ("src", "href"):
            if attrs.get(key):
                self.links.append(attrs[key])
        if tag == "img":
            self.images.append(attrs.get("src", ""))
        if tag == "h3":
            self.heading = ""

    def handle_data(self, data):
        if self.heading is not None:
            self.heading += data

    def handle_endtag(self, tag):
        if tag == "h3" and self.heading is not None:
            self.headings.append(self.heading.strip())
            self.heading = None


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_library(mech, manifest, catalog):
    clips = manifest["clips"]
    labels = [clip["label"] for clip in clips]
    numbers = [int(label.split()[0]) for label in labels]
    require(len(set(numbers)) == len(numbers), "Duplicate clip numbers")
    require(numbers == sorted(numbers), "Manifest clips are not in numeric order")
    require(numbers == list(range(1,len(clips)+1)), "Gallery numbering has gaps")
    groups = [group['id'] for group in manifest['gallery_groups']]
    require(len(groups) == len(set(groups)), "Duplicate gallery groups")
    require(all(clip['gallery_group'] in groups for clip in clips), "Unknown clip group")
    group_order = [groups.index(clip['gallery_group']) for clip in clips]
    require(group_order == sorted(group_order), "Related clips are not adjacent")
    gifs = [mech['animation_dir'] + '/' + clip["slug"] + ".gif" for clip in clips]
    require(len(set(gifs)) == len(gifs), "Duplicate clip filenames")
    for clip, name in zip(clips, gifs):
        asset = (ROOT / name).resolve()
        require(asset.parent == ROOT / mech['animation_dir'], f"Nonportable clip path: {name}")
        require(asset.is_file(), f"Missing GIF: {name}")
        with asset.open("rb") as stream:
            require(stream.read(6) in (b"GIF87a", b"GIF89a"), f"Invalid GIF: {name}")
        require(clip["fps"] == 24, f"Unexpected frame rate: {clip['label']}")
        require(clip["duration_frames"] > 0, f"Invalid duration: {clip['label']}")
    pages = pages_for(mech, manifest)
    for name in pages:
        parser = GalleryParser()
        parser.feed((ROOT / name).read_text(encoding="utf-8"))
        require(parser.current_pages == [mech['page']], f'Incorrect selected mech: {name}')
        require(all(other['page'] in parser.links for other, _ in catalog), f'Missing mech navigation: {name}')
        require('styles/gallery.css' in parser.links, f"Missing stylesheet: {name}")
        require(parser.headings == labels, f"Clip labels/order mismatch: {name}")
        require(parser.sections == [group for group in groups if any(c['gallery_group'] == group for c in clips)], f"Group order mismatch: {name}")
        require(len(parser.ids) == len(set(parser.ids)), f"Duplicate HTML IDs: {name}")
        require([unquote(urlsplit(src).path) for src in parser.images] == gifs,
                f"Preview inventory/order mismatch: {name}")
        for link in parser.links:
            url = urlsplit(link)
            require(not url.scheme and not url.netloc, f"Non-local link in {name}: {link}")
            if not url.path:
                if url.fragment:
                    require(unquote(url.fragment) in parser.ids, f"Broken group link: {link}")
                continue
            target = (ROOT / unquote(url.path)).resolve()
            require(target.is_relative_to(ROOT), f"Link escapes project: {link}")
            require(target.is_file(), f"Broken link in {name}: {link}")
    for alias in pages[1:]:
        require((ROOT/pages[0]).read_bytes() == (ROOT/alias).read_bytes(),
                'Compatibility gallery differs from main mech page')
    print(f"PASS: {mech['name']}: {len(clips)} clips, numbering, GIF headers, page isolation, and local links.")


def main():
    catalog = libraries()
    for key in ['id', 'page', 'manifest', 'animation_dir', 'contact_sheet']:
        values = [mech[key] for mech, _ in catalog]
        require(len(set(values)) == len(values), f'Duplicate mech {key}')
    for mech, manifest in catalog:
        if manifest.get('verification_report'):
            report_path = (ROOT / manifest['verification_report']).resolve()
            require(report_path.is_relative_to(ROOT) and report_path.is_file(), 'Missing mech verification report')
        require(re.fullmatch(r'[a-z0-9-]+', mech['id']), 'Invalid mech ID')
        require(re.fullmatch(r'[a-z0-9_-]+\.html', mech['page']), 'Page must be a root HTML filename')
        for key in ['manifest', 'animation_dir', 'contact_sheet', 'notes_template', 'guide']:
            if key not in mech:
                continue
            path = (ROOT / mech[key]).resolve()
            require(path.is_relative_to(ROOT), f'Path escapes repository: {key}')
            if key != 'contact_sheet' or manifest['clips']:
                require(path.exists(), f'Missing mech path: {mech[key]}')
        validate_library(mech, manifest, catalog)
    manifest = next(data for mech, data in catalog if mech['id'] == 'hellcat')
    guide_paths = {mech['guide'] for mech, _ in catalog if mech.get('guide')}
    for name in sorted({'README.md', 'docs/adding-a-mech.md'} | guide_paths):
        document = ROOT / name
        for link in re.findall(r'\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (document.parent / unquote(url.path)).resolve()
            require(target.is_relative_to(ROOT) and target.exists(), f"Broken documentation link in {name}: {link}")
    report = json.loads((ROOT/'data/verification/weapon_aim_verification.json').read_text(encoding='utf-8'))
    require(report == manifest['weapon_elevation_verification'], 'Weapon verification copies disagree')
    for key, filename in [('death_animations_verification','death_animations.json'), ('dodge_animations_verification','dodge_animations.json'), ('terrain_revision_verification','terrain_revision.json'), ('dance_party_verification','dance_party.json'), ('time_warp_verification','time_warp.json')]:
        if key in manifest:
            report = json.loads((ROOT/'data/verification'/filename).read_text(encoding='utf-8'))
            require(report == manifest[key], f'Verification copies disagree: {filename}')
    print("PASS: documentation links and historical verification reports.")


if __name__ == "__main__":
    main()
