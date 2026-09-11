"""Render terrain previews. Supply PROJECT_ROOT and HC_EXT_RENDER_LABELS through Blender MCP."""
import bpy,math,json
from mathutils import Vector
from pathlib import Path
rig=bpy.data.objects['HELLCAT | CURRENT MECH RIG'];studio=bpy.data.scenes['HELLCAT | Walking GIF studio'];win=bpy.context.window
ctx=bpy.app.driver_namespace['HC animation build context'];ext=bpy.app.driver_namespace['HC terrain revision context']
orig_scene=win.scene;orig_action=rig.animation_data.action;orig_slot=rig.animation_data.action_slot;orig_frame=orig_scene.frame_current;saved={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
cam=studio.camera;cam_matrix=cam.matrix_world.copy();cam_scale=cam.data.ortho_scale;old_frame=studio.frame_current;old_path=studio.render.filepath;old_size=(studio.render.resolution_x,studio.render.resolution_y,studio.render.resolution_percentage);old_format=studio.render.image_settings.file_format;old_engine=studio.render.engine
floor=bpy.data.objects['HC GIF | floor'];floor_hidden=floor.hide_render
objects=[];meshes=[];materials=[];actions=[];done=[]
out=Path(PROJECT_ROOT)/'build/terrain_previews';out.mkdir(parents=True,exist_ok=True)
labels=globals().get('HC_EXT_RENDER_LABELS',['21 Sprint Into Jump'])
def distance(spec,t):return spec['travel_fn'](t) if 'travel_fn' in spec else spec['speed']*t/24
def mesh_object(name,vs,fs,colors):
 me=bpy.data.meshes.new('HC TEMP PREVIEW '+name);meshes.append(me);me.from_pydata(vs,[],fs);me.update()
 ob=bpy.data.objects.new('HC TEMP PREVIEW '+name,me);objects.append(ob);studio.collection.objects.link(ob)
 for i,c in enumerate(colors):
  mat=bpy.data.materials.new('HC TEMP PREVIEW material '+str(i));materials.append(mat);mat.diffuse_color=(*c,1);me.materials.append(mat)
 for p in me.polygons:p.material_index=p.index%len(colors)
 return ob
try:
 win.scene=studio;studio.render.engine='BLENDER_WORKBENCH';studio.render.image_settings.file_format='PNG';studio.render.resolution_x=640;studio.render.resolution_y=720;studio.render.resolution_percentage=100
 for spec in bpy.app.driver_namespace['HC animation library specs']:
  if spec['label'] not in labels:continue
  for ob in objects:ob.hide_render=True
  terrain='terrain_mode' in spec;floor.hide_render=terrain
  dlast=distance(spec,spec['duration']);lo=min(0,-dlast)-5;hi=max(0,-dlast)+5
  if terrain:
   k=spec['terrain_kind'];mode=spec['terrain_mode'];dx=.20;dy=.08;nx=41;ny=math.ceil((hi-lo)/dy)+1;vs=[];fs=[]
   for j in range(ny):
    y=lo+(hi-lo)*j/(ny-1)
    for i in range(nx):
     x=-4+8*i/(nx-1);vs.append((x,y,ext['terrain_height'](k,mode,x,y)))
   for j in range(ny-1):
    for i in range(nx-1):
     a=j*nx+i;fs.append((a,a+1,a+nx+1));fs.append((a,a+nx+1,a+nx))
   mesh_object('reference '+mode,vs,fs,[(.115,.14,.125),(.12,.147,.132),(.127,.15,.135),(.12,.145,.13)])
  # Cross markings make controller movement, braking and incline visible.
  vs=[];fs=[]
  for y in range(math.floor(lo),math.ceil(hi)+1):
   a=len(vs)
   for x,yy in [(-3,y-.018),(3,y-.018),(3,y+.018),(-3,y+.018)]:
    z=ext['terrain_height'](spec['terrain_kind'],spec['terrain_mode'],x,yy)+.003 if terrain else .0005
    vs.append((x,yy,z))
   if not terrain or spec['terrain_mode']!='rough':fs.append((a,a+1,a+2,a+3))
  if fs:mesh_object('travel markings',vs,fs,[(.25,.29,.28)])
  ctx['reset']();rig.animation_data.action=bpy.data.actions[spec['name']]
  act=rig.animation_data.action.copy();act.name='HC TEMP PREVIEW | '+spec['label'];act.use_fake_user=False;actions.append(act);rig.animation_data.action=act
  for f in range(1,spec['duration']+2):
   studio.frame_set(f);rig.pose.bones['CTRL.root'].location=(0,-distance(spec,f-1),spec['fn'](f-1)['preview_z']);rig.pose.bones['CTRL.root'].keyframe_insert(data_path='location',frame=f)
  jump='Jump' in spec['label'];target=Vector((0,-.20,3.65 if jump else 2.85));cam.location=target+Vector((11,-13,10));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=9.2 if jump else 6.7
  bpy.context.view_layer.update();tracking=cam.matrix_world.copy();slug=spec['label'].lower().replace(' ','_');folder=out/slug;folder.mkdir(exist_ok=True)
  frames=globals().get('HC_EXT_RENDER_FRAME_OVERRIDE') or list(range(1,spec['duration']+(1 if spec['loop'] else 2),spec.get('preview_frame_step',2)))
  for f in frames:
   studio.frame_set(f);cam.matrix_world=tracking;cam.location.y-=distance(spec,f-1)
   if terrain:cam.location.z+=spec['fn'](f-1)['preview_z']
   studio.render.filepath=str(folder/f'frame_{f:03d}.png');bpy.ops.render.render(write_still=True)
  done.append({'clip':spec['label'],'frames':len(frames),'folder':str(folder)})
finally:
 studio.render.engine=old_engine;studio.render.image_settings.file_format=old_format;floor.hide_render=floor_hidden;cam.matrix_world=cam_matrix;cam.data.ortho_scale=cam_scale;studio.render.filepath=old_path;studio.render.resolution_x,studio.render.resolution_y,studio.render.resolution_percentage=old_size
 studio.frame_set(old_frame);win.scene=orig_scene;rig.animation_data.action=orig_action
 if orig_slot:rig.animation_data.action_slot=orig_slot
 for n,m in saved.items():rig.pose.bones[n].matrix_basis=m
 orig_scene.frame_set(orig_frame)
 for o in objects:bpy.data.objects.remove(o,do_unlink=True)
 for m in meshes:bpy.data.meshes.remove(m)
 for m in materials:bpy.data.materials.remove(m)
 for a in actions:bpy.data.actions.remove(a)
print(json.dumps({'rendered':done,'saved':False}))
