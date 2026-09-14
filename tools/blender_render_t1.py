"""Render baked T1 Actions through a bounded Blender timer; no .blend save.

Run after the library and studio scripts through Blender MCP with PROJECT_ROOT.
Set RENDER_NUMBERS to a subset for review or omit for the full library.
Progress and resumable raw frames stay in ignored build/t1_library.
"""
import bpy, json, math, time, traceback
from pathlib import Path
from mathutils import Vector

ctx = bpy.app.driver_namespace['T1 library']
root = Path(PROJECT_ROOT)
studio = bpy.data.scenes[ctx['studio']]
rig = bpy.data.objects[ctx['rig']]
master = bpy.data.objects['T1 | master transform']
ground = bpy.data.objects[ctx['ground']]
base = master.location.copy()
numbers = globals().get('RENDER_NUMBERS', list(range(1,48)))
queue = []
for spec in ctx['specs']:
    if spec['number'] not in numbers: continue
    frames = list(range(1, spec['duration_frames']+1, spec['preview_frame_step']))
    if not spec['loop']: frames.append(spec['duration_frames']+1)
    folder = root/'build/t1_library'/spec['slug']
    folder.mkdir(parents=True, exist_ok=True)
    for frame in frames:
        path = folder/f'frame_{frame:04d}.png'
        if not path.exists(): queue.append((spec,frame,path))
status = dict(total=len(queue), done=0, running=True, started=time.time())
ctx['render_status'] = status
studio.display.render_aa = '8'
status_path = root/'build/t1_library/render_progress.json'

def write_status():
    status_path.write_text(json.dumps(status, indent=2))

def render_next():
    try:
        if not queue:
            master.location=base
            status.update(running=False, finished=time.time())
            write_status()
            return None
        spec, frame, path = queue.pop(0)
        rig.animation_data.action = bpy.data.actions[spec['action']]
        master.location = base
        travel = Vector((0,0,0))
        if spec.get('controller_preview_travel'):
            q=max(0,min(1,(frame-11)/23));q=q*q*(3-2*q)
            travel=Vector(spec['controller_direction'])*spec['controller_distance_units']*q
            master.location=base+travel
        # Shared objects must first evaluate in their source scene. Changing only
        # the secondary render scene leaves the original rig at its prior pose.
        bpy.data.scenes[ctx['source_scene']].frame_set(frame)
        bpy.context.view_layer.update()
        studio.frame_set(frame)
        for v in ground.data.vertices:
            v.co.z=ctx['terrain'](spec,v.co.x,v.co.y,frame-1)
        ground.data.update()
        # Fixed shot within each clip. Extra room for falls and controller travel.
        cam=studio.camera;direction=ctx['camera_direction']
        center=Vector((0,-.5,5.4));scale=24
        if spec.get('controller_preview_travel'):
            center+=Vector(spec['controller_direction'])*spec['controller_distance_units']*.5;scale=27
        cam.location=center+direction*45;cam.data.ortho_scale=scale
        studio.render.filepath=str(path)
        bpy.ops.render.render(write_still=True,scene=studio.name)
        status.update(done=status['done']+1,clip=spec['label'],frame=frame,updated=time.time())
        write_status()
        return .05
    except Exception:
        master.location=base
        status.update(running=False,error=traceback.format_exc())
        write_status()
        return None

ctx['render_timer']=render_next
write_status()
bpy.app.timers.register(render_next,first_interval=.5)
print('Queued',len(queue),'preview frames')
