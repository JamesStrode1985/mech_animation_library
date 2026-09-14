"""Isolated hover preview studio. Live skeleton shared, original review scene unchanged."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
ctx=bpy.app.driver_namespace['HT library'];studio=bpy.data.scenes.new('HT-01 | Gallery preview studio');studio.collection.children.link(bpy.data.collections['HT-01 | Rigged model'])
cam=bpy.data.objects.new('HT gallery camera',bpy.data.cameras.new('HT gallery camera'));studio.collection.objects.link(cam);studio.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=18.8
d=Vector((19,-28,18)).normalized();cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.location=Vector((0,-.8,3.7))+d*40
count=51;step=.8;vs=[((i-25)*step,(j-25)*step,0) for j in range(count) for i in range(count)];fs=[(j*count+i,j*count+i+1,(j+1)*count+i+1,(j+1)*count+i) for j in range(count-1) for i in range(count-1)]
me=bpy.data.meshes.new('HT gallery ground');me.from_pydata(vs,[],fs);ground=bpy.data.objects.new('HT gallery reference ground',me);studio.collection.objects.link(ground)
for name,color in [('A',(.115,.14,.155,1)),('B',(.16,.185,.20,1))]:
 m=bpy.data.materials.new('HT gallery slate '+name);m.diffuse_color=color;me.materials.append(m)
for p in me.polygons:
 j,i=divmod(p.index,count-1);p.material_index=(i//2+j//2)%2
# A preview-only flash emphasizes firing events; it is not weighted/exported tank geometry.
bpy.ops.mesh.primitive_cone_add(vertices=12,radius1=.20,radius2=.015,depth=.65)
flash=bpy.context.object;flash.name='HT gallery cannon flash'
for c in list(flash.users_collection):c.objects.unlink(flash)
studio.collection.objects.link(flash);m=bpy.data.materials.new('HT gallery flash amber');m.diffuse_color=(1.,.50,.07,1);flash.data.materials.append(m);flash.hide_render=True
studio.render.engine='BLENDER_WORKBENCH';studio.render.resolution_x=576;studio.render.resolution_y=512;studio.render.resolution_percentage=100;studio.render.fps=24;studio.render.image_settings.file_format='PNG';studio.display.render_aa='8';studio.world=bpy.data.worlds.new('HT gallery world');studio.world.color=(.085,.105,.12);studio.view_settings.view_transform='Standard'
sh=studio.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=1.15;sh.curvature_valley_factor=1.0;sh.background_type='WORLD'
for spec in ctx['specs']:
 spec['preview_frame_step']=1 if spec['number']==35 else 2 if spec['number'] in list(range(9,13))+list(range(42,48)) else 3
ctx.update(studio=studio.name,ground=ground.name,camera_direction=d,flash=flash.name)
(Path(PROJECT_ROOT)/'build/hover_library/specs.json').write_text(json.dumps(ctx['specs'],indent=2))
print('Hover preview studio ready')
