"""Build the HELLCAT Time Warp emote in live Blender; supply PROJECT_ROOT. Never saves .blend."""
import bpy,math,json
from mathutils import Vector
from pathlib import Path

rig=bpy.data.objects['HELLCAT | CURRENT MECH RIG'];scene=bpy.context.scene
ctx=bpy.app.driver_namespace['HC animation build context']
LABEL='47 Time Warp';DURATION=264
# 32 beats in 11 seconds at 24 fps: about 175 BPM. Not an audio-derived beat map.
BPM=32*60/(DURATION/24)
def smooth(x):
    x=max(0,min(1,x));return x*x*(3-2*x)
def ramp(b,a,z):return smooth((b-a)/(z-a))
def step(b,a,z,start,end,height=.20):
    if b<=a:return start,0
    if b>=z:return end,0
    p=(b-a)/(z-a);return start+(end-start)*smooth(p),height*math.sin(math.pi*p)**1.2

def state(t):
    st=ctx['state']();b=t*32/DURATION;env=ramp(b,0,1)*(1-ramp(b,30,32))
    narrow=ramp(b,10,14)*(1-ramp(b,24,28))
    center=.48*ramp(b,2,4)*(1-ramp(b,5,9))
    hop=.23*math.sin(math.pi*(b-2)/2)**1.2 if 2<b<4 else 0
    pulse=math.sin(math.pi*(b-14))**2 if 14<b<24 else 0
    z=(-.14-.05*math.sin(math.pi*b)**2-.10*narrow)*env+hop
    ctx['loc'](st,'CTRL.pelvis',(center,-.18*pulse,z))
    yaw=7*math.sin(math.pi*b/2)*env
    if b>=28:yaw=22*math.sin(math.pi*(b-28)/2)*(1-ramp(b,30,32))
    ctx['rot'](st,'CTRL.torso',((3+6*pulse)*env,yaw,-4*math.sin(math.pi*b/2)*env))
    ctx['rot'](st,'CTRL.sensor.yaw',(0,-yaw*.55,0))
    ctx['rot'](st,'CTRL.sensor.pitch',(-3*env-4*pulse,0,0))
    for side,sign in [('L',1),('R',-1)]:
        x=.48*ramp(b,2,4);lift=hop
        if b>=4:
            a,zstep=(7,9) if side=='L' else (5,7)
            x,lift=step(b,a,zstep,.48,0)
        if b>=9:
            a,zstep=(10,12) if side=='L' else (12,14)
            x,lift=step(b,a,zstep,0,-sign*.13,.15)
        if b>=24:
            a,zstep=(24,26) if side=='L' else (26,28)
            x,lift=step(b,a,zstep,-sign*.13,0,.19)
        ctx['loc'](st,'CTRL.foot_IK.'+side,(x,0,lift))
        st['contact'][side]=lift<1e-6;st['lift'][side]=lift
        # Hip swivel draws the knees inward without violating the mechanical hinges.
        ctx['rot'](st,'CTRL.hip_swivel.'+side,(0,-sign*5*narrow,0))
        pod=(-6-8*narrow)*env
        if b>=28:pod=-18*ramp(b,28,29)*(1-ramp(b,30,32))
        ctx['rot'](st,'CTRL.pod_aim.'+side,(pod,0,0))
    ctx['rot'](st,'CTRL.cannon.aim',((-5-8*pulse)*env,0,0))
    ctx['rot'](st,'CTRL.antenna.head',(3*math.sin(math.tau*b)*env,0,0))
    ctx['rot'](st,'CTRL.antenna.hull',(2*math.sin(math.tau*b+.5)*env,0,0))
    return st

digest=bpy.app.driver_namespace['HC terrain revision context']['digest']
bpy.app.driver_namespace['HC time warp protected actions']={a.name:digest(a) for a in bpy.data.actions if a.name.startswith('HC ANIM | ') and a.name!='HC ANIM | '+LABEL}
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
    markers=[(name,round(beat*DURATION/32)+1) for name,beat in [('Prepare',0),('Lateral hop left',2),('Land left',4),('Step right',5),('Gather',9),('Knees inward',10),('Hip pulses',14),('Recover stance',24),('Pod flourish',28),('Ready',32)]]
    for name,f in markers:action.pose_markers.new(name).frame=f
    action['HC animation library']='MECH_2026_09';action['HC dance emote']=True;action['FPS']=24;action['Loop']=True;action['BPM']=BPM
    action['Category']='Emote';action['Root motion']='None';action['Contact samples']=json.dumps(samples)
    action.asset_mark();action.asset_data.description='Time Warp mech adaptation: left hop, right step, inward knees, hip pulses and pod flourish. 32-beat loop; original film reference; approximate tempo.'
finally:
    ctx['reset']();rig.animation_data.action=original[0]
    if original[1]:rig.animation_data.action_slot=original[1]
    scene.frame_set(original[2])
bpy.app.driver_namespace['HC time warp context']={'state':state,'label':LABEL,'duration':DURATION}
row={'label':LABEL,'source_label':LABEL,'action':'HC ANIM | '+LABEL,'slug':'47_time_warp','duration_frames':DURATION,'fps':24,'loop':True,'category':'Emote','gallery_group':'emotes','nominal_speed_units_per_s':0,'bpm':BPM,'preview_frame_step':2,'revision':'Time Warp mech adaptation','timing_note':'32-beat loop at approximately 175 BPM; cue manually to the original film recording. No audio-derived beat alignment or audio included.','markers':[{'name':n,'frame':f} for n,f in markers]}
(Path(PROJECT_ROOT)/'build/time_warp_action.json').write_text(json.dumps(row,indent=2)+'\n')
print(json.dumps({'created':row['action'],'duration_seconds':DURATION/24,'saved':False}))
