"""Render a soundtrack-cued video using a temporary retimed Action.
Supply PROJECT_ROOT and VIDEO_FRAMES (a bounded batch) through Blender MCP.
Preserves both dance Actions and restores the scene; does not save .blend.
Cue map is based on the user's supplied 199.34-second recording.
"""
import bpy,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector

START=54.10;END=77.80;FPS=24;COUNT=round((END-START)*FPS)
# Recording time -> original dance beat. Repeated beats hold between verbal cues.
CUES=[(54.10,0),(54.85,2),(56.05,4),(58.38,5),(59.26,7),(60.30,9),
      (63.65,10),(64.25,12),(65.15,14),(66.96,14),(73.84,24),
      (74.52,26),(75.20,28),(76.55,30),(77.80,32)]
def phase(time):
    for (a,x),(b,y) in zip(CUES,CUES[1:]):
        if time<=b:return x+(y-x)*max(0,min(1,(time-a)/(b-a)))
    return 32
def smooth(x):
    x=max(0,min(1,x));return x*x*(3-2*x)

rig=bpy.data.objects['HELLCAT | CURRENT MECH RIG'];studio=bpy.data.scenes['HELLCAT | Walking GIF studio'];win=bpy.context.window
ctx=bpy.app.driver_namespace['HC animation build context'];cloud=bpy.app.driver_namespace['HC death context']['cloud']
saved=(win.scene,rig.animation_data.action,rig.animation_data.action_slot,win.scene.frame_current)
pose={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
camera=studio.camera;camera_matrix=camera.matrix_world.copy();camera_scale=camera.data.ortho_scale
settings=(studio.render.filepath,studio.render.resolution_x,studio.render.resolution_y,studio.render.resolution_percentage,studio.render.engine,studio.render.image_settings.file_format,studio.frame_current)
source=bpy.data.actions['HC ANIM | 47 Time Warp'];preview=None
folder=Path(PROJECT_ROOT)/'build/time_warp_video/frames';folder.mkdir(parents=True,exist_ok=True)
def curves(action):return [fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
try:
    win.scene=studio;ctx['reset']()
    preview=source.copy();preview.name='HC TEMP AUDIO SYNC | Time Warp';preview.use_fake_user=False;preview.asset_clear()
    source_curves={(fc.data_path,fc.array_index):fc for fc in curves(source)}
    for fc in curves(preview):
        original=source_curves[fc.data_path,fc.array_index]
        keys=[]
        for f in range(1,COUNT+1):
            time=START+(f-1)/FPS;source_frame=1+phase(time)*264/32
            value=original.evaluate(source_frame)
            # Pod tuck substitutes for the hand-on-hip cue before the knee motion.
            if fc.data_path in ['pose.bones["CTRL.pod_aim.L"].rotation_euler','pose.bones["CTRL.pod_aim.R"].rotation_euler'] and fc.array_index==0 and 60.9<=time<65.15:
                blend=smooth((time-60.9)/.8);value=value*(1-blend)+math.radians(-14)*blend
            keys.extend((f,value))
        for modifier in list(fc.modifiers):fc.modifiers.remove(modifier)
        fc.keyframe_points.clear();fc.keyframe_points.add(COUNT);fc.keyframe_points.foreach_set('co',keys)
        for key in fc.keyframe_points:key.interpolation='LINEAR'
        fc.update()
    rig.animation_data.action=preview
    studio.render.engine='BLENDER_WORKBENCH';studio.render.image_settings.file_format='PNG'
    studio.render.resolution_x=720;studio.render.resolution_y=640;studio.render.resolution_percentage=100
    direction=Vector((8,-13,6)).normalized();rotation=(-direction).to_track_quat('-Z','Y')
    right=rotation@Vector((1,0,0));up=rotation@Vector((0,1,0));lo=np.array([1e9,1e9]);hi=-lo
    for f in range(1,COUNT+1,12):
        studio.frame_set(f)
        for bn,points in cloud.items():
            m=np.asarray(rig.matrix_world@rig.pose.bones[bn].matrix)
            projected=points@m[:3,:].T@np.array([right,up]).T
            lo=np.minimum(lo,projected.min(axis=0));hi=np.maximum(hi,projected.max(axis=0))
    center=(lo+hi)/2;target=right*center[0]+up*center[1]
    camera.location=target+direction*20;camera.rotation_euler=rotation.to_euler()
    camera.data.ortho_scale=max(hi[0]-lo[0],(hi[1]-lo[1])*720/640)*1.13
    if globals().get('VIDEO_VERIFY',False):
        lowest=1e9;root_error=0;collisions={};tree=bpy.app.driver_namespace['HC weapon mesh_tree']
        floor=bpy.app.driver_namespace['HC death context']['floor_low']
        for f in range(1,COUNT+1):
            studio.frame_set(f);lowest=min(lowest,floor()[0]);root_error=max(root_error,rig.pose.bones['CTRL.root'].location.length)
            pod=tree('HC Pods | twin armored sponsons','CTRL.pod_aim')
            for hull in ['HC Hull | closed faceted lower tub','HC Hull | layered casemate armor']:
                count=len(pod.overlap(tree(hull)))
                if count:collisions.setdefault(hull,[]).append([f,count])
        report={'frames_checked':COUNT,'minimum_body_floor_z':lowest,'root_error':root_error,'pod_hull_intersections':collisions,'scope':'All video poses checked for conservative body floor clearance, stationary root and the retimed pod motion against hull armor. Original source dance has its separate leg-armor verification.'}
        (folder.parent/'pose_verification.json').write_text(json.dumps(report,indent=2)+'\n')
        assert lowest>=0 and root_error<1e-6 and not collisions,report
    for f in VIDEO_FRAMES:
        assert 1<=f<=COUNT
        studio.frame_set(f);studio.render.filepath=str(folder/f'frame_{f:04d}.png');bpy.ops.render.render(write_still=True)
    (folder.parent/'sync.json').write_text(json.dumps({'audio_start_seconds':START,'audio_end_seconds':START+COUNT/FPS,'fps':FPS,'frame_count':COUNT,'cues_recording_seconds_to_dance_beats':CUES,'source_action':source.name,'source_action_modified':False,'notes':'Cue-based retime from supplied recording. Short musical holds and 0.688-second hip-pulse spacing are intentional. No source audio included in the project.'},indent=2)+'\n')
finally:
    camera.matrix_world=camera_matrix;camera.data.ortho_scale=camera_scale
    studio.render.filepath,studio.render.resolution_x,studio.render.resolution_y,studio.render.resolution_percentage,studio.render.engine,studio.render.image_settings.file_format,f=settings
    studio.frame_set(f);win.scene=saved[0];rig.animation_data.action=saved[1]
    if saved[2]:rig.animation_data.action_slot=saved[2]
    for name,m in pose.items():rig.pose.bones[name].matrix_basis=m
    saved[0].frame_set(saved[3]);bpy.context.view_layer.update()
    if preview:bpy.data.actions.remove(preview)
print(json.dumps({'rendered':len(VIDEO_FRAMES),'total_frames':COUNT,'seconds':COUNT/FPS,'saved':False}))
