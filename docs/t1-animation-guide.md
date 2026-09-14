# T1 Artillery Walker animation library

Open [the T1 gallery](../t1-artillery-walker.html). Its 47 previews match the Hellcat inventory and numbering, with motion adapted to four heavy digitigrade legs, a long artillery hull, and a separate roof turret.

## Motion and controls

- Walk uses staggered four-beat contacts; run uses a diagonal trot; sprint uses a staggered gallop. Backward movement and stops use the corresponding gait.
- Moving jumps preserve a gait lead-in, preload, drive, airborne arc, landing compression, and recovery. The standalone jump begins from a planted stance.
- Strafing separates travel direction from hull aim. The main barrel and roof guns use independent elevation and recoil. Roof yaw is separate from the hull.
- Rough terrain uses uneven foot heights and body height compensation. Uphill and downhill clips use a 22-degree reference slope. The longer rear lower legs need a minimum compression distance as well as a maximum reach limit.
- Revision 2 deaths keep the feet grounded while the legs fold: front-first forward slump, rear-first backward slump, and a staggered failure. There is no whole-body rollover. Original Action names and asset slugs remain stable.
- Artillery recoil uses a 0.891-unit barrel kick with a 0.90-unit travel limit, followed by a delayed hull shove and leg compression. Fire is frame 10, maximum barrel recoil frame 12, hull impact frame 18, and leg compression frame 21. Recovery is slower than the kick.
- Dodge leaps use a four-legged drive and landing. Clip 42 is a **forward hull ram**, replacing the biped shoulder ram to suit this chassis.
- Dance Party uses alternating steps and hull yaw. Time Warp has its own directional hops, broad squat, and hull thrusts. Both are adapted to four legs. Time Warp contains no soundtrack and is not an exact audio synchronization deliverable.

The live rig is `T1 | ANIMATION RIG`. Actions are named `T1 ANIM | 01 Walk` through `T1 ANIM | 47 Time Warp`; exact identifiers and markers are in the [manifest](../data/mechs/t1-artillery-walker.json). Original Hellcat action names are retained as source mapping, not shared animation data.

## Game integration

Actions use 24 fps and an identity `CTRL.root`. Apply world movement in the game controller. Most GIFs sample every third frame (8 fps); revision 2 deaths and dances sample every second frame (12 fps), while artillery recoil uses every frame (24 fps). One-shots hold the final pose. Controller displacement is shown only in dodge previews: 5.5 scene units for the hull ram, 4.5 for the other three directions. That displacement is not baked into the gameplay root.

Use manifest gait speed and touchdown/takeoff markers as starting points for controller blending. Apply runtime foot IK and body height adjustment to the actual terrain; the fixed reference surfaces in these clips are illustrative. Match clip scale to the engine's world units before using the speed and distance metadata.

## Verification and rebuilding

The [verification report](../data/verification/t1_library.json) records checks at every integer frame for leg endpoint IK, sampled sole clearance, stationary gameplay root, and loop endpoint continuity. Model bounds are sampled for framing. These checks do not establish exhaustive surface collision clearance or a physically simulated mass/recoil model.

The repository contains final GIF previews, metadata, and generation scripts. It does **not** contain the editable model or baked Blender Actions. The source scene is maintained separately in Blender. These scripts do not save or overwrite a `.blend` file.

With the intended T1 scene and rig open, run the following files through Blender MCP, supplying `PROJECT_ROOT` as this repository's absolute path:

1. `tools/blender_t1_library.py` creates the recipes. Assign `bake = bpy.app.driver_namespace['T1 library']['bake']`, then call `bake(list(range(1,48)))` to bake the Actions.
2. `tools/blender_verify_t1.py` writes the checks. `VERIFY_NUMBERS` can select a subset.
3. `tools/blender_t1_studio.py` creates a separate preview scene. Run it from the source scene once.
4. `tools/blender_render_t1.py` queues resumable PNG renders in ignored `build/t1_library/`. Watch `render_progress.json` until `running` is false; an `error` field means rendering failed. Remove only affected raw frame folders before intentionally rerendering changed clips.
5. Run `python tools/package_t1.py` with Pillow after all renders complete, then the normal gallery builders and validators described in the [README](../README.md).

Keep the live Blender instance claimed while editing or rendering. Release it when finished. Saving the source model is a separate explicit action.
