"""Render the dance-party emote through Blender MCP; restore scene settings.
Supply PROJECT_ROOT and optionally DANCE_FRAMES.
"""
import bpy,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector

out=Path(PROJECT_ROOT)/'build/dance_previews';out.mkdir(parents=True,exist_ok=True)
rig=bpy.data.objects['HELLCAT | CURRENT MECH RIG'];studio=bpy.data.scenes['HELLCAT | Walking GIF studio'];win=bpy.context.window
dc=bpy.app.driver_namespace['HC death context'];ctx=bpy.app.driver_namespace['HC animation build context']
saved=(win.scene,rig.animation_data.action,rig.animation_data.action_slot,win.scene.frame_current)
saved_pose={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
camera=studio.camera;cam_matrix=camera.matrix_world.copy();cam_scale=camera.data.ortho_scale
settings=(studio.render.filepath,studio.render.resolution_x,studio.render.resolution_y,studio.render.resolution_percentage,studio.render.engine,studio.render.image_settings.file_format,studio.frame_current)
done=[]
try:
    win.scene=studio;studio.render.engine='BLENDER_WORKBENCH';studio.render.image_settings.file_format='PNG'
    studio.render.resolution_x=720;studio.render.resolution_y=640;studio.render.resolution_percentage=100
    for c in [dict(label='46 Dance Party',duration=192)]:
        ctx['reset']();rig.animation_data.action=bpy.data.actions['HC ANIM | '+c['label']]
        direction=Vector((8,-13,6)).normalized();rotation=(-direction).to_track_quat('-Z','Y')
        right=rotation@Vector((1,0,0));up=rotation@Vector((0,1,0))
        lo=np.array([1e9,1e9]);hi=-lo
        for f in list(range(1,194,6)):
            studio.frame_set(f)
            for bn,points in dc['cloud'].items():
                m=np.asarray(rig.matrix_world@rig.pose.bones[bn].matrix)
                projected=points@m[:3,:].T@np.array([right,up]).T
                lo=np.minimum(lo,projected.min(axis=0));hi=np.maximum(hi,projected.max(axis=0))
        center=(lo+hi)/2;target=right*center[0]+up*center[1]
        camera.location=target+direction*20;camera.rotation_euler=rotation.to_euler()
        camera.data.ortho_scale=max((hi[0]-lo[0])*1.13,(hi[1]-lo[1])*720/640*1.13)
        folder=out/c['label'].lower().replace(' ','_');folder.mkdir(exist_ok=True)
        frames=globals().get('DANCE_FRAMES') or list(range(1,c['duration']+1,2))
        for f in frames:
            studio.frame_set(f);studio.render.filepath=str(folder/f'frame_{f:03d}.png');bpy.ops.render.render(write_still=True)
        done.append({'label':c['label'],'frames':len(frames),'ortho_scale':camera.data.ortho_scale})
finally:
    camera.matrix_world=cam_matrix;camera.data.ortho_scale=cam_scale
    studio.render.filepath,studio.render.resolution_x,studio.render.resolution_y,studio.render.resolution_percentage,studio.render.engine,studio.render.image_settings.file_format,frame=settings
    studio.frame_set(frame);win.scene=saved[0];rig.animation_data.action=saved[1]
    if saved[2]:rig.animation_data.action_slot=saved[2]
    for n,m in saved_pose.items():rig.pose.bones[n].matrix_basis=m
    saved[0].frame_set(saved[3]);bpy.context.view_layer.update()
print(json.dumps({'rendered':done,'blend_saved':False}))
