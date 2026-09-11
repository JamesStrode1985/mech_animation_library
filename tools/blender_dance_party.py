"""Build the HELLCAT dance emote in live Blender; supply PROJECT_ROOT. Never saves .blend."""
import bpy,math,json
from mathutils import Vector
from pathlib import Path

rig=bpy.data.objects['HELLCAT | CURRENT MECH RIG'];scene=bpy.context.scene
ctx=bpy.app.driver_namespace['HC animation build context']
LABEL='46 Dance Party';DURATION=192
def smooth(x):
    x=max(0,min(1,x));return x*x*(3-2*x)
def state(t):
    st=ctx['state']();env=smooth(t/6)*(1-smooth((t-180)/12))
    beat=t/12;u=beat%1;bar=int(t//48);wave=math.sin(math.pi*u)
    active='L' if int(beat)%2==0 else 'R'
    sway=math.sin(math.pi*beat)
    z=(-.13-.10*(1-wave))*env
    x=-.14*sway*env
    yaw=22*math.sin(math.pi*beat/2)*env
    roll=-6*sway*env;pitch=(3+4*math.sin(math.tau*beat))*env
    if bar==2:
        # Both feet stay planted for a rapid hull shimmy and alternating pod wave.
        x=.12*math.sin(math.pi*beat)*env
        yaw=28*math.sin(math.tau*beat/2)*env
        roll=7*math.sin(math.tau*beat)*env
        z=(-.19+.055*math.cos(math.tau*beat))*env
    if bar>=3:
        flourish=smooth((t-144)/8)*(1-smooth((t-168)/20))
        yaw=(30*flourish+10*math.sin(math.pi*beat/2))*env
        pitch=(2*flourish+3*math.sin(math.tau*beat))*env
    ctx['loc'](st,'CTRL.pelvis',(x,0,z))
    ctx['rot'](st,'CTRL.torso',(pitch,yaw,roll))
    ctx['rot'](st,'CTRL.sensor.yaw',(0,-yaw*.55,0))
    ctx['rot'](st,'CTRL.sensor.pitch',(-pitch*.5+3*math.sin(math.tau*beat)*env,0,0))
    for side,sign in [('L',1),('R',-1)]:
        v=Vector((0,0,0))
        if side==active and bar!=2:
            lift=.30 if bar==0 else .24 if bar==1 else .36
            v.z=lift*wave**1.2*env
            if bar==1:
                v.x=sign*.23*wave*env;v.y=.22*math.sin(math.tau*u)*env
            else:v.y=-.16*wave*env
        ctx['loc'](st,'CTRL.foot_IK.'+side,v)
        st['contact'][side]=v.z<1e-6;st['lift'][side]=v.z
        ctx['rot'](st,'CTRL.ankle_tilt.'+side,(-10*wave*env if v.z else 0,0,0))
        pod=(-9+9*math.sin(math.pi*beat+sign*math.pi/2))*env
        if bar>=3:pod=-18*smooth((t-144)/8)*env
        ctx['rot'](st,'CTRL.pod_aim.'+side,(pod,0,0))
    cannon=(-6+5*math.sin(math.pi*beat/2))*env
    if bar>=3:cannon=-17*smooth((t-144)/8)*env
    ctx['rot'](st,'CTRL.cannon.aim',(cannon,0,0))
    ctx['rot'](st,'CTRL.antenna.head',(4*math.sin(math.tau*beat+.5)*env,0,0))
    ctx['rot'](st,'CTRL.antenna.hull',(2.5*math.sin(math.tau*beat-.3)*env,0,0))
    return st

digest=bpy.app.driver_namespace['HC terrain revision context']['digest']
bpy.app.driver_namespace['HC dance protected actions']={a.name:digest(a) for a in bpy.data.actions if a.name.startswith('HC ANIM | ') and a.name!='HC ANIM | '+LABEL}
original=(rig.animation_data.action,rig.animation_data.action_slot,scene.frame_current)
try:
    old=bpy.data.actions.get('HC ANIM | '+LABEL)
    if old:
        assert old.get('HC dance emote');old.name='HC ARCHIVE | '+LABEL;old.use_fake_user=True;old.asset_clear()
    action=bpy.data.actions.new('HC ANIM | '+LABEL);action.use_fake_user=True;rig.animation_data.action=action
    samples=[]
    for f in range(1,DURATION+2):
        scene.frame_set(f);st=state(f-1);ctx['apply'](st)
        for n in ctx['controls']:
            p=rig.pose.bones[n]
            if n in ctx['FX']:p.keyframe_insert(data_path='scale',frame=f,group='Optional weapon FX')
            else:
                p.keyframe_insert(data_path='location',frame=f,group=n);p.keyframe_insert(data_path='rotation_euler',frame=f,group=n)
        samples.append({'frame':f,'contacts':st['contact']})
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:key.interpolation='LINEAR'
                    fc.modifiers.new('CYCLES')
    markers=[('Stomp groove',1),('Side shuffle',49),('Hull shimmy',97),('Victory flourish',145),('Return to ready',181)]
    for name,f in markers:action.pose_markers.new(name).frame=f
    action['HC animation library']='MECH_2026_09';action['HC dance emote']=True;action['FPS']=24;action['Loop']=True;action['BPM']=120
    action['Category']='Emote';action['Root motion']='None';action['Contact samples']=json.dumps(samples)
    action.asset_mark();action.asset_data.description='8-second party dance: stomps, shuffle, hull shimmy, pod waves and victory flourish. 120 BPM, stationary root.'
finally:
    ctx['reset']();rig.animation_data.action=original[0]
    if original[1]:rig.animation_data.action_slot=original[1]
    scene.frame_set(original[2])
bpy.app.driver_namespace['HC dance context']={'state':state,'label':LABEL,'duration':DURATION}
row={'label':LABEL,'source_label':LABEL,'action':'HC ANIM | '+LABEL,'slug':'46_dance_party','duration_frames':DURATION,'fps':24,'loop':True,'category':'Emote','gallery_group':'emotes','nominal_speed_units_per_s':0,'bpm':120,'preview_frame_step':2,'revision':'Dance party','markers':[{'name':n,'frame':f} for n,f in markers]}
(Path(PROJECT_ROOT)/'build/dance_action.json').write_text(json.dumps(row,indent=2)+'\n')
print(json.dumps({'created':row['action'],'duration_seconds':8,'saved':False}))
