import bpy,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(PROJECT_ROOT);ctx=bpy.app.driver_namespace['T1 library'];source=bpy.context.scene
studio=bpy.data.scenes.new('T1 | Gallery preview studio')
for o in source.objects:
 if o.visible_get() and o.type not in ['CAMERA','LIGHT']:studio.collection.objects.link(o)
cam=bpy.data.objects.new('T1 preview | camera',bpy.data.cameras.new('T1 preview | camera'));studio.collection.objects.link(cam)
target=Vector((0,-.5,5.4));direction=Vector((25,-33,19)).normalized();cam.location=target+direction*45;cam.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=24;studio.camera=cam
count=81;step=.65;verts=[((i-40)*step,(j-40)*step,0) for j in range(count) for i in range(count)];faces=[(j*count+i,j*count+i+1,(j+1)*count+i+1,(j+1)*count+i) for j in range(count-1) for i in range(count-1)]
me=bpy.data.meshes.new('T1 preview ground');me.from_pydata(verts,[],faces);ground=bpy.data.objects.new('T1 preview | reference ground',me);studio.collection.objects.link(ground)
for n,color in [('A',(.115,.14,.155,1)),('B',(.15,.17,.185,1))]:
 m=bpy.data.materials.new('T1 preview slate '+n);m.diffuse_color=color;me.materials.append(m)
for p in me.polygons:
 y,x=divmod(p.index,count-1);p.material_index=(x//4+y//4)%2
studio.render.engine='BLENDER_WORKBENCH';studio.render.resolution_x=640;studio.render.resolution_y=576;studio.render.resolution_percentage=100;studio.render.image_settings.file_format='PNG';studio.render.fps=24
studio.world=bpy.data.worlds.new('T1 preview world');studio.world.color=(.08,.10,.12);studio.view_settings.view_transform='Standard'
sh=studio.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=1.25;sh.curvature_valley_factor=1.1;sh.background_type='WORLD';sh.show_specular_highlight=True
ctx['studio']=studio.name;ctx['ground']=ground.name;ctx['camera_direction']=direction
print('Created separate T1 gallery studio')
