"""Create a separate workbench preview scene; original scene settings stay intact."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(PROJECT_ROOT);ctx=bpy.app.driver_namespace['SW locomotion context']
source=bpy.context.scene
name='SW | Locomotion preview studio'
assert name not in bpy.data.scenes
studio=bpy.data.scenes.new(name)
for o in source.objects:
    if o.type not in ['CAMERA','LIGHT'] and (o.visible_get() or o.type in ['EMPTY','ARMATURE']):studio.collection.objects.link(o)
cam=bpy.data.objects.new('SW preview | camera',bpy.data.cameras.new('SW preview | camera'));studio.collection.objects.link(cam)
cam.location=(24,-34,20);target=Vector((0,0,8));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=20.5;studio.camera=cam
mesh=bpy.data.meshes.new('SW preview | ground');mesh.from_pydata([(-200,-200,0),(200,-200,0),(200,200,0),(-200,200,0)],[],[(0,1,2,3)])
ground=bpy.data.objects.new('SW preview | ground',mesh);studio.collection.objects.link(ground);ground.color=(.12,.14,.15,1)
mat=bpy.data.materials.new('SW preview | slate');mat.diffuse_color=(.12,.14,.15,1);ground.data.materials.append(mat)
studio.render.engine='BLENDER_WORKBENCH';studio.render.resolution_x=640;studio.render.resolution_y=720;studio.render.resolution_percentage=100;studio.render.image_settings.file_format='PNG';studio.render.fps=24
sh=studio.display.shading;sh.light='STUDIO';sh.studiolight_rotate_z=.4;sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=1.4;sh.curvature_valley_factor=1.0;sh.show_specular_highlight=True;sh.background_type='WORLD';sh.background_color=(.09,.105,.12);sh.show_object_outline=False
studio.world=bpy.data.worlds.new('SW preview | world');studio.world.color=(.09,.105,.12)
studio.view_settings.view_transform='Standard'
ctx['studio']=studio.name
print(json.dumps({'studio':studio.name,'objects':len(studio.objects),'resolution':[640,720],'engine':studio.render.engine}))
