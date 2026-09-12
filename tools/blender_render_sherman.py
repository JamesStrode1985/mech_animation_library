"""Render a bounded batch from an authored Sherman Action; restore active scene."""
import bpy,json
from pathlib import Path
ROOT=Path(PROJECT_ROOT);ctx=bpy.app.driver_namespace['SW locomotion context'];c=ctx['configs'][RENDER_CLIP]
studio=bpy.data.scenes[ctx['studio']];r=bpy.data.objects['SHERMAN WALKER | ANIMATION RIG']
saved=bpy.context.window.scene
out=ROOT/'build/sherman_locomotion'/c['slug'];out.mkdir(parents=True,exist_ok=True)
try:
    bpy.context.window.scene=studio;r.animation_data.action=bpy.data.actions[c['action']]
    for frame in RENDER_FRAMES:
        studio.frame_set(frame);studio.render.filepath=str(out/f'frame_{frame:03d}.png')
        bpy.ops.render.render(write_still=True)
finally:
    bpy.context.window.scene=saved
print(json.dumps({'clip':c['label'],'frames':list(RENDER_FRAMES),'folder':str(out)}))
