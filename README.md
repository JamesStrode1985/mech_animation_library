# HELLCAT animation library

38 in-place Blender Action assets at 24 fps. Changes are unsaved in the open Blender project.

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

| Action | Frames | Loop | Nominal units/s |
|---|---:|---|---:|
| HC ANIM | 01 Walk | 1–49 | Yes | 0.431 |
| HC ANIM | 02 Run | 1–29 | Yes | 2.462 |
| HC ANIM | 03 Sprint | 1–21 | Yes | 4.880 |
| HC ANIM | 04 Jump | 1–85 | No | 0.000 |
| HC ANIM | 05 Side Step Left | 1–49 | Yes | 0.278 |
| HC ANIM | 06 Side Step Right | 1–49 | Yes | 0.278 |
| HC ANIM | 07 Run Into Jump | 1–107 | No | 2.462 |
| HC ANIM | 08 Walk Into Jump | 1–133 | No | 0.431 |
| HC ANIM | 09 Strafe Fire Left | 1–41 | Yes | 0.737 |
| HC ANIM | 10 Strafe Fire Right | 1–41 | Yes | 0.737 |
| HC ANIM | 11 Hull Idle | 1–97 | Yes | 0.000 |
| HC ANIM | 12 Hull Scan | 1–97 | Yes | 0.000 |
| HC ANIM | 13 Hull Turn Left | 1–61 | No | 0.000 |
| HC ANIM | 14 Hull Turn Right | 1–61 | No | 0.000 |
| HC ANIM | 15 Hull Pitch Up | 1–61 | No | 0.000 |
| HC ANIM | 16 Hull Pitch Down | 1–61 | No | 0.000 |
| HC ANIM | 17 Hull Lean Left | 1–61 | No | 0.000 |
| HC ANIM | 18 Hull Lean Right | 1–61 | No | 0.000 |
| HC ANIM | 19 Hull Brace | 1–61 | No | 0.000 |
| HC ANIM | 20 Hull Recoil | 1–41 | No | 0.000 |
| HC ANIM | 21 Sprint Into Jump | 1–81 | No | 4.880 |
| HC ANIM | 22 Walk Backward | 1–49 | Yes | -0.310 |
| HC ANIM | 23 Run Backward | 1–29 | Yes | -1.526 |
| HC ANIM | 24 Walk To Stop | 1–97 | No | 0.431 |
| HC ANIM | 25 Run To Stop | 1–71 | No | 2.462 |
| HC ANIM | 26 Sprint To Stop | 1–61 | No | 4.880 |
| HC ANIM | 27 Walk Rough Terrain | 1–193 | Yes | 0.431 |
| HC ANIM | 28 Run Rough Terrain | 1–57 | Yes | 2.462 |
| HC ANIM | 29 Sprint Rough Terrain | 1–41 | Yes | 4.880 |
| HC ANIM | 30 Walk Uphill | 1–97 | Yes | 0.431 |
| HC ANIM | 31 Walk Downhill | 1–97 | Yes | 0.431 |
| HC ANIM | 32 Run Uphill | 1–57 | Yes | 2.462 |
| HC ANIM | 33 Run Downhill | 1–57 | Yes | 2.462 |
| HC ANIM | 34 Sprint Uphill | 1–41 | Yes | 4.880 |
| HC ANIM | 35 Sprint Downhill | 1–41 | Yes | 4.880 |
| HC ANIM | 36 Aim Track Up | 1–113 | No | 0.000 |
| HC ANIM | 37 Aim Track Down | 1–113 | No | 0.000 |
| HC ANIM | 38 Independent Weapon Aim | 1–113 | No | 0.000 |

## Validation

Every frame was checked for stationary roots, foot IK reach, sole height and knee hinge alignment. Terrain clips were checked against their reference surface. Loop closure poses match. Sampled mesh checks found no intersections among the tested hip, ankle, hydraulic, hose and armor pairs. These checks are not an exhaustive collision test of every object pair.

The manifest contains detailed verification measurements. GIF sample rate is 24 fps / preview_frame_step. All Actions use 24 fps. Controller travel is present only in temporary render copies, which are removed afterward.
