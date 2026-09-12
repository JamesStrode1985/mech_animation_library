# Mech animation libraries

An offline site with separate animation screens for each mech. M18 Hellcat Ghost and Sherman Walker each have 47 previews, grouped by movement and numbered 01–47. Sherman uses its own rig, cadence, weapon controls, and articulated ammunition feed.

Open [index.html](index.html) in a browser and use the mech switcher, or open [Sherman Walker](sherman-walker.html) directly. No installation, build step, internet connection, or server is required to view the gallery. The repository includes final previews and metadata; editable Blender models and Actions are maintained separately.

## Project layout

```text
index.html                         Main generated gallery
revision_6.html                    Generated compatibility page for existing bookmarks
sherman-walker.html                Generated Sherman Walker screen
assets/animations/                Final numbered GIF previews
assets/animations/sherman-walker/  Sherman Walker animation previews
assets/contact_sheet.png           Grouped preview sheet
styles/gallery.css                 Gallery styling
templates/gallery.html             Gallery page template
data/manifest.json                 Clip inventory, grouping, timing, and source mapping
data/mechs.json                    Mech registry, screen paths, and asset locations
data/mechs/sherman-walker.json      Separate Sherman Walker inventory
data/verification/                 Detailed verification reports
docs/animation-guide.md            Rig integration, playback, and export notes
docs/adding-a-mech.md               Add clips and register another mech
tools/                             Build and validation scripts
```

[index.html](index.html) and [revision_6.html](revision_6.html) remain identical Hellcat pages. Each mech screen uses the shared template and stylesheet with its own manifest. Edit those sources, then rebuild instead of editing generated pages individually. Hellcat-specific notes live in `templates/hellcat-notes.html`.

## Building and validating

Use Python 3.9 or newer. HTML generation and validation use only the standard library. Rebuilding the contact sheet additionally requires Pillow 9.1 or newer.

From the repository root:

```text
python tools/build_gallery.py
python tools/build_contact_sheet.py
python tools/validate_gallery.py
python tools/test_multi_mech.py
git diff --check
```

The tools locate the project relative to their own files, so they also work when called from another directory. HTML generation does not require Blender or raw render frames. The contact sheet is built from the final GIFs. Visually review changed previews and layout in addition to running validation.

## Editing animations

See [adding a mech or its animations](docs/adding-a-mech.md) for the multi-mech workflow. The paths below refer to the existing Hellcat library; Sherman uses its own manifest and GIF folder. Both build commands process all registered libraries.

- Add or replace final GIFs in `assets/animations/` and update [data/manifest.json](data/manifest.json).
- Keep related clips adjacent, with consecutive gallery numbers. Update filenames and labels together when renumbering.
- Preserve `source_label` and `action` as the original Blender identifiers unless those source Actions have actually been renamed. Historical verification records use the original source labels.
- Rebuild both gallery pages and the contact sheet after inventory changes.
- Keep raw `frame_*.png` images in ignored `build/` and release ZIPs in ignored `dist/`. Commit final previews, generated pages, documentation, and relevant verification reports.
- The previous Blender rendering scripts outside this repository are legacy local tools and are not required to view or rebuild this gallery.

See the [animation guide](docs/animation-guide.md) for playback, rig controls, controller movement, and export details, and the [weapon aiming report](data/verification/weapon_aim_verification.json) for its checked poses and limitations.
