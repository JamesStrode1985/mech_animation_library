"""Create four quick in-place dodge leaps in the live HELLCAT rig.
Supply PROJECT_ROOT through Blender MCP. Requires the existing animation context.
Does not save the Blender file.
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector

rig=bpy.data.objects['HELLCAT | CURRENT MECH RIG'];scene=bpy.context.scene
ctx=bpy.app.driver_namespace['HC animation build context']
original=(rig.animation_data.action,rig.animation_data.action_slot,scene.frame_current)
CONFIG=[
    dict(label='42 Dodge Forward',direction=(0,-1,0),lead='R',distance=2.35,height=.12,lean=13,attack=True),
    dict(label='43 Dodge Backward',direction=(0,1,0),lead='R',distance=1.90,height=.38,lean=-10),
    dict(label='44 Dodge Left',direction=(1,0,0),lead='L',distance=2.10,height=.42,lean=0),
    dict(label='45 Dodge Right',direction=(-1,0,0),lead='R',distance=2.10,height=.42,lean=0),
]
for c in CONFIG:
    c.update(duration=30,takeoff=6,land=16,brake_end=22,lead_release=5,trail_land=18)
    if c.get('attack'):c.update(takeoff=9,land=14,brake_end=24,lead_release=3,trail_land=20)

def smooth(v):
    v=max(0,min(1,v));return v*v*(3-2*v)

def distance(c,t):
    if c.get('attack'):
        if t<=3:return 0.0
        if t<=9:return .45*((t-3)/6)**2
        if t<=14:return .45+1.10*(t-9)/5
        if t<=24:
            u=(t-14)/10;return 1.55+.80*(2*u-u*u)
        return c['distance']
    if t<=4:return 0.0
    if t<=6:return .10*((t-4)/2)**2
    if t<=16:return .10+(c['distance']*.82-.10)*(t-6)/10
    if t<=22:
        u=(t-16)/6;return c['distance']*(.82+.18*(2*u-u*u))
    return c['distance']

def height(c,t):
    if not c['takeoff']<t<c['land']:return 0.0
    p=(t-c['takeoff'])/(c['land']-c['takeoff']);return c['height']*4*p*(1-p)

def envelope(t,keys):
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if t<=b:return x+(y-x)*smooth((t-a)/(b-a))
    return keys[-1][1]

def state(c,t):
    st=ctx['state']();d=Vector(c['direction']);lead=c['lead']
    if t<=4:
        load=smooth(t/4);pelvis=-.24*load;commit=load*.5
    elif t<=6:
        u=(t-4)/2;pelvis=-.24+.28*smooth(u);commit=.5+.5*u
    elif t<16:
        p=(t-6)/10;pelvis=.04-.11*math.sin(math.pi*p);commit=1-.28*p
    elif t<=19:
        u=(t-16)/3;pelvis=-.32*smooth(u);commit=.72*(1-u)-.25*u
    else:
        recovery=smooth((t-19)/11);pelvis=-.32*(1-recovery);commit=-.25*(1-recovery)
    offset=d*(.085*commit);offset.z=pelvis
    ctx['loc'](st,'CTRL.pelvis',offset)
    ctx['rot'](st,'CTRL.torso',(c['lean']*commit,0,-d.x*7.0*commit))
    ctx['rot'](st,'CTRL.sensor.pitch',(-c['lean']*.35*commit,0,0))
    for n in ['CTRL.cannon.aim','CTRL.pod_aim.L','CTRL.pod_aim.R']:
        ctx['rot'](st,n,(-c['lean']*.45*commit,0,0))
    if c.get('attack'):
        # Positive torso yaw brings the mech's right (-X) shoulder forward (-Y).
        # Wind up, present the armored shoulder, absorb the hit, then unwind.
        # Load the left leg while the right steps out; extend left into the
        # launch, catch on right, then drive the shoulder through that contact.
        pelvis=envelope(t,[(0,0),(4,-.24),(9,-.04),(13,-.10),(15,-.27),(18,-.17),(23,-.13),(30,0)])
        shift=envelope(t,[(0,0),(4,.17),(8,.13),(12,-.03),(15,-.17),(19,-.11),(25,-.04),(30,0)])
        drive=envelope(t,[(0,0),(5,.04),(9,.13),(14,.13),(17,.24),(21,.12),(30,0)])
        ctx['loc'](st,'CTRL.pelvis',(shift,-drive,pelvis))
        yaw=envelope(t,[(0,0),(4,-8),(9,45),(14,56),(17,78),(19,76),(24,38),(30,0)])
        pitch=envelope(t,[(0,0),(4,6),(9,11),(14,10),(17,17),(20,9),(24,-2),(30,0)])
        lean=envelope(t,[(0,0),(5,-2),(10,2),(14,3),(17,6),(21,3),(30,0)])
        ctx['rot'](st,'CTRL.torso',(pitch,yaw,lean))
        tuck=envelope(t,[(0,0),(8,1),(19,1),(24,.5),(30,0)])
        ctx['rot'](st,'CTRL.cannon.aim',(-20*tuck,0,0))
        ctx['rot'](st,'CTRL.pod_aim.R',(-20*tuck,0,0))
        ctx['rot'](st,'CTRL.pod_aim.L',(-12*tuck,0,0))
        ctx['rot'](st,'CTRL.sensor.pitch',(-pitch*.45,0,0))
    for side in ['L','R']:
        release=c['lead_release'] if side==lead else c['takeoff'];land=c['land'] if side==lead else c['trail_land']
        if t<=release:
            v=-d*distance(c,t);pitch=(9 if d.y<0 else -6 if d.y>0 else 0)*smooth((t-3)/3)
            contact=True
            if c.get('attack'):pitch=0  # Keep the driving sole planted until push-off.
        elif t<land:
            p=(t-release)/(land-release)
            start=-distance(c,release);end=c['distance']-distance(c,land)
            v=d*(start+(end-start)*smooth(p))
            v.z=(.25 if side==lead else .36)*math.sin(math.pi*p)**1.2
            if d.x:v.z*=.85
            pitch=(-10 if d.y<0 else 8 if d.y>0 else 0)*math.sin(math.pi*p)
            contact=False
        else:
            v=d*(c['distance']-distance(c,t));pitch=0;contact=True
        ctx['loc'](st,'CTRL.foot_IK.'+side,v)
        ctx['rot'](st,'CTRL.ankle_tilt.'+side,(pitch,0,0))
        ctx['rot'](st,'CTRL.hock_angle.'+side,(-3*max(commit,0),0,0))
        st['contact'][side]=contact;st['lift'][side]=max(0,v.z)
    impact=17 if c.get('attack') else 16
    shake=math.exp(-max(0,t-impact)/4)*math.sin(max(0,t-impact)*1.2)*(1-smooth((t-24)/6)) if t>=impact else 0
    ctx['rot'](st,'CTRL.antenna.head',(2*shake,0,0))
    st['preview_z']=height(c,t)
    return st

selected=set(globals().get('DODGE_BUILD_LABELS') or [c['label'] for c in CONFIG])
rows=[r for r in bpy.app.driver_namespace.get('HC dodge context',{}).get('rows',[]) if r['source_label'] not in selected]
try:
    for c in CONFIG:
        if c['label'] not in selected:continue
        name='HC ANIM | '+c['label'];prior=bpy.data.actions.get(name)
        if prior:
            assert prior.get('HC dodge animation')
            prior.name='HC ARCHIVE | '+c['label']+' | previous dodge pass';prior.use_fake_user=True;prior.asset_clear()
        action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data.action=action
        samples=[]
        for f in range(1,c['duration']+2):
            scene.frame_set(f);st=state(c,f-1);ctx['apply'](st)
            for n in ctx['controls']:
                p=rig.pose.bones[n]
                if n in ctx['FX']:p.keyframe_insert(data_path='scale',frame=f,group='Optional weapon FX')
                else:
                    p.keyframe_insert(data_path='location',frame=f,group=n)
                    p.keyframe_insert(data_path='rotation_euler',frame=f,group=n)
            delta=Vector(c['direction'])*distance(c,f-1);delta.z=height(c,f-1)
            samples.append({'frame':f,'time_seconds':(f-1)/24,'translation':list(delta),'contacts':st['contact']})
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for key in fc.keyframe_points:key.interpolation='LINEAR'
        for label,f in [('Anticipation',1),('Takeoff',c['takeoff']+1),('Apex',round((c['takeoff']+c['land'])/2)+1),('Lead foot landing',c['land']+1),('Trailing foot landing',c['trail_land']+1),('Braking complete',c['brake_end']+1),('Ready',31)]:
            action.pose_markers.new(label).frame=f
        if c.get('attack'):
            for label,f in [('Left leg drive',5),('Right foot plant',15),('Attack active start',15),('Right shoulder impact',18),('Attack active end',20)]:
                action.pose_markers.new(label).frame=f
        action['HC animation library']='MECH_2026_09';action['HC dodge animation']=True;action['FPS']=24;action['Loop']=False;action['Category']='Dodge'
        action['Root motion']='None. Apply per-frame controller translation samples externally.'
        action['Controller trajectory']=json.dumps(samples)
        action['Gameplay']='Author stamina, invulnerability, interruption and recovery cancel windows in the game controller; no damage logic is encoded in this Action.'
        action.asset_mark();action.asset_data.description='Quick directional dodge leap; 24 fps; anticipation, flight, staggered landing and braking; in-place root.'
        rows.append({'label':c['label'],'source_label':c['label'],'action':name,'duration_frames':30,'fps':24,'loop':False,'category':'Dodge','nominal_speed_units_per_s':c['distance']/(30/24),'slug':c['label'].lower().replace(' ','_'),'markers':[{'name':m.name,'frame':m.frame} for m in action.pose_markers],'revision':'Four quick directional dodge leaps','preview_frame_step':1,'controller_preview_travel':True,'gallery_group':'dodges','controller_distance_units':c['distance'],'controller_peak_height_units':c['height'],'controller_samples':samples})
        if c.get('attack'):
            action['Category']='Attack';action['Attack active frames']=[15,20];action['Impact frame']=18
            action.asset_data.description='Right-shoulder ram: left-leg push-off, right-foot catch and planted shoulder follow-through. In-place, 24 fps.'
            rows[-1].update(label='42 Forward Shoulder Ram',category='Attack',revision='Single-leg drive and planted follow-through',attack={'side':'right','drive_leg':'left','catch_leg':'right','catch_frame':15,'active_frames':[15,20],'impact_frame':18,'combat_logic':'Animation timing only; author hitboxes, damage and interruption in the game controller.'})
finally:
    ctx['reset']();rig.animation_data.action=original[0]
    if original[1]:rig.animation_data.action_slot=original[1]
    scene.frame_set(original[2])
rows.sort(key=lambda r:int(r['label'].split()[0]))
bpy.app.driver_namespace['HC dodge context']={'config':CONFIG,'state':state,'distance':distance,'height':height,'rows':rows}
out=Path(PROJECT_ROOT)/'build';out.mkdir(exist_ok=True);(out/'dodge_actions.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps({'created':['HC ANIM | '+label for label in sorted(selected)],'frames_per_action':31,'duration_seconds':1.25,'flight_seconds':{c['label']:(c['land']-c['takeoff'])/24 for c in CONFIG if c['label'] in selected},'saved':False}))
