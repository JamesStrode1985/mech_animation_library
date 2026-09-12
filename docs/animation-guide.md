# Animation guide

Playback, rig integration, source Action mapping, and verification for the HELLCAT animations.

[Back to the project](../README.md) · [Clip manifest](../data/manifest.json)

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
- Uphill and downhill reference grades are +22 and -22 degrees. The terrain previews move the root vertically along the reference surface; gameplay root keys remain zero.
- Firing strafes orient pelvis and legs 90 degrees into lateral travel. The hull counter-rotates to remain aimed forward. Supply lateral world movement from the controller.
- Hull Actions key only upper-body controls and optional firing effects. Layer these relative to the neutral pose using an upper-body mask.
- Independent elevation controls: `CTRL.cannon.aim`, `CTRL.pod_aim.L`, and `CTRL.pod_aim.R`. Local X negative raises the muzzle. Each joint has a local ±20 degree limit. Pod armor and its gun cluster rotate together; the recoil controls and muzzle FX remain children of their respective aim joint.
- Clips 36/37: hull reaches its ±5 degree aiming contribution at frame 21, weapons reach an additional ±20 degrees at frame 57, hold through frame 81, and return to neutral at frame 113. Clip 38 demonstrates three separate weapon elevations with the hull level.
- Hull contribution is an aiming allocation, not a new global torso limit: existing running/sprinting lean remains intact. Runtime aiming should compute each target direction in the actual posed hull frame, then clamp the local weapon angle. The main bore has an existing approximately 2 degree upward cant; the documented ranges are offsets from its neutral pose.
- A callable helper is provided in Blender Text `HELLCAT - INDEPENDENT WEAPON ELEVATION.py`. It supplies hull/weapon angle allocation with separate cannon/left/right offsets; it is not an automatic game-engine target tracker. Bake aim and recoil bones or implement the same hierarchy in your controller.
- Weapon verification: all 339 frames checked for root/angle behavior; 87 sampled poses checked for moving pod armor and gun barrels versus hull, stowage and upper leg armor, with no intersections in those pairs. Existing embedded cannon mantlet/trunnion mating surfaces are excluded. Details are in the [weapon aiming verification report](../data/verification/weapon_aim_verification.json).
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

Clips 17–19 use roughly three times the original ground-height variation, with an additional smaller ridge pattern. Swing-foot lift is increased by 50%, with stronger hull pitch/roll adjustment and a lower stance. The feet are fitted to the same reference surface shown in the previews.

| Gallery clip | Original Blender Action | Frames | Loop |
|---|---|---:|---|
| 17 Walk Rough Terrain | HC ANIM \| 27 Walk Rough Terrain | 1–193 | Yes |
| 18 Run Rough Terrain | HC ANIM \| 28 Run Rough Terrain | 1–57 | Yes |
| 19 Sprint Rough Terrain | HC ANIM \| 29 Sprint Rough Terrain | 1–41 | Yes |

### Uphill and downhill

Clips 20–25 now use **22° uphill and downhill slopes**, increased from 8°. Foot lift is increased by 20%; the uphill posture commits forward and the downhill posture braces against the descent. Gameplay roots remain stationary, and the preview supplies travel and ground height. Runtime foot IK and ground collision are still needed for arbitrary game terrain.

The nine revised clips retain their existing Action names, gallery numbers, durations and loop timing. See [terrain verification](../data/verification/terrain_revision.json). The reproducible revision, rendering, verification and packaging tools are `blender_terrain_revision.py`, `blender_render_terrain.py`, `blender_verify_terrain.py`, and `package_terrain_previews.py` in `tools/`; Blender tools require the existing live HELLCAT animation contexts and `PROJECT_ROOT`.

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

### Death animations

| Gallery clip | Original Blender Action | Frames | Loop |
|---|---|---:|---|
| 39 Death Forward Collapse | HC ANIM \| 39 Death Forward Collapse | 1–109 | No |
| 40 Death Backward Fall | HC ANIM \| 40 Death Backward Fall | 1–101 | No |
| 41 Death Side Collapse | HC ANIM \| 41 Death Side Collapse | 1–117 | No |

Play once, stop locomotion, and hold the last frame. `CTRL.root` stays fixed; `CTRL.death_fall` supplies the local whole-body collapse beneath it. The additional control is neutral in the existing 38 Actions. Bake its motion with the evaluated deform and mechanical bones when exporting. These are authored death motions, not a runtime ragdoll simulation.

Forward collapse buckles the knees and twists the hull before impact at frame 57; backward fall impacts at frame 47; sideways collapse follows a failed recovery step and impacts at frame 67. Each has Fatal hit, Loss of balance, Ground impact, and Settled markers. The GIF previews repeat for review, while the Actions themselves are non-looping.

All 327 frames were checked for stationary gameplay roots, conservative skinned-vertex ground clearance, joint attachment, hinge alignment, and a stable final hold. Sampled collision checks cover 86 poses for the listed armor and barrel pairs. See the [death verification report](../data/verification/death_animations.json) for the scope and measurements.

The project includes the new Blender creation, render, and verification scripts under `tools/blender_*deaths.py` and `tools/blender_death_animations.py`. They require the existing live HELLCAT rig and animation build context; they do not recreate the source model. Supply `PROJECT_ROOT` when running through Blender MCP. Generated preview frames and packaging metadata stay in ignored `build/`. Package them with `python tools/package_death_previews.py`, then run the standard gallery builders and validator.

### Dodge leaps

| Gallery clip | Original Blender Action | Frames | Travel / peak height (model units) |
|---|---|---:|---:|
| 42 Forward Shoulder Ram | HC ANIM \| 42 Dodge Forward | 1–31 | 2.35 / 0.12 |
| 43 Dodge Backward | HC ANIM \| 43 Dodge Backward | 1–31 | 1.90 / 0.38 |
| 44 Dodge Left | HC ANIM \| 44 Dodge Left | 1–31 | 2.10 / 0.42 |
| 45 Dodge Right | HC ANIM \| 45 Dodge Right | 1–31 | 2.10 / 0.42 |

Each clip lasts 1.25 seconds at 24 fps and does not loop. Dodges 43–45 anticipate at frame 1, take off at frame 7, reach the apex at frame 12, land the lead foot at frame 17 and trailing foot at frame 19, finish braking at frame 23, and return to ready at frame 31. The initial and final poses match. Left and right are from the mech's perspective; the hull keeps facing forward during lateral dodges.

Clip 42 loads and drives from the left leg while the right foot swings forward. The left foot remains planted through frame 10; the right foot catches at frame 15. The hull then turns a further 22 degrees into the right-shoulder impact at frame 18, with the right foot planted throughout the follow-through. The left foot recovers at frame 21, braking ends at frame 25, and the mech returns to ready at frame 31. The attack window is frames 15–20. These are animation cues; the game controls hit detection, damage, and interruption. The original `HC ANIM | 42 Dodge Forward` identifier and `42_dodge_forward.gif` filename remain stable. The other three dodges are unchanged.

`CTRL.root` and `CTRL.death_fall` stay neutral. Apply `controller_samples` from each manifest clip relative to the dodge start and rotate that translation by the character's heading. In model coordinates, forward is -Y, backward +Y, left +X, and right -X. The samples include horizontal travel, vertical trajectory and foot contact states. They are also stored in the source Action's `Controller trajectory` custom property. Landing foot motion counters the final controller deceleration, so using the supplied curve preserves planted contacts. Movement over arbitrary terrain still needs the game controller's collision handling and ground adaptation.

The GIFs simulate controller travel using temporary render-only Actions and a reference grid. They repeat for review; the gameplay Actions do not loop. Author stamina cost, invulnerability, interruption, and recovery-cancel windows in the game controller using the animation markers; these clips provide animation and movement data, not combat logic.

All 124 frames passed stationary-root, ground-clearance, airborne-foot, planted-landing, joint-attachment, neutral-endpoint, and specified armor-pair checks. See [dodge verification](../data/verification/dodge_animations.json) for measurements and scope.

Creation, rendering and verification scripts are in `tools/blender_dodge_animations.py`, `tools/blender_render_dodges.py`, and `tools/blender_verify_dodges.py`. They require the existing live HELLCAT rig and its animation/geometry contexts. Supply `PROJECT_ROOT` through Blender MCP; intermediates go in ignored `build/`. Package with `python tools/package_dodge_previews.py`, then run the gallery builders and validator.

### Dance Party

Clip **46 Dance Party** (`HC ANIM | 46 Dance Party`) is an eight-second, 120 BPM emote at 24 fps, frames 1–193. It loops from a matching neutral pose: stomp groove at frame 1, side shuffle at 49, hull shimmy and alternating pod waves at 97, victory flourish at 145, and return to ready at 181. The root stays stationary. Weapon movement is expressive; muzzle flashes remain off. The GIF has no audio.

All 193 frames passed the checks described in [dance verification](../data/verification/dance_party.json). Build, render, verify and package with `tools/blender_dance_party.py`, `tools/blender_render_dance.py`, `tools/blender_verify_dance.py`, and `tools/package_dance_preview.py`; the Blender scripts require the existing live rig and animation contexts plus `PROJECT_ROOT`.

### Time Warp

**47 Time Warp** (`HC ANIM | 47 Time Warp`) is a separate emote; clip 46 Dance Party is preserved. The original 1975 film is the reference for this mech adaptation: lateral hop left, step right, inward-knee stance, repeated hip pulses, and a pod flourish in place of arm gestures.

The loop is 32 beats across 264 frames (11 seconds at 24 fps), approximately 175 BPM. This working tempo is near the [indexed soundtrack tempo](https://music.toolstud.io/tracks/7a48-a0b8/time-warp); it is **not** an audio-derived beat map. No audio is included, and the choreography is a repeating excerpt rather than a full-song routine. Set a start cue and adjust playback rate against the actual soundtrack when integrating; exact recording synchronization has not been verified.

A separate local video export retimes the dance to movement cues in the supplied 199.34-second MP3, using recording time 54.10–77.81 seconds. It holds between cues, tucks the pods before the knee movement, and times the hip pulses at 0.688-second intervals. The reusable gallery Action stays unchanged. This is a cue-based adaptation, rather than a reproduction of the full film choreography.

Generate it with `tools/blender_render_time_warp_video.py` through Blender MCP, supplying `PROJECT_ROOT` and bounded `VIDEO_FRAMES` batches (1–569). Set `VIDEO_VERIFY=True` for the video pose checks. `tools/export_time_warp_video.py AUDIO_PATH` creates `dist/47_time_warp_synced.mp4` with the trimmed AAC audio and H.264 video. Media dependencies (`imageio-ffmpeg`, `av`, and optional `faster-whisper` for local cue analysis) are installed into ignored `build/media_runtime`. Intermediate frames, speech-analysis files and export verification stay under `build/time_warp_video`; source music and the resulting audio/video are not included in Git.

Beat markers and timing are in the manifest and source Action. All 265 frames, including the duplicate loop endpoint, passed [Time Warp verification](../data/verification/time_warp.json). Use `tools/blender_time_warp.py`, `tools/blender_render_time_warp.py`, `tools/blender_verify_time_warp.py`, and `tools/package_time_warp_preview.py` to rebuild with the existing live rig and animation contexts.

## Validation

Every frame was checked for stationary roots, foot IK reach, sole height and knee hinge alignment. Terrain clips were checked against their reference surface. Loop closure poses match. Sampled mesh checks found no intersections among the tested hip, ankle, hydraulic, hose and armor pairs. These checks are not an exhaustive collision test of every object pair.

The manifest contains detailed verification measurements. GIF sample rate is 24 fps / preview_frame_step. All Actions use 24 fps. Controller travel is present only in temporary render copies, which are removed afterward.
