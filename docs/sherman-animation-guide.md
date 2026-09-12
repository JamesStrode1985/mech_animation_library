# Sherman Walker animation guide

Open [the Sherman gallery](../sherman-walker.html). It contains 47 independently
rendered Sherman animations matching the Hellcat's numbered movement categories.
The [manifest](../data/mechs/sherman-walker.json) records exact Action names,
durations, markers, preview timing, and corresponding Hellcat source Actions.

## Inventory

| Numbers | Movement |
| --- | --- |
| 01–03 | Walk, run, sprint |
| 04–05 | Walk and run backward |
| 06–08 | Walk, run, sprint to a stop |
| 09–12 | Standing jump; walk, run, sprint into a jump |
| 13–16 | Side steps and strafing fire, left and right |
| 17–19 | Walk, run, sprint over rough terrain |
| 20–25 | Walk, run, sprint uphill and downhill |
| 26–35 | Idle, scan, hull turns, pitch, roll, brace, recoil |
| 36–38 | Upward, downward, and independent weapon aiming |
| 39–41 | Forward, backward, and sideways deaths |
| 42–45 | Forward shoulder ram; backward, left, and right dodges |
| 46–47 | Dance Party and Time Warp |

## Sherman adaptations

The basic walk takes 48 frames, the run 32, and the sprint 24 at 24 fps. Walking
emphasizes sustained support and weight transfer. Running and sprinting shorten
support, add flight, and deepen recovery and landing compression. Timing and
posture suggest a heavy machine; this is not a physical mass simulation or a
certification of complete anatomical range.

The approved left arm stays straight from shoulder to hand in every clip. Its
elbow and wrist offsets stay zero because their different bone rolls cannot be
treated as a common bend axis. Swing and gun elevation come from the shoulder.
The articulated ammunition feed follows its existing guides. The asymmetric
cannon arm has restrained swing and tucks during the ram and falls. The cannon,
left gun, and roof gun replace Hellcat's weapon-pod roles.

Strafing rotates the hips and legs toward travel while the hull counter-rotates
to aim forward. Moving jumps retain an approach gait, staggered takeoff, landing
compression, and a return to gait. The ram loads one leg, catches with the other,
then follows through with the hull. Deaths use separate forward, backward, and
sideways body falls, with the cannon tucked and body clearance adjusted to ground.

Rough-ground previews use a moving multi-frequency surface matched to stance-foot
speed. Uphill and downhill references use 22-degree slopes. Feet adapt pitch,
roll, and height, with a final sole-clearance correction after the leg solver.
Runtime foot placement must conform to actual game terrain. Studio terrain is
separate from the model scene.

The revised dodges (42–45) last 36 frames / 1.5 seconds, with stronger loading,
larger leg recovery, airborne whole-body lean, and staggered impact compression.
The evasive leap uses 1.8 rig units of vertical lift before pose corrections;
the forward attack keeps a lower, driving trajectory and follows through after
the right foot plants. Whole-body lean avoids crushing the hull into hip armor.

Their preview controller travels 10.5 world scene units for the ram, 8 backward,
and 9 to either side. Each GIF shows the complete translation over a fixed grid
of two-unit squares. The gameplay Action still has an identity root. Apply the
manifest's `controller_travel_keys` along `controller_direction` in the game;
`tools/sherman_controller.py` provides the monotone cubic interpolation used by
the preview. The listed average speed includes the windup and recovery. These
distances are scene units, not a declaration that the model is scaled in meters.
The [dodge travel report](../data/verification/sherman_dodges_revision3.json) records
the monotone travel checks and ammunition-feed translation check.

Time Warp follows the same approximate 32-beat, 175 BPM choreography convention
as the Hellcat gallery clip. It includes no audio or exact soundtrack alignment.

## Controller and playback

All gameplay Actions keep `CTRL.root` at identity. The controller supplies travel;
body motion, jumps, and falls are inside the pose. Loop playback uses frames 1
through `duration_frames`, with a duplicate closing key at `duration_frames + 1`.
One-shots include their final keyed pose. Use event markers for takeoff, landing,
braking, and attacks. Recorded speeds are scene units per second.

Hull and aim previews include a full-body ready pose. Use an upper-body bone mask
and an appropriate reference pose when blending them over locomotion; these are
not engine-specific additive exports. The original multi-axis hips and ankles
remain available within the rig's existing limits.

Clips 01–03 and revised dodges 42–45 have 24 fps GIF previews. Other clips sample the 24 fps Actions at 12 fps,
using alternating 80/90 ms GIF delays. One-shots hold their final pose for 700 ms
before gallery replay. This hold is not an extra Action key or gameplay delay.

## Validation and model clearance

The earlier locomotion pass shortened and tapered the rear thigh/calf guards,
remapping their panels and fasteners together. Original mesh datablocks remain
as backups. This full-library pass retains those changes and the straight arm.

The [locomotion report](../data/verification/sherman_locomotion.json) covers 01–03.
The [full-library report](../data/verification/sherman_full_library.json) covers
04–47: all integer frames for IK reach, sole clearance, root identity, and arm
centerline; loop endpoints; native driver health; sampled intersections among
27 rigid armor regions; and selected evaluated rear-armor/ammo-feed poses.
Existing baseline joint contacts are excluded from new-contact findings.

Checks require IK error below 0.001 rig units, positive sole clearance, preserved
arm alignment, and no new contacts in tested regions. Rendered poses and GIF
phase sheets receive visual review. This targeted check does not certify every
bolt, hose, arbitrary blend, or runtime pose as collision-free.

## Authoring and rebuild

Editable Actions live in the open Blender model, not this repository. This
operation does not save or overwrite the `.blend`; save in Blender to retain the
model and Actions. Project-local scripts preserve the recipe for the matching rig.
Use Blender MCP and supply `PROJECT_ROOT` as this repository's absolute path.

1. The base `blender_sherman_locomotion.py`, `blender_sherman_clearance.py`, and
   `blender_sherman_studio.py` establish the approved rig context and preview scene.
   Do not apply clearance changes again to an already modified model in a fresh
   session without restoring original mesh data.
2. `blender_sherman_full_library.py` authors 04–47. Select clips with
   `BUILD_NUMBERS`; `BUILD_FRAMES` permits bounded frame batches. Start at frame 1
   and finish through the closing frame. Prior Actions are retained.
3. Run `blender_verify_sherman_full.py` with `VERIFY_NUMBERS`, and
   `blender_verify_sherman_full_surfaces.py` with `VERIFY_NUMBER` for evaluated checks.
4. `blender_render_sherman_full.py` accepts `RENDER_NUMBER` and bounded
   `RENDER_FRAMES`; honor `preview_frame_step` and include the final key for one-shots.
   Temporary PNGs go under ignored `build/sherman_full/`.
5. Run `python tools/package_sherman_full.py` with Pillow (append selected numbers,
   such as `42 43 44 45`, to preserve other GIFs). It validates reports
   and render completeness before publishing all 47 manifest entries. The older
   `package_sherman_previews.py` packages only 01–03 and replaces the manifest;
   run the full packager afterward when rebuilding the complete library.
6. Rebuild HTML and contact sheets, then run gallery validation, multi-mech tests,
   and `git diff --check`.
