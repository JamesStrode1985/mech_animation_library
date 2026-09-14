# Multiple mech libraries

The site has a separate static HTML screen for each mech. The switcher on every
screen links to the others. It works offline with ordinary links; there is no
server, runtime JSON fetch, or browser storage requirement.

## Current libraries

| Mech | Screen | Clip inventory | GIF folder |
| --- | --- | --- | --- |
| M18 Hellcat Ghost | [index.html](../index.html) | [manifest](../data/manifest.json) | `assets/animations/` |
| Sherman Walker | [sherman-walker.html](../sherman-walker.html) | [manifest](../data/mechs/sherman-walker.json) | `assets/animations/sherman-walker/` |
| T1 Artillery Walker | [t1-artillery-walker.html](../t1-artillery-walker.html) | [manifest](../data/mechs/t1-artillery-walker.json) | `assets/animations/t1-artillery-walker/` |
| HT-01 Hover Tank | [hover-tank.html](../hover-tank.html) | [manifest](../data/mechs/hover-tank.json) | `assets/animations/hover-tank/` |

All four registered libraries contain 47 previews each. See the
[Sherman guide](sherman-animation-guide.md), [T1 guide](t1-animation-guide.md), and
[hover-tank guide](hover-animation-guide.md) for timing and rig details. The
editable Blender models and Actions remain separate from this site.

## Add Sherman Walker animations

1. Export final GIF previews into `assets/animations/sherman-walker/`.
2. Add groups and clip records to `data/mechs/sherman-walker.json`. Follow the
   example below, using the actual Blender Action name and export timing.
3. Number clips consecutively starting at 01 **within this mech**, with related
   clips adjacent in `gallery_groups` order. A Sherman `01_walk.gif` is independent
   of the Hellcat file of the same name.
4. Run the commands below, then open the Sherman page and review the previews.

Example record (illustrative only; not an existing animation):

```json
{
  "mech_id": "sherman-walker",
  "revision": 1,
  "gallery_groups": [{"id": "forward", "title": "Forward locomotion"}],
  "clips": [{
    "label": "01 Walk",
    "source_label": "01 Walk",
    "action": "REPLACE WITH ACTUAL BLENDER ACTION NAME",
    "slug": "01_walk",
    "gallery_group": "forward",
    "category": "Locomotion",
    "duration_frames": 48,
    "fps": 24,
    "loop": true,
    "nominal_speed_units_per_s": 0,
    "controller_preview_travel": false
  }]
}
```

Keep the 24 fps, in-place gameplay convention. Record actual preview/controller
travel separately from gameplay root motion. Preserve source labels and Actions.

```text
python tools/build_gallery.py
python tools/build_contact_sheet.py
python tools/validate_gallery.py
git diff --check
```

Both builders process every registered mech. Empty libraries get a page but no
contact sheet or contact-sheet link. Existing animation packaging scripts target
Hellcat; do not use them to package Sherman clips without adapting their manifest
and asset paths.

## Register another mech

Add an entry to [data/mechs.json](../data/mechs.json) with a unique `id`, `name`,
root-level HTML `page`, `manifest`, `animation_dir`, and `contact_sheet` path.
Create its manifest and GIF directory. An empty manifest needs `revision`,
`clips: []`, and `gallery_groups: []`. Commit a `.gitkeep` in an empty GIF directory.

Optional `notes_template` and `guide` paths provide model-specific notes. All paths
are relative to the repository root. Rebuild and validate to generate its screen
and add it to every mech switcher. No template changes are needed.

The existing Hellcat manifest and asset paths are retained for compatibility with
its packaging tools. `revision_6.html` remains a copy of its main page, including
the new switcher.
