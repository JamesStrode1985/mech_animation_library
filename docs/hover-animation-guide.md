# HT-01 Hover Tank animation integration

The hover tank has a complete 47-clip counterpart to the Hellcat library, numbered independently on `hover-tank.html`. The manifest records each Hellcat equivalent while preserving hover-specific Action names. All animation is authored for this tank's 23-bone rigid skin; no walker renders are reused.

## Motion and playback

- 01-05: slow hover (1.6 units/s), cruise (4.8), boost (9.6), and reverse travel.
- 06-08: speed-specific braking with counter-pitch and damped settling.
- 09-12: a vertical hop and three moving hops; moving versions retain forward trim before and after thrust.
- 13-16: lateral slides and strafing fire. The hull banks into travel while the turret aims on a different heading.
- 17-25: rough-ground hover corrections and uphill/downhill at all speeds, using 18-degree reference slopes.
- 26-35: hover idle, scan, turret turns, hull pitch/bank, landing brace, and staged cannon recoil.
- 36-38: hull pitch followed by further independent gun elevation, plus split weapon tracking.
- 39-41: front, rear, and side lift failures. The tank sinks and settles instead of performing leg-collapse animation.
- 42-45: forward hull ram and three boost dodges. The game controller supplies 6.5 units of ram travel or 5.5 units of dodge travel.
- 46-47: separate dance sequences. Time Warp is a 32-beat hover adaptation without embedded music or a new soundtrack synchronization claim.

All Actions are 24 fps, with identity ROOT transforms. Hull bone translation is local body response and vertical lift, not accumulated travel. The preview moves the reference grid for locomotion and translates the rig object for dodges; neither is keyed into the gameplay Action. Drive vehicle travel from your controller using the manifest speed/direction and event markers. Terrain clips are examples, not a replacement for runtime terrain sensing.

Landing brace keys the armature's `landing_deploy` property. Exporters that do not preserve Blender drivers need the four landing bone transforms baked on export. Weapon and body transforms are already keyed on pose bones. Separate gameplay effects should consume firing markers; gallery flashes are preview-only geometry.

## Rig and source

The armature is `HT-01 | RIG`. ROOT controls travel; Hull controls lift and banking; Turret rotates around Z; Cannon_Elevation and MG_Elevation rotate around X (negative raises); Cannon_Recoil slides rearward along Y; MG_Yaw is independent. All mesh vertices have one full-weight influence. The original editable modeling collections are retained hidden in Blender, distinct from the active weighted edition.

The gallery repository contains scripts, manifests, verification reports, GIFs, and contact sheets. It does not contain the editable `.blend` file or export-ready character binaries. The source remains the user's separately maintained HoverTank1.blend.

## Regeneration

Use Blender MCP with the hover tank open and claimed. Run `tools/blender_hover_library.py` with PROJECT_ROOT set to this repository, then invoke its registered `bake` function in bounded clip-number batches. The recipe script refuses to duplicate existing HT Actions. For a deliberate revision, retain/rename previous Actions before rebuilding.

Run `tools/blender_verify_hover.py`, then `tools/blender_hover_studio.py` and `tools/blender_render_hover.py`. The renderer uses a resumable timer and writes progress/raw PNGs into ignored `build/hover_library/`. RENDER_NUMBERS can restrict the preview queue. Stop or finish an existing queue before starting another.

Run `python tools/package_hover.py`, `python tools/build_gallery.py`, `python tools/build_contact_sheet.py`, and `python tools/validate_gallery.py`. Pillow is required for GIFs/contact sheets. `--available` packages complete clips for visual review without publishing a partial manifest.

Checks cover each integer frame's stationary ROOT, sampled terrain clearance, and loop seams. They do not constitute exhaustive collision or physics validation. Review changed clips visually as well.
