"""Create HELLCAT death Actions in the live Blender scene. Does not save the blend.

Requires the existing HELLCAT animation build context in Blender's driver namespace.
Run through Blender MCP, with PROJECT_ROOT supplied as this repository's absolute path.
"""
import bpy, math, json
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix

root = Path(PROJECT_ROOT)
rig = bpy.data.objects['HELLCAT | CURRENT MECH RIG']
scene = bpy.context.scene
ctx = bpy.app.driver_namespace['HC animation build context']
old_action = rig.animation_data.action
old_frame = scene.frame_current
fall_name = 'CTRL.death_fall'

if fall_name not in rig.data.bones:
    rig.animation_data.action = None
    ctx['reset']()
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    children = [b.name for b in rig.data.bones['CTRL.root'].children]
    bpy.ops.object.mode_set(mode='EDIT')
    bone = rig.data.edit_bones.new(fall_name)
    bone.head = (0,0,0); bone.tail = (0,.5,0)
    bone.parent = rig.data.edit_bones['CTRL.root']; bone.use_deform = False
    for name in children:
        rig.data.edit_bones[name].parent = bone
    bpy.ops.object.mode_set(mode='OBJECT')
    pb = rig.pose.bones[fall_name]; pb.rotation_mode = 'XYZ'
    pb.custom_shape = rig.pose.bones['CTRL.root'].custom_shape
    pb.custom_shape_scale_xyz = (.7,.7,.7)
    pb['Purpose'] = 'Whole-body death offset below stationary gameplay root. Bake with deform bones on export.'
    rig.data.collections['01 Animator controls'].assign(rig.data.bones[fall_name])
    for key in ['controls','dynamic']:
        ctx[key].append(fall_name)
    for action in list(bpy.data.actions):
        if not action.name.startswith('HC ANIM | '): continue
        rig.animation_data.action = action
        pb.location = (0,0,0); pb.rotation_euler = (0,0,0)
        for frame in [action.frame_range[0], action.frame_range[1]]:
            for path in ['location','rotation_euler']:
                pb.keyframe_insert(data_path=path, frame=frame, group=fall_name)

def smooth(t):
    t=max(0,min(1,t)); return t*t*(3-2*t)

CONFIG = [
    dict(label='39 Death Forward Collapse',kind='forward',duration=108,impact=56,begin=24,angle=78),
    dict(label='40 Death Backward Fall',kind='backward',duration=100,impact=46,begin=12,angle=-88),
    dict(label='41 Death Side Collapse',kind='side',duration=116,impact=66,begin=32,angle=-86),
]

def pose_state(c,t):
    st=ctx['state'](); k=c['kind']
    buckle=smooth((t-8)/(c['impact']-12))
    hit=math.sin(math.pi*min(1,t/12)) if t<12 else 0
    droop=smooth((t-c['impact']+3)/22)
    if k=='forward':
        ctx['loc'](st,'CTRL.pelvis',(0,-.03*buckle,-.54*buckle))
        ctx['rot'](st,'CTRL.torso',(-5*hit+5*buckle,80*smooth((t-10)/43),1.5*hit))
        feet={'L':(0,-.22*buckle,0),'R':(0,.25*buckle,.12*buckle)}
        ctx['rot'](st,'CTRL.cannon.aim',(-20*smooth((t-10)/30),0,0))
    elif k=='backward':
        ctx['loc'](st,'CTRL.pelvis',(0,.08*buckle,-.42*buckle))
        ctx['rot'](st,'CTRL.torso',(-9*hit+7*buckle,-8*buckle,0))
        feet={'L':(0,-.43*buckle,.10*buckle),'R':(0,-.13*buckle,.27*buckle)}
        ctx['rot'](st,'CTRL.cannon.aim',(8*droop,0,0))
    else:
        ctx['loc'](st,'CTRL.pelvis',(-.09*buckle,0,-.45*buckle))
        ctx['rot'](st,'CTRL.torso',(3*buckle,-10*buckle,7*hit+3*buckle))
        catch=math.sin(math.pi*smooth((t-12)/24))*.13 if t<36 else 0
        feet={'L':(.12*buckle,.16*buckle,.18*buckle),'R':(-.16*buckle,-.12*buckle,catch)}
        ctx['rot'](st,'CTRL.cannon.aim',(9*droop,0,0))
    for side,v in feet.items():
        ctx['loc'](st,'CTRL.foot_IK.'+side,v)
        st['contact'][side]=v[2]<.01;st['lift'][side]=v[2]
        ctx['rot'](st,'CTRL.hock_angle.'+side,(4*buckle,0,0))
        ctx['rot'](st,'CTRL.ankle_tilt.'+side,((8 if side=='L' else -5)*buckle,0,0))
        ctx['rot'](st,'CTRL.pod_aim.'+side,((12 if side=='L' else 17)*droop,0,0))
    ctx['rot'](st,'CTRL.sensor.pitch',(12*droop-6*hit,0,0))
    ctx['rot'](st,'CTRL.sensor.yaw',(0,9*droop,0))
    u=max(0,t-c['impact']); decay=math.exp(-u/8) if u else 0
    fade=1-smooth((t-c['impact']-22)/12)
    ctx['rot'](st,'CTRL.antenna.head',(4*decay*math.sin(u*.65)*fade,0,0))
    ctx['rot'](st,'CTRL.antenna.hull',(-3*decay*math.sin(u*.5)*fade,0,0))
    progress=max(0,min(1,(t-c['begin'])/(c['impact']-c['begin'])))
    angle=c['angle']*progress**2.15
    if t>c['impact']:angle += math.copysign(4,c['angle'])*decay*math.sin(u*.42)*fade
    bounce=.055*decay*math.sin(u*.5)**2*fade
    return st,angle,bounce

# Cache all bound model vertices for a conservative floor solve, excluding FX and hidden backups.
names=[n for n in bpy.app.driver_namespace['HC bound mesh names'] if n in bpy.data.objects]
mesh_objects=[bpy.data.objects[n] for n in names if bpy.data.objects[n].type=='MESH']
groups={}; count=0
for o in mesh_objects:
    local=rig.matrix_world.inverted()@o.matrix_world
    for v in o.data.vertices:
        for g in v.groups:
            bn=o.vertex_groups[g.group].name
            if bn not in rig.pose.bones or g.weight<=0:continue
            q=rig.data.bones[bn].matrix_local.inverted()@local@v.co
            groups.setdefault(bn,[]).append((q.x,q.y,q.z,1))
        count+=1
cloud={bn:np.asarray(points,dtype=np.float64) for bn,points in groups.items()}

def floor_low():
    lowest=1e9; source=None
    for bn,points in cloud.items():
        m=rig.matrix_world@rig.pose.bones[bn].matrix
        z=points@np.asarray(m[2],dtype=np.float64)
        v=float(z.min())
        if v<lowest:lowest=v;source=bn
    return lowest,source

def apply_death(c,t):
    st,angle,bounce=pose_state(c,t)
    ctx['apply'](st)
    fall=rig.pose.bones[fall_name]
    fall.rotation_euler=(math.radians(angle),0,0) if c['kind']!='side' else (0,math.radians(angle),0)
    bpy.context.view_layer.update()
    low,bone=floor_low()
    fall.location.z=.009-low+bounce
    bpy.context.view_layer.update()
    return {'floor_support':bone,'body_angle':angle,'bounce':bounce}

reports=[]
for c in CONFIG:
    name='HC ANIM | '+c['label']
    existing=bpy.data.actions.get(name)
    if existing:
        assert existing.get('HC death animation')
        existing.name='HC ARCHIVE | '+c['label']+' | previous death pass'
        existing.use_fake_user=True;existing.asset_clear()
    action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data.action=action
    supports=[]
    for f in range(1,c['duration']+2):
        scene.frame_set(f)
        detail=apply_death(c,f-1)
        for n in ctx['controls']:
            p=rig.pose.bones[n]
            if n in ctx['FX']:p.keyframe_insert(data_path='scale',frame=f,group='Optional weapon FX')
            else:
                p.keyframe_insert(data_path='location',frame=f,group=n)
                p.keyframe_insert(data_path='rotation_euler',frame=f,group=n)
        if f in [1,c['begin']+1,c['impact']+1,c['duration']+1]:supports.append(dict(frame=f,**detail))
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for point in fc.keyframe_points:point.interpolation='LINEAR'
    for name,f in [('Fatal hit',1),('Loss of balance',c['begin']+1),('Ground impact',c['impact']+1),('Settled',c['impact']+35)]:
        action.pose_markers.new(name).frame=f
    action['HC animation library']='MECH_2026_09';action['HC death animation']=True
    action['FPS']=24;action['Loop']=False;action['Category']='Death'
    action['Root motion']='Stationary CTRL.root; CTRL.death_fall supplies local corpse collapse. Hold last frame; disable gameplay locomotion.'
    action.asset_mark();action.asset_data.description='Death; '+c['kind']+' collapse; 24 fps; stationary gameplay root; final corpse pose held.'
    reports.append({'label':c['label'],'frames':c['duration']+1,'samples':supports})
rig.animation_data.action=old_action
ctx['reset']();scene.frame_set(old_frame)
bpy.app.driver_namespace['HC death context']={'config':CONFIG,'apply':apply_death,'floor_low':floor_low,'cloud':cloud,'meshes':names,'reports':reports}
print(json.dumps({'created':reports,'floor_vertices':count,'saved':False}))
