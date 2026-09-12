"""Render bounded batches of the Sherman library through Blender MCP; never save .blend."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(PROJECT_ROOT);lib=bpy.app.driver_namespace['SW full library'];base=bpy.app.driver_namespace['SW locomotion context']
spec=next(s for s in lib['specs'] if s['number']==RENDER_NUMBER)
studio=bpy.data.scenes[base['studio']];r=bpy.data.objects['SHERMAN WALKER | ANIMATION RIG']
report=json.loads((ROOT/'build/sherman_full/verification'/(spec['slug']+'.json')).read_text())
direction=Vector((24,-34,24 if spec.get('terrain_mode') else 12)).normalized();q=(-direction).to_track_quat('-Z','Y')
right=q@Vector((1,0,0));up=q@Vector((0,1,0));lo,hi=report['view_bounds']
master=bpy.data.objects['SHERMAN WALKER | master transform'];master_saved=master.location.copy()
travel=spec.get('controller_preview_travel',False)
exec(compile((ROOT/'tools/sherman_controller.py').read_text(),'controller_travel','exec'))
if travel:
    offset=Vector(spec['controller_direction'])*spec['controller_distance_units']
    lo=[a+min(0,offset.dot(axis)) for a,axis in zip(lo,[right,up])]
    hi=[a+max(0,offset.dot(axis)) for a,axis in zip(hi,[right,up])]
if spec.get('terrain_mode'):
    import numpy as np
    cache=lib.setdefault('terrain_camera_bounds',{})
    if spec['slug'] not in cache:
        r.animation_data.action=bpy.data.actions[spec['action']];axes=np.array([right,up]).T
        lows=[];highs=[]
        for f in range(1,spec['duration_frames']+1,max(1,spec['duration_frames']//10)):
            bpy.context.scene.frame_set(f);bpy.context.view_layer.update();p=lib['world_points']()@axes;lows.append(p.min(axis=0));highs.append(p.max(axis=0))
        cache[spec['slug']]=(np.min(lows,axis=0).tolist(),np.max(highs,axis=0).tolist())
    lo,hi=cache[spec['slug']]
center=right*((lo[0]+hi[0])/2)+up*((lo[1]+hi[1])/2)
camera=studio.camera;camera.location=center+direction*40;camera.rotation_euler=q.to_euler()
camera.data.ortho_scale=max(20.5,(hi[0]-lo[0])*1.14,(hi[1]-lo[1])*640/720*1.14)
if travel:camera.data.ortho_scale=max(20.5,(hi[0]-lo[0])*720/640*1.14,(hi[1]-lo[1])*1.14)
ground=bpy.data.objects['SW preview | ground'];ground.hide_render=bool(spec.get('terrain_mode')) or travel
grid=bpy.data.objects.get('SW preview | dodge ground')
if travel and grid is None:
    count=41;step=2;verts=[((x-20)*step,(y-20)*step,0) for y in range(count) for x in range(count)]
    faces=[(y*count+x,y*count+x+1,(y+1)*count+x+1,(y+1)*count+x) for y in range(count-1) for x in range(count-1)]
    mesh=bpy.data.meshes.new('SW dodge ground');mesh.from_pydata(verts,[],faces);mesh.update()
    grid=bpy.data.objects.new('SW preview | dodge ground',mesh);studio.collection.objects.link(grid)
    for i,color in enumerate([(.12,.145,.16,1),(.18,.205,.22,1)]):
        material=bpy.data.materials.new('SW dodge tile '+str(i));material.diffuse_color=color;mesh.materials.append(material)
    for polygon in mesh.polygons:
        y,x=divmod(polygon.index,count-1);polygon.material_index=(x+y)%2
if grid:grid.hide_render=not travel
for o in studio.objects:
    if o.name.startswith('SW terrain |'):o.hide_render=True
terrain=None
if spec.get('terrain_mode'):
    name='SW terrain | '+spec['slug'];terrain=bpy.data.objects.get(name)
    if terrain is None:
        # Studio-only surface; the gameplay rig remains in place. Heights use the exact gait sampler.
        extent=40;step=.5;count=int(2*extent/step)+1
        vertices=[(x*step-extent,y*step-extent,lib['terrain'](spec,x*step-extent,y*step-extent,0)) for y in range(count) for x in range(count)]
        faces=[(j*count+i,j*count+i+1,(j+1)*count+i+1,(j+1)*count+i) for j in range(count-1) for i in range(count-1)]
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
        terrain=bpy.data.objects.new(name,mesh);studio.collection.objects.link(terrain);terrain.scale=(1.1,)*3
        for index,color in enumerate([(.135,.155,.165,1),(.15,.17,.18,1)]):
            mat=bpy.data.materials.get('SW terrain slate '+str(index)) or bpy.data.materials.new('SW terrain slate '+str(index))
            mat.diffuse_color=color;mesh.materials.append(mat)
        for p in mesh.polygons:
            yy,xx=divmod(p.index,count-1);p.material_index=((xx//4)+(yy//4))%2
    terrain.hide_render=False
saved=bpy.context.window.scene;out=ROOT/'build/sherman_full'/spec['slug'];out.mkdir(parents=True,exist_ok=True)
try:
    bpy.context.window.scene=studio;r.animation_data.action=bpy.data.actions[spec['action']]
    for frame in RENDER_FRAMES:
        if travel:master.location=master_saved+Vector(spec['controller_direction'])*controller_distance(spec,frame)
        if terrain:terrain.location.y=spec.get('terrain_period',0)*(frame-1)/spec['duration_frames']*1.1 if spec['terrain_mode']=='rough' else 0
        studio.frame_set(frame);studio.render.filepath=str(out/f'frame_{frame:03d}.png');bpy.ops.render.render(write_still=True)
finally:
    ground.hide_render=False
    master.location=master_saved
    if grid:grid.hide_render=True
    if terrain:terrain.hide_render=True
    bpy.context.window.scene=saved
print(json.dumps({'clip':spec['label'],'rendered':list(RENDER_FRAMES)}))
