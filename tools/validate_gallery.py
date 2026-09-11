"""Validate the offline gallery using only the Python standard library."""
import json
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

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("src", "href"):
            if attrs.get(key):
                self.links.append(attrs[key])
        if tag == "img":
            self.images.append(attrs.get("src", ""))
        if tag == "h2":
            self.heading = ""

    def handle_data(self, data):
        if self.heading is not None:
            self.heading += data

    def handle_endtag(self, tag):
        if tag == "h2" and self.heading is not None:
            self.headings.append(self.heading.strip())
            self.heading = None


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    clips = manifest["clips"]
    labels = [clip["label"] for clip in clips]
    numbers = [int(label.split()[0]) for label in labels]
    require(len(set(numbers)) == len(numbers), "Duplicate clip numbers")
    require(numbers == sorted(numbers), "Manifest clips are not in numeric order")
    gifs = [clip["slug"] + ".gif" for clip in clips]
    require(len(set(gifs)) == len(gifs), "Duplicate clip filenames")
    for clip, name in zip(clips, gifs):
        asset = (ROOT / name).resolve()
        require(asset.parent == ROOT, f"Nonportable clip path: {name}")
        require(asset.is_file(), f"Missing GIF: {name}")
        with asset.open("rb") as stream:
            require(stream.read(6) in (b"GIF87a", b"GIF89a"), f"Invalid GIF: {name}")
        require(clip["fps"] == 24, f"Unexpected frame rate: {clip['label']}")
        require(clip["duration_frames"] > 0, f"Invalid duration: {clip['label']}")
    pages = ["index.html", f"revision_{manifest['revision']}.html"]
    for name in pages:
        parser = GalleryParser()
        parser.feed((ROOT / name).read_text(encoding="utf-8"))
        require(parser.headings == labels, f"Clip labels/order mismatch: {name}")
        require([unquote(urlsplit(src).path) for src in parser.images] == gifs,
                f"Preview inventory/order mismatch: {name}")
        for link in parser.links:
            url = urlsplit(link)
            require(not url.scheme and not url.netloc, f"Non-local link in {name}: {link}")
            if not url.path:
                continue
            target = (ROOT / unquote(url.path)).resolve()
            require(target.is_relative_to(ROOT), f"Link escapes project: {link}")
            require(target.is_file(), f"Broken link in {name}: {link}")
    print(f"PASS: {len(clips)} clips, numeric order, GIF headers, and all links in {', '.join(pages)}.")


if __name__ == "__main__":
    main()
