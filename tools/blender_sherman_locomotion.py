"""Author Sherman locomotion through Blender MCP. Supply PROJECT_ROOT; never saves .blend."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
ROOT=Path(PROJECT_ROOT)
r=bpy.data.objects['SHERMAN WALKER | ANIMATION RIG']
scene=bpy.context.scene
if 'SW locomotion context' not in bpy.app.driver_namespace:
    bpy.app.driver_namespace['SW locomotion context']={
        'action':r.animation_data.action if r.animation_data else None,
        'slot':r.animation_data.action_slot if r.animation_data else None,
        'pose':{p.name:(p.matrix_basis.copy(),p.rotation_mode) for p in r.pose.bones},
        'frame':scene.frame_current,'range':(scene.frame_start,scene.frame_end),'fps':scene.render.fps}
ctx=bpy.app.driver_namespace['SW locomotion context']
r.animation_data_create()
for p in r.pose.bones:
    p.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
# Geometry under the foot, in rig coordinates, determines sole contact when rolling.
cloud={s:[] for s in ['L','R']}
for o in scene.objects:
    if o.type!='MESH' or not o.visible_get():continue
    transform=r.matrix_world.inverted()@o.matrix_world
    for side in cloud:
        groups={g.index for g in o.vertex_groups if g.name in ['DEF.foot.'+side,'CTRL.toe.'+side]}
        if not groups:continue
        cloud[side].extend(transform@v.co for v in o.data.vertices if any(g.group in groups and g.weight>.99 for g in v.groups))
# Three authored rhythms: longer support for walking; compression/flight for running.
configs=[
 dict(label='01 Walk',slug='01_walk',frames=48,duty=.64,stride=2.65,lift=.48,drop=.48,bob=.13,lean=2.5,sway=.18,arm=9),
 dict(label='02 Run',slug='02_run',frames=32,duty=.43,stride=3.45,lift=1.10,drop=.88,bob=.29,lean=7,sway=.10,arm=15),
 dict(label='03 Sprint',slug='03_sprint',frames=24,duty=.35,stride=4.15,lift=1.65,drop=1.13,bob=.43,lean=11,sway=.07,arm=20)]

def smooth(a):
    a=max(0,min(1,a));return a*a*(3-2*a)

def world_delta(name,translation=(0,0,0),angles=(0,0,0)):
    p=r.pose.bones[name];basis=p.bone.matrix_local.to_3x3()
    p.location=basis.inverted()@Vector(translation)
    q=Quaternion((0,0,1),math.radians(angles[2]))@Quaternion((0,1,0),math.radians(angles[1]))@Quaternion((1,0,0),math.radians(angles[0]))
    p.rotation_mode='QUATERNION';p.rotation_quaternion=basis.to_quaternion().inverted()@q@basis.to_quaternion()

def pose(c,t):
    for p in r.pose.bones:p.matrix_basis=Matrix.Identity(4)
    cycle=2*math.pi*t
    # Lowest shortly after impact, extension before the next contact.
    bounce=-c['drop']-c['bob']*math.cos(2*cycle-.7)
    world_delta('CTRL.pelvis',(c['sway']*math.sin(cycle),0,bounce),(0,1.1*math.sin(cycle),2.6*math.sin(cycle)))
    world_delta('CTRL.torso',angles=(c['lean']+1.1*math.sin(2*cycle-.8),-.8*math.sin(cycle),-4.2*math.sin(cycle)))
    for side,phase in [('L',t%1),('R',(t+.5)%1)]:
        duty=c['duty'];distance=c['stride']
        if phase<duty:
            u=phase/duty;y=-distance/2+distance*u;lift=0
            pitch=-5*(1-smooth(u/.18))+12*smooth((u-.78)/.22)
        else:
            u=(phase-duty)/(1-duty)
            # Hermite swing retains the stance velocity at both ends.
            m=distance*(1-duty)/duty
            y=(2*u**3-3*u**2+1)*(distance/2)+(u**3-2*u*u+u)*m+(-2*u**3+3*u*u)*(-distance/2)+(u**3-u*u)*m
            lift=c['lift']*math.sin(math.pi*u)**1.4
            pitch=12*(1-smooth(u/.35))-5*smooth((u-.55)/.45)
        foot=r.pose.bones['CTRL.foot_IK.'+side];center=foot.bone.head_local
        q=Quaternion((1,0,0),math.radians(pitch))
        lowest=min((center+q@(v-center)).z for v in cloud[side])
        ground=min(v.z for v in cloud[side])
        world_delta(foot.name,(0,y,lift+ground-lowest),(pitch,0,0))
        world_delta('CTRL.knee_pole.'+side,(0,-1,0))
    # Keep the approved shoulder-to-hand chain straight; swing only at the shoulder.
    # Forearm and wrist rest axes have different rolls: local X is not a shared hinge.
    p=r.pose.bones['CTRL.arm.upper.L'];p.rotation_mode='XYZ'
    p.rotation_euler.x=math.radians(-8-c['lean']+c['arm']*math.sin(cycle+.3))
    p=r.pose.bones['CTRL.arm.forearm.L'];p.rotation_mode='XYZ'
    p.rotation_euler=(0,0,0)
    p=r.pose.bones['CTRL.arm.gun.L'];p.rotation_mode='XYZ';p.rotation_euler=(0,0,0)
    p=r.pose.bones['CTRL.arm.upper.R'];p.rotation_mode='XYZ';p.rotation_euler.x=math.radians(-2+3*math.sin(cycle+math.pi+.3))
    p=r.pose.bones['CTRL.cannon.aim'];p.rotation_mode='XYZ';p.rotation_euler.x=math.radians(-c['lean']*.35)
    p=r.pose.bones['CTRL.antenna'];p.rotation_mode='XYZ';p.rotation_euler.x=math.radians(1.2*math.sin(2*cycle-1.2))

controls=['CTRL.root','CTRL.pelvis','CTRL.torso','CTRL.foot_IK.L','CTRL.foot_IK.R','CTRL.knee_pole.L','CTRL.knee_pole.R','CTRL.arm.upper.L','CTRL.arm.forearm.L','CTRL.arm.gun.L','CTRL.arm.upper.R','CTRL.cannon.aim','CTRL.antenna']
for c in configs:
    name='SW ANIM | '+c['label']
    if name in bpy.data.actions:
        old=bpy.data.actions[name];old.name=name+' | previous';old.use_fake_user=True
    action=bpy.data.actions.new(name);action.use_fake_user=True;r.animation_data.action=action
    for f in range(1,c['frames']+2):
        pose(c,(f-1)/c['frames'])
        for name in controls:
            p=r.pose.bones[name]
            p.keyframe_insert('location',frame=f,group=name)
            p.keyframe_insert('rotation_quaternion' if p.rotation_mode=='QUATERNION' else 'rotation_euler',frame=f,group=name)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:key.interpolation='LINEAR'
    for frame,label in [(1,'L contact'),(1+c['frames']//2,'R contact'),(1+round(c['frames']*c['duty']),'L toe-off')]:
        action.pose_markers.new(label).frame=frame
    action['gameplay_root_motion']='in-place';action['fps']=24
    action['motion_notes']='Human-like gait coordination, heavy load compression and controlled weapon inertia; artistic mass, not physics simulation.'
    c['action']=action.name
ctx['configs']=configs;ctx['controls']=controls
scene.render.fps=24
r.animation_data.action=bpy.data.actions[configs[0]['action']]
scene.frame_start=1;scene.frame_end=configs[0]['frames'];scene.frame_set(1)
bpy.context.view_layer.update()
print(json.dumps({'created':configs,'ground':{s:min(p.z for p in cloud[s]) for s in cloud},'saved_blend':False}))
