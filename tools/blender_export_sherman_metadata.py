"""Persist the completed session's verification and packaging metadata, not the .blend."""
import bpy,json
from pathlib import Path
ROOT=Path(PROJECT_ROOT);ctx=bpy.app.driver_namespace['SW locomotion context']
report=dict(model='Sherman Walker',fps=24,root_motion='in-place',
 method='All integer frames: two-bone IK, sole geometry, stationary root, loop seam, 27 rigid armor proxies. Eight poses per gait: evaluated armor surfaces and ammunition feed clearance. Baseline joint contacts are retained. This is a targeted motion clearance review, not exhaustive collision or dynamics certification.',
 clips=ctx['verification'],clearance_modified_objects=ctx['clearance_changes'],blend_saved=False)
(ROOT/'data/verification/sherman_locomotion.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(ROOT/'build/sherman_locomotion/configs.json').write_text(json.dumps(ctx['configs'],indent=2),encoding='utf-8')
print('Wrote verification and packaging metadata; .blend not saved.')
