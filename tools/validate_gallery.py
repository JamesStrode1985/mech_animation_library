"""Validate the offline gallery using only the Python standard library."""
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class GalleryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.images = []
        self.headings = []
        self.heading = None
        self.ids = []
        self.sections = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
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


def main():
    manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
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
    gifs = ['assets/animations/' + clip["slug"] + ".gif" for clip in clips]
    require(len(set(gifs)) == len(gifs), "Duplicate clip filenames")
    for clip, name in zip(clips, gifs):
        asset = (ROOT / name).resolve()
        require(asset.parent == ROOT / 'assets/animations', f"Nonportable clip path: {name}")
        require(asset.is_file(), f"Missing GIF: {name}")
        with asset.open("rb") as stream:
            require(stream.read(6) in (b"GIF87a", b"GIF89a"), f"Invalid GIF: {name}")
        require(clip["fps"] == 24, f"Unexpected frame rate: {clip['label']}")
        require(clip["duration_frames"] > 0, f"Invalid duration: {clip['label']}")
    pages = ["index.html", f"revision_{manifest['revision']}.html"]
    for name in pages:
        parser = GalleryParser()
        parser.feed((ROOT / name).read_text(encoding="utf-8"))
        require('styles/gallery.css' in parser.links, f"Missing stylesheet: {name}")
        require(parser.headings == labels, f"Clip labels/order mismatch: {name}")
        require(parser.sections == groups, f"Group order mismatch: {name}")
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
    require((ROOT/'index.html').read_bytes() == (ROOT/pages[1]).read_bytes(),
            'Compatibility gallery differs from index.html')
    for name in ['README.md', 'docs/animation-guide.md']:
        document = ROOT / name
        for link in re.findall(r'\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (document.parent / unquote(url.path)).resolve()
            require(target.is_relative_to(ROOT) and target.exists(), f"Broken documentation link in {name}: {link}")
    report = json.loads((ROOT/'data/verification/weapon_aim_verification.json').read_text(encoding='utf-8'))
    require(report == manifest['weapon_elevation_verification'], 'Weapon verification copies disagree')
    for key, filename in [('death_animations_verification','death_animations.json'), ('dodge_animations_verification','dodge_animations.json'), ('terrain_revision_verification','terrain_revision.json')]:
        if key in manifest:
            report = json.loads((ROOT/'data/verification'/filename).read_text(encoding='utf-8'))
            require(report == manifest[key], f'Verification copies disagree: {filename}')
    print(f"PASS: {len(clips)} clips, numeric order, GIF headers, and all links in {', '.join(pages)}.")


if __name__ == "__main__":
    main()
