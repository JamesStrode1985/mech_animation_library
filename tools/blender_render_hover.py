"""Bounded, resumable frame queue for the HT hover library. No Blender save."""
import bpy,json,math,time,traceback
from pathlib import Path
from mathutils import Vector,Matrix
ctx=bpy.app.driver_namespace['HT library'];root=Path(PROJECT_ROOT);rig=bpy.data.objects[ctx['rig']];source=bpy.data.scenes[ctx['source_scene']];studio=bpy.data.scenes[ctx['studio']];ground=bpy.data.objects[ctx['ground']];flash=bpy.data.objects[ctx['flash']]
numbers=globals().get('RENDER_NUMBERS',list(range(1,48)));queue=[]
for spec in ctx['specs']:
 if spec['number'] not in numbers:continue
 frames=list(range(1,spec['duration_frames']+1,spec['preview_frame_step']))
 if not spec['loop']:frames.append(spec['duration_frames']+1)
 folder=root/'build/hover_library'/spec['slug'];folder.mkdir(parents=True,exist_ok=True)
 for f in frames:
  path=folder/f'frame_{f:04d}.png'
  if not path.exists():queue.append((spec,f,path))
status={'total':len(queue),'done':0,'running':True,'started':time.time()};ctx['render_status']=status;status_path=root/'build/hover_library/render_progress.json'
def next_frame():
 try:
  if not queue:
   rig.location=(0,0,0);rig.animation_data.action=None;status.update(running=False,finished=time.time());status_path.write_text(json.dumps(status));return None
  spec,f,path=queue.pop(0);t=f-1;n=spec['number'];rig.animation_data.action=bpy.data.actions[spec['action']];rig.location=(0,0,0);travel=Vector((0,0,0))
  if spec.get('controller_preview_travel'):
   q=max(0,min(1,(t-8)/25));q=q*q*(3-2*q);travel=Vector(spec['controller_direction'])*spec['controller_distance_units']*q;rig.location=travel
  source.frame_set(f);bpy.context.view_layer.update();studio.frame_set(f)
  offset=Vector((0,0,0))
  if spec.get('preview_scrolling_ground'):
   elapsed=t/24
   if 6<=n<=8:
    onset=spec['duration_frames']*.3/24;span=spec['duration_frames']*.52/24;q=max(0,min(1,(elapsed-onset)/span));elapsed=min(elapsed,onset)+span*(q-q**3+.5*q**4)
   dist=abs(spec['nominal_speed_units_per_s'])*elapsed;offset=-Vector(spec['travel_direction'])*(dist%3.2)
  ground.location=offset
  for v in ground.data.vertices:v.co.z=ctx['terrain'](spec,v.co.x+offset.x,v.co.y+offset.y,t)
  ground.data.update()
  st=ctx['motion'](spec,t);flash.hide_render=st['shot']<.08
  if not flash.hide_render:
   D=rig.pose.bones['Cannon_Recoil'].matrix@rig.data.bones['Cannon_Recoil'].matrix_local.inverted();M=Matrix.Translation((0,-8.65,5.32))@Vector((0,-1,0)).to_track_quat('Z','Y').to_matrix().to_4x4();flash.matrix_world=rig.matrix_world@D@M;flash.scale=(st['shot'],)*3
  center=Vector((0,-.7,3.7));scale=18.8
  if spec.get('controller_preview_travel'):center+=Vector(spec['controller_direction'])*spec['controller_distance_units']*.5;scale=23.5
  studio.camera.location=center+ctx['camera_direction']*40;studio.camera.data.ortho_scale=scale;studio.render.filepath=str(path);bpy.ops.render.render(write_still=True,scene=studio.name)
  status.update(done=status['done']+1,clip=spec['label'],frame=f,updated=time.time());status_path.write_text(json.dumps(status));return .02
 except Exception:
  rig.location=(0,0,0);status.update(running=False,error=traceback.format_exc());status_path.write_text(json.dumps(status));return None
ctx['render_timer']=next_frame;status_path.write_text(json.dumps(status));bpy.app.timers.register(next_frame,first_interval=.3);print('Queued',len(queue),'hover preview frames')
