# HELLCAT animation library

An offline gallery of 46 in-place mech animation previews, grouped by movement and numbered 01–46.

Open [index.html](index.html) in a browser. No installation, build step, internet connection, or server is required to view the gallery. The repository includes final previews and metadata; the editable Blender model and Actions are maintained separately.

## Project layout

```text
index.html                         Main generated gallery
revision_6.html                    Generated compatibility page for existing bookmarks
assets/animations/                Final numbered GIF previews
assets/contact_sheet.png           Grouped preview sheet
styles/gallery.css                 Gallery styling
templates/gallery.html             Gallery page template
data/manifest.json                 Clip inventory, grouping, timing, and source mapping
data/verification/                 Detailed verification reports
docs/animation-guide.md            Rig integration, playback, and export notes
tools/                             Build and validation scripts
```

[index.html](index.html) and [revision_6.html](revision_6.html) are generated from the same template and contain the same gallery. Edit the template, stylesheet, or manifest, then rebuild instead of editing generated pages individually.

## Building and validating

Use Python 3.9 or newer. HTML generation and validation use only the standard library. Rebuilding the contact sheet additionally requires Pillow 9.1 or newer.

From the repository root:

```text
python tools/build_gallery.py
python tools/build_contact_sheet.py
python tools/validate_gallery.py
git diff --check
```

The tools locate the project relative to their own files, so they also work when called from another directory. HTML generation does not require Blender or raw render frames. The contact sheet is built from the final GIFs. Visually review changed previews and layout in addition to running validation.

## Editing animations

- Add or replace final GIFs in `assets/animations/` and update [data/manifest.json](data/manifest.json).
- Keep related clips adjacent, with consecutive gallery numbers. Update filenames and labels together when renumbering.
- Preserve `source_label` and `action` as the original Blender identifiers unless those source Actions have actually been renamed. Historical verification records use the original source labels.
- Rebuild both gallery pages and the contact sheet after inventory changes.
- Keep raw `frame_*.png` images in ignored `build/` and release ZIPs in ignored `dist/`. Commit final previews, generated pages, documentation, and relevant verification reports.
- The previous Blender rendering scripts outside this repository are legacy local tools and are not required to view or rebuild this gallery.

See the [animation guide](docs/animation-guide.md) for playback, rig controls, controller movement, and export details, and the [weapon aiming report](data/verification/weapon_aim_verification.json) for its checked poses and limitations.
