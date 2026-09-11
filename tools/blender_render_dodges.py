"""Render dodge previews with temporary controller motion and a reference grid.
Supply PROJECT_ROOT, DODGE_LABELS and optionally DODGE_FRAMES through Blender MCP.
The source Actions and .blend save state are preserved.
"""
import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector

out=Path(PROJECT_ROOT)/'build/dodge_previews';out.mkdir(parents=True,exist_ok=True)
rig=bpy.data.objects['HELLCAT | CURRENT MECH RIG'];studio=bpy.data.scenes['HELLCAT | Walking GIF studio'];win=bpy.context.window
dc=bpy.app.driver_namespace['HC dodge context'];ctx=bpy.app.driver_namespace['HC animation build context'];cloud=bpy.app.driver_namespace['HC death context']['cloud']
saved=(win.scene,rig.animation_data.action,rig.animation_data.action_slot,win.scene.frame_current)
pose={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
camera=studio.camera;old_camera=camera.matrix_world.copy();old_scale=camera.data.ortho_scale
settings=(studio.render.filepath,studio.render.resolution_x,studio.render.resolution_y,studio.render.resolution_percentage,studio.render.engine,studio.render.image_settings.file_format,studio.frame_current)
temporary=[];grid=None;mesh=None;material=None;done=[]
try:
    win.scene=studio;studio.render.engine='BLENDER_WORKBENCH';studio.render.image_settings.file_format='PNG'
    studio.render.resolution_x=720;studio.render.resolution_y=640;studio.render.resolution_percentage=100
    vertices=[];faces=[]
    for coordinate in range(-7,8):
        for points in [[(coordinate-.009,-7,.001),(coordinate+.009,-7,.001),(coordinate+.009,7,.001),(coordinate-.009,7,.001)],
                       [(-7,coordinate-.009,.001),(7,coordinate-.009,.001),(7,coordinate+.009,.001),(-7,coordinate+.009,.001)]]:
            start=len(vertices);vertices.extend(points);faces.append(tuple(range(start,start+4)))
    mesh=bpy.data.meshes.new('HC TEMP dodge reference grid');mesh.from_pydata(vertices,[],faces);mesh.update()
    grid=bpy.data.objects.new('HC TEMP dodge reference grid',mesh);studio.collection.objects.link(grid)
    material=bpy.data.materials.new('HC TEMP dodge grid material');material.diffuse_color=(.20,.26,.28,1);mesh.materials.append(material);grid.color=(.20,.26,.28,1)
    for c in dc['config']:
        if c['label'] not in DODGE_LABELS:continue
        ctx['reset']()
        preview=bpy.data.actions['HC ANIM | '+c['label']].copy();preview.name='HC TEMP PREVIEW | '+c['label'];preview.use_fake_user=False;temporary.append(preview)
        rig.animation_data.action=preview
        for f in range(1,32):
            studio.frame_set(f);v=Vector(c['direction'])*dc['distance'](c,f-1);v.z=dc['height'](c,f-1)
            rig.pose.bones['CTRL.root'].location=v
            rig.pose.bones['CTRL.root'].keyframe_insert(data_path='location',frame=f,group='Temporary controller preview')
        direction=Vector((8,-13,6)).normalized();rotation=(-direction).to_track_quat('-Z','Y')
        right=rotation@Vector((1,0,0));up=rotation@Vector((0,1,0));lo=np.array([1e9,1e9]);hi=-lo
        for f in [1,7,12,17,23,31]:
            studio.frame_set(f)
            for bn,points in cloud.items():
                m=np.asarray(rig.matrix_world@rig.pose.bones[bn].matrix)
                projected=points@m[:3,:].T@np.array([right,up]).T
                lo=np.minimum(lo,projected.min(axis=0));hi=np.maximum(hi,projected.max(axis=0))
        center=(lo+hi)/2;target=right*center[0]+up*center[1]
        camera.location=target+direction*20;camera.rotation_euler=rotation.to_euler();camera.data.ortho_scale=max(hi[0]-lo[0],(hi[1]-lo[1])*720/640)*1.13
        folder=out/c['label'].lower().replace(' ','_');folder.mkdir(exist_ok=True)
        frames=globals().get('DODGE_FRAMES') or list(range(1,32))
        for f in frames:
            studio.frame_set(f);studio.render.filepath=str(folder/f'frame_{f:03d}.png');bpy.ops.render.render(write_still=True)
        done.append({'clip':c['label'],'frames':len(frames),'controller_distance':c['distance']})
finally:
    camera.matrix_world=old_camera;camera.data.ortho_scale=old_scale
    studio.render.filepath,studio.render.resolution_x,studio.render.resolution_y,studio.render.resolution_percentage,studio.render.engine,studio.render.image_settings.file_format,frame=settings
    studio.frame_set(frame);win.scene=saved[0];rig.animation_data.action=saved[1]
    if saved[2]:rig.animation_data.action_slot=saved[2]
    for name,m in pose.items():rig.pose.bones[name].matrix_basis=m
    saved[0].frame_set(saved[3]);bpy.context.view_layer.update()
    for action in temporary:bpy.data.actions.remove(action)
    if grid:bpy.data.objects.remove(grid,do_unlink=True)
    if mesh:bpy.data.meshes.remove(mesh)
    if material:bpy.data.materials.remove(material)
print(json.dumps({'rendered':done,'temporary_controller_actions_removed':len(temporary),'blend_saved':False}))
