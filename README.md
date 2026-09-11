# HELLCAT animation library

An offline preview gallery for 38 in-place Blender animations at 24 fps.

## Project workflow

This folder is the standalone [mech_animation_library repository](https://github.com/JamesStrode1985/mech_animation_library). Open `index.html` to view the gallery; no installation, build step, or server is required.

- Commit final GIFs, gallery HTML, contact sheet, manifest, documentation, and relevant verification reports.
- Keep intermediate render frames and release ZIPs out of Git; `.gitignore` excludes them.
- Use `manifest.json` as the clip inventory and group clips by movement, in numeric order. `revision_6.html` is the current bookmarked gallery page.
- Run `python tools/validate_gallery.py` with Python 3.9 or newer, then `git diff --check`, before committing changes. Visually review changed previews as well.

The editable Blender model and Actions are maintained separately and are not included in this repository. Earlier Blender rendering scripts live outside this repository. Rebuild HTML from the manifest with `python tools/build_gallery.py`; rebuild the contact sheet from final GIFs with `python tools/build_contact_sheet.py` (requires Pillow). Neither operation requires intermediate render frames. The existing integration notes below describe those source animations. Statements about unsaved Blender changes in older gallery output describe the state when that preview was produced, not the source file's current save status.

## Playback and export

- Select the mech rig and choose an Action beginning with `HC ANIM |` in the Action Editor, or browse the marked Action assets.
- Loop Actions include an identical closure key at duration + 1. Export the cycle without duplicating the closure frame.
- One-shot Actions include the final recovery pose at duration + 1.
- The root stays stationary, including jumps. Supply horizontal and vertical movement from the game controller. Jump preview height is simulated only during rendering.
- Use Takeoff, Apex, and Land Action markers to synchronize controller jumps. Transition clips include approach and movement recovery.
- Standing jump: takeoff frame 19, apex frame 35, landing frame 51, recovery through frame 85. Preview height is 1.65 model units.
- Run into jump: left-leg takeoff frame 39, apex frame 52, right-leg landing frame 65, continuous running recovery. Preview height is 1.75 model units. Maintain forward speed of 2.462 model units/s through the jump.
- Walk into jump: right-leg takeoff frame 56, apex frame 71, left-leg landing frame 85. The trailing leg swings through into the next step. Preview height is 1.45 model units. Maintain forward speed of 0.431 model units/s.
- Sprint into jump: left-leg takeoff frame 26, apex frame 39, right-leg landing frame 51. Preview height is 2.0 model units. Maintain forward speed of 4.88 model units/s.
- Backward clips face forward and travel backward. Negative nominal speed values indicate reverse controller movement.
- Stop clips include Begin braking, Controller stopped, and Feet settled markers. The manifest and Action custom property contain per-frame controller distance samples; use them to synchronize deceleration with planted braking steps.
- Rough-terrain and hill clips use authored reference ground. Apply runtime foot IK, pelvis adjustment and normal alignment to adapt them to actual game terrain. These clips do not automatically detect arbitrary terrain.
- Uphill and downhill reference grades are +8 and -8 degrees. The terrain previews move the root vertically along the reference surface; gameplay root keys remain zero.
- Firing strafes orient pelvis and legs 90 degrees into lateral travel. The hull counter-rotates to remain aimed forward. Supply lateral world movement from the controller.
- Hull Actions key only upper-body controls and optional firing effects. Layer these relative to the neutral pose using an upper-body mask.
- Independent elevation controls: `CTRL.cannon.aim`, `CTRL.pod_aim.L`, and `CTRL.pod_aim.R`. Local X negative raises the muzzle. Each joint has a local ±20 degree limit. Pod armor and its gun cluster rotate together; the recoil controls and muzzle FX remain children of their respective aim joint.
- Clips 36/37: hull reaches its ±5 degree aiming contribution at frame 21, weapons reach an additional ±20 degrees at frame 57, hold through frame 81, and return to neutral at frame 113. Clip 38 demonstrates three separate weapon elevations with the hull level.
- Hull contribution is an aiming allocation, not a new global torso limit: existing running/sprinting lean remains intact. Runtime aiming should compute each target direction in the actual posed hull frame, then clamp the local weapon angle. The main bore has an existing approximately 2 degree upward cant; the documented ranges are offsets from its neutral pose.
- A callable helper is provided in Blender Text `HELLCAT - INDEPENDENT WEAPON ELEVATION.py`. It supplies hull/weapon angle allocation with separate cannon/left/right offsets; it is not an automatic game-engine target tracker. Bake aim and recoil bones or implement the same hierarchy in your controller.
- Weapon verification: all 339 frames checked for root/angle behavior; 87 sampled poses checked for moving pod armor and gun barrels versus hull, stowage and upper leg armor, with no intersections in those pairs. Existing embedded cannon mantlet/trunnion mating surfaces are excluded. Details are in weapon_aim_verification.json.
- Bake evaluated deform bones and mechanical helper motion when exporting to a game engine; the live rig uses IK, constraints, and driven piston mechanisms.
- Optional muzzle flashes are in `HC | 42 optional weapon animation FX`. Exclude that collection if the engine supplies weapon effects.
- Nominal speed values use model units per second; adapt to your engine scale. Left/right refer to the mech.

## Clip list

Gallery numbers follow the grouped viewing order. The original Blender Action names are unchanged; the source column maps each preview to the editable animation. Historical verification reports use those original source labels.

### Forward movement

| Gallery clip | Original Blender Action | Frames | Loop |
|---|---|---:|---|
| 01 Walk | HC ANIM \| 01 Walk | 1–49 | Yes |
| 02 Run | HC ANIM \| 02 Run | 1–29 | Yes |
| 03 Sprint | HC ANIM \| 03 Sprint | 1–21 | Yes |

### Backward movement

| Gallery clip | Original Blender Action | Frames | Loop |
|---|---|---:|---|
| 04 Walk Backward | HC ANIM \| 22 Walk Backward | 1–49 | Yes |
| 05 Run Backward | HC ANIM \| 23 Run Backward | 1–29 | Yes |

### Coming to a stop

| Gallery clip | Original Blender Action | Frames | Loop |
|---|---|---:|---|
| 06 Walk To Stop | HC ANIM \| 24 Walk To Stop | 1–97 | No |
| 07 Run To Stop | HC ANIM \| 25 Run To Stop | 1–71 | No |
| 08 Sprint To Stop | HC ANIM \| 26 Sprint To Stop | 1–61 | No |

### Jumps and moving jumps

| Gallery clip | Original Blender Action | Frames | Loop |
|---|---|---:|---|
| 09 Jump | HC ANIM \| 04 Jump | 1–85 | No |
| 10 Walk Into Jump | HC ANIM \| 08 Walk Into Jump | 1–133 | No |
| 11 Run Into Jump | HC ANIM \| 07 Run Into Jump | 1–107 | No |
| 12 Sprint Into Jump | HC ANIM \| 21 Sprint Into Jump | 1–81 | No |

### Side steps and strafing

| Gallery clip | Original Blender Action | Frames | Loop |
|---|---|---:|---|
| 13 Side Step Left | HC ANIM \| 05 Side Step Left | 1–49 | Yes |
| 14 Side Step Right | HC ANIM \| 06 Side Step Right | 1–49 | Yes |
| 15 Strafe Fire Left | HC ANIM \| 09 Strafe Fire Left | 1–41 | Yes |
| 16 Strafe Fire Right | HC ANIM \| 10 Strafe Fire Right | 1–41 | Yes |

### Rough terrain

| Gallery clip | Original Blender Action | Frames | Loop |
|---|---|---:|---|
| 17 Walk Rough Terrain | HC ANIM \| 27 Walk Rough Terrain | 1–193 | Yes |
| 18 Run Rough Terrain | HC ANIM \| 28 Run Rough Terrain | 1–57 | Yes |
| 19 Sprint Rough Terrain | HC ANIM \| 29 Sprint Rough Terrain | 1–41 | Yes |

### Uphill and downhill

| Gallery clip | Original Blender Action | Frames | Loop |
|---|---|---:|---|
| 20 Walk Uphill | HC ANIM \| 30 Walk Uphill | 1–97 | Yes |
| 21 Walk Downhill | HC ANIM \| 31 Walk Downhill | 1–97 | Yes |
| 22 Run Uphill | HC ANIM \| 32 Run Uphill | 1–57 | Yes |
| 23 Run Downhill | HC ANIM \| 33 Run Downhill | 1–57 | Yes |
| 24 Sprint Uphill | HC ANIM \| 34 Sprint Uphill | 1–41 | Yes |
| 25 Sprint Downhill | HC ANIM \| 35 Sprint Downhill | 1–41 | Yes |

### Hull movement

| Gallery clip | Original Blender Action | Frames | Loop |
|---|---|---:|---|
| 26 Hull Idle | HC ANIM \| 11 Hull Idle | 1–97 | Yes |
| 27 Hull Scan | HC ANIM \| 12 Hull Scan | 1–97 | Yes |
| 28 Hull Turn Left | HC ANIM \| 13 Hull Turn Left | 1–61 | No |
| 29 Hull Turn Right | HC ANIM \| 14 Hull Turn Right | 1–61 | No |
| 30 Hull Pitch Up | HC ANIM \| 15 Hull Pitch Up | 1–61 | No |
| 31 Hull Pitch Down | HC ANIM \| 16 Hull Pitch Down | 1–61 | No |
| 32 Hull Lean Left | HC ANIM \| 17 Hull Lean Left | 1–61 | No |
| 33 Hull Lean Right | HC ANIM \| 18 Hull Lean Right | 1–61 | No |
| 34 Hull Brace | HC ANIM \| 19 Hull Brace | 1–61 | No |
| 35 Hull Recoil | HC ANIM \| 20 Hull Recoil | 1–41 | No |

### Weapon aiming

| Gallery clip | Original Blender Action | Frames | Loop |
|---|---|---:|---|
| 36 Aim Track Up | HC ANIM \| 36 Aim Track Up | 1–113 | No |
| 37 Aim Track Down | HC ANIM \| 37 Aim Track Down | 1–113 | No |
| 38 Independent Weapon Aim | HC ANIM \| 38 Independent Weapon Aim | 1–113 | No |

## Validation

Every frame was checked for stationary roots, foot IK reach, sole height and knee hinge alignment. Terrain clips were checked against their reference surface. Loop closure poses match. Sampled mesh checks found no intersections among the tested hip, ankle, hydraulic, hose and armor pairs. These checks are not an exhaustive collision test of every object pair.

The manifest contains detailed verification measurements. GIF sample rate is 24 fps / preview_frame_step. All Actions use 24 fps. Controller travel is present only in temporary render copies, which are removed afterward.
