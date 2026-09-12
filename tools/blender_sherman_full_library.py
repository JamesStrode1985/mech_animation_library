"""Sherman-specific counterparts to the full Hellcat library. Execute through Blender MCP.
PROJECT_ROOT is required; optional BUILD_NUMBERS selects numbered Actions. Never saves .blend.
"""
import bpy,math,json,ast
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path(PROJECT_ROOT);r=bpy.data.objects['SHERMAN WALKER | ANIMATION RIG'];scene=bpy.context.scene
# Load the approved gait recipe up to (but not including) its Action authoring loop.
recipe=(ROOT/'tools/blender_sherman_locomotion.py').read_text(encoding='utf-8-sig')
exec(compile(recipe[:recipe.index('\ncontrols=')],'approved_sherman_gait','exec'))
gait_pose=pose;gait_configs=configs
base_ctx=ctx
CONTROLS=[p.name for p in r.pose.bones if p.name.startswith('CTRL.')]
MODES={n:('QUATERNION' if n in ['CTRL.root','CTRL.pelvis','CTRL.torso'] or 'foot_IK' in n or 'knee_pole' in n else 'XYZ') for n in CONTROLS}
ROOT_CHILDREN=['CTRL.pelvis','CTRL.foot_IK.L','CTRL.foot_IK.R','CTRL.knee_pole.L','CTRL.knee_pole.R']
source=json.loads((ROOT/'data/manifest.json').read_text(encoding='utf-8'))

# Static rest-coordinate point clouds grouped by rigid binding; used for floor and framing.
if 'SW full library' not in bpy.app.driver_namespace:bpy.app.driver_namespace['SW full library']={}
lib=bpy.app.driver_namespace['SW full library']
if 'cloud' not in lib:
    points={}
    for o in scene.objects:
        if o.type!='MESH' or not o.visible_get():continue
        T=r.matrix_world.inverted()@o.matrix_world
        group_names={g.index:g.name for g in o.vertex_groups}
        for v in o.data.vertices:
            if not v.groups:continue
            g=max(v.groups,key=lambda a:a.weight);n=group_names[g.group]
            if g.weight<.98 or n not in r.data.bones:continue
            p=r.data.bones[n].matrix_local.inverted()@T@v.co
            points.setdefault(n,[]).append((*p,1))
    lib['cloud']={n:np.array(v,dtype=np.float64) for n,v in points.items()}

def envelope(t,keys):
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if t<=b:return x+(y-x)*smooth((t-a)/(b-a))
    return keys[-1][1]

def pulse(t,a,width=7):return math.sin(math.pi*(t-a)/width)**2 if a<t<a+width else 0

def reset():
    for p in r.pose.bones:p.matrix_basis=Matrix.Identity(4)

def ready(drop=.5):
    reset();world_delta('CTRL.pelvis',(0,0,-drop))

def delta(n,v):r.pose.bones[n].location+=r.data.bones[n].matrix_local.to_3x3().inverted()@Vector(v)

def shift(v):
    for n in ROOT_CHILDREN:delta(n,v)

def global_rotate(degrees,axis=(0,0,1),pivot=(0,0,0)):
    bpy.context.view_layer.update();G=Matrix.Translation(pivot)@Quaternion(axis,math.radians(degrees)).to_matrix().to_4x4()@Matrix.Translation(-Vector(pivot))
    targets={n:G@r.pose.bones[n].matrix for n in ROOT_CHILDREN}
    for n,m in targets.items():r.pose.bones[n].matrix=m
    bpy.context.view_layer.update()

def snapshot():return {n:r.pose.bones[n].matrix_basis.copy() for n in CONTROLS}

def blend(a,b,k):
    for n in CONTROLS:
        pa,qa,sa=a[n].decompose();pb,qb,sb=b[n].decompose()
        r.pose.bones[n].matrix_basis=Matrix.LocRotScale(pa.lerp(pb,k),qa.slerp(qb,k),sa.lerp(sb,k))

def recoil(t,shots):
    value=max([pulse(t,a,5) for a in shots]+[0])
    r.pose.bones['CTRL.cannon.recoil'].location.y=-.18*value
    return value

def sole_points(side):
    p=r.pose.bones['DEF.foot.'+side];T=p.matrix@p.bone.matrix_local.inverted()
    return [T@v for v in cloud[side]]

def terrain(spec,x,y,t):
    mode=spec.get('terrain_mode')
    if mode in ['uphill','downhill']:return (-1 if mode=='downhill' else 1)*math.tan(math.radians(22))*(-y)
    if mode=='rough':
        period=spec.get('terrain_period',8)
        q=2*math.pi*(y/period-t/spec['duration_frames'])
        return .42*math.sin(q+.65*x)+.20*math.sin(2*q-.9*x)+.10*math.sin(1.2*x)
    return 0

def correct_feet(spec,t,contact=None):
    # Ensure actual soles, including ankle limits, contact the authored terrain.
    if not spec.get('terrain_mode'):return
    for _ in range(3):
        bpy.context.view_layer.update()
        for s in ['L','R']:
            points=sole_points(s);low=min(v.z-terrain(spec,v.x,v.y,t) for v in points)
            if contact[s]:dz=.062-low
            else:dz=max(0,.11-low)
            delta('CTRL.foot_IK.'+s,(0,0,dz))
    bpy.context.view_layer.update()

def limit_reach():
    bpy.context.view_layer.update();low=-1e6;high=1e6
    for s in ['L','R']:
        H=r.pose.bones['DEF.thigh.'+s].head;B=r.pose.bones['CTRL.foot_IK.'+s].head
        a=r.data.bones['DEF.thigh.'+s].length;b=r.data.bones['DEF.shin.'+s].length
        xy=(H.x-B.x)**2+(H.y-B.y)**2
        minD=math.sqrt(a*a+b*b+2*a*b*math.cos(math.radians(117)))
        low=max(low,B.z+math.sqrt(max(.01,minD*minD-xy))-H.z)
        high=min(high,B.z+math.sqrt(max(.01,(a+b-.03)**2-xy))-H.z)
    change=max(low,min(0,high)) if low<=high else high
    if abs(change)>1e-6:delta('CTRL.pelvis',(0,0,change));bpy.context.view_layer.update()

def world_points():
    return np.concatenate([pts@np.asarray(r.matrix_world@r.pose.bones[n].matrix).T for n,pts in lib['cloud'].items()])[:,:3]

def motion(spec,t):
    n=spec['number'];N=spec['duration_frames'];u=t/N
    contact={'L':True,'R':True};info={}
    if n in [4,5]:
        k=n-4;c=dict(gait_configs[k]);c['stride']*=.72;c['lean']=-2 if k==0 else -4
        gait_pose(c,(-t/c['frames'])%1)
    elif 6<=n<=8:
        c=gait_configs[n-6];start=c['frames'];gait_pose(c,t/c['frames']);a=snapshot();ready();b=snapshot()
        blend(a,b,smooth((t-start)/(N-start-12)))
        delta('CTRL.torso',(0,.10*pulse(t,start,N-start-8),0))
        world_delta('CTRL.torso',angles=(-5*pulse(t,start,N-start-8),0,0))
    elif 9<=n<=12:
        moving=n!=9;k=max(0,n-10);c=gait_configs[k];lead=c['frames'] if moving else 0
        take=lead+(8 if moving else 18);land=take+(32 if n<11 else 28)
        if moving and t<lead:gait_pose(c,t/c['frames'])
        else:
            ready(.55)
            if t<take:
                e=smooth((t-lead)/(take-lead));delta('CTRL.pelvis',(0,-.13*e,-.75*math.sin(math.pi*e)))
                if moving:
                    launch=snapshot();gait_pose(c,0);start_pose=snapshot()
                    for nn,mm in launch.items():r.pose.bones[nn].matrix_basis=mm
                    delta('CTRL.foot_IK.L',(0,-.9,.12*math.sin(math.pi*e)))
                    delta('CTRL.foot_IK.R',(0,.9,0));goal=snapshot();blend(start_pose,goal,e)
            elif t<land:
                p=(t-take)/(land-take);jump=2.3*4*p*(1-p)*(1.15 if n==12 else 1)
                shift((0,0,jump));delta('CTRL.pelvis',(0,0,-.35*math.sin(math.pi*p)))
                for s,sign in [('L',1),('R',-1)]:
                    delta('CTRL.foot_IK.'+s,(0,-sign*.9*math.cos(math.pi*p) if moving else 0,.55*math.sin(math.pi*p)))
                    contact[s]=False
                world_delta('CTRL.torso',angles=((9 if moving else 3)*math.sin(math.pi*p),0,0))
            else:
                recovery=smooth((t-land)/max(1,N-land-8));delta('CTRL.pelvis',(0,0,-.9*pulse(t,land,14)))
                if moving:
                    delta('CTRL.foot_IK.L',(0,.9,0));delta('CTRL.foot_IK.R',(0,-.9,0))
                    a=snapshot();gait_pose(c,(t-land)/c['frames']);b=snapshot();blend(a,b,recovery)
        world_delta('CTRL.arm.upper.L',angles=(-12*math.sin(math.pi*min(1,max(0,(t-lead)/(N-lead)))),0,0))
    elif 13<=n<=16:
        direction=1 if n in [13,15] else -1
        c=dict(gait_configs[0 if n<15 else 1]);c['stride']=1.65 if n<15 else 2.4;c['lift']*=.8
        gait_pose(c,t/N)
        if n<15:
            for s in ['L','R']:
                p=r.pose.bones['CTRL.foot_IK.'+s];v=p.bone.matrix_local.to_3x3()@p.location
                world_delta(p.name,(-direction*v.y,0,v.z))
            world_delta('CTRL.torso',angles=(0,-direction*3,0))
        else:
            yaw=direction*45;global_rotate(yaw)
            world_delta('CTRL.torso',angles=(4,0,-yaw))
            world_delta('CTRL.arm.upper.L',angles=(-82,0,0))
            recoil(t,[8,28]);world_delta('CTRL.roof_gun.traverse',angles=(0,0,8*math.sin(2*math.pi*u)))
    elif 17<=n<=25:
        if n<=19:k=n-17;mode='rough'
        else:k=(n-20)//2;mode='uphill' if n%2==0 else 'downhill'
        c=dict(gait_configs[k]);c['lift']*=.82 if k else 1.25;c['stride']*=.82
        cycles=4 if k==0 and mode=='rough' else 2
        phase=t/N*cycles;gait_pose(c,phase)
        for s in ['L','R']:
            p=r.pose.bones['CTRL.foot_IK.'+s];v=p.bone.matrix_local.to_3x3()@p.location;pos=p.bone.head_local+v
            h=terrain(spec,pos.x,pos.y,t);eps=.01
            gx=(terrain(spec,pos.x+eps,pos.y,t)-terrain(spec,pos.x-eps,pos.y,t))/(2*eps)
            gy=(terrain(spec,pos.x,pos.y+eps,t)-terrain(spec,pos.x,pos.y-eps,t))/(2*eps)
            pitch=max(-24,min(24,math.degrees(math.atan(gy))));roll=max(-12,min(12,-math.degrees(math.atan(gx))))
            world_delta(p.name,(v.x,v.y,v.z+h),(pitch,roll,0));contact[s]=(phase+(0 if s=='L' else .5))%1<c['duty']
        delta('CTRL.pelvis',(0,0,terrain(spec,0,0,t)))
        world_delta('CTRL.torso',angles=(c['lean']+(7 if mode=='uphill' else -7 if mode=='downhill' else 3*math.sin(4*math.pi*u)),0,2*math.sin(2*math.pi*u) if mode=='rough' else 0))
        correct_feet(spec,t,contact)
    elif 26<=n<=38:
        ready();e=envelope(t,[(0,0),(N*.3,1),(N*.65,1),(N,0)])
        if n==26:world_delta('CTRL.torso',angles=(.9*math.sin(2*math.pi*u),0,.5*math.sin(2*math.pi*u)))
        elif n==27:
            world_delta('CTRL.torso',angles=(0,0,22*math.sin(2*math.pi*u)))
            world_delta('CTRL.roof_gun.traverse',angles=(0,0,-16*math.sin(2*math.pi*u)))
        elif n in [28,29]:world_delta('CTRL.torso',angles=(0,0,(30 if n==28 else -30)*e))
        elif n in [30,31]:world_delta('CTRL.torso',angles=((-7 if n==30 else 9)*e,0,0))
        elif n in [32,33]:world_delta('CTRL.torso',angles=(0,(-5 if n==32 else 5)*e,0))
        elif n==34:
            delta('CTRL.pelvis',(0,0,-.55*e));world_delta('CTRL.torso',angles=(7*e,0,0));world_delta('CTRL.arm.upper.L',angles=(-18*e,0,0))
        elif n==35:
            kick=recoil(t,[8]);world_delta('CTRL.torso',angles=(-5*kick,0,-2*kick));delta('CTRL.pelvis',(0,.1*kick,-.12*kick))
        else:
            lift=envelope(t,[(0,0),(20,1),(80,1),(N,0)])
            fine=envelope(t,[(0,0),(20,0),(56,1),(80,1),(N,0)])
            sign=-1 if n==36 else 1
            world_delta('CTRL.torso',angles=(sign*5*lift,0,0))
            world_delta('CTRL.cannon.aim',angles=(sign*20*fine,0,0))
            world_delta('CTRL.arm.upper.L',angles=(-90*lift+sign*18*fine,0,0))
            world_delta('CTRL.roof_gun.elevation',angles=(sign*15*fine,0,0))
            if n==38:
                world_delta('CTRL.torso',angles=(0,0,5*math.sin(2*math.pi*u)))
                world_delta('CTRL.cannon.aim',angles=(-16*fine,0,0))
                world_delta('CTRL.arm.upper.L',angles=(-90*lift+16*fine,0,0))
                world_delta('CTRL.roof_gun.traverse',angles=(0,0,28*fine))
                world_delta('CTRL.roof_gun.elevation',angles=(-8*fine,0,0))
    elif 39<=n<=41:
        ready(.5+.6*smooth(t/30))
        fall=smooth((t-15)/(45 if n==39 else 40 if n==40 else 50))
        axis=(1,0,0) if n!=41 else (0,1,0);angle=(82 if n==39 else -86 if n==40 else 86)*fall
        world_delta('CTRL.torso',angles=(4*math.sin(t*.8)*math.exp(-t/10),0,0))
        world_delta('CTRL.cannon.aim',angles=(-25*fall,0,0));r.pose.bones['CTRL.cannon.recoil'].location.y=-.18*fall
        global_rotate(angle,axis,(0,0,6))
        bpy.context.view_layer.update();minimum=world_points()[:,2].min()/1.1
        shift((0,0,.07-minimum));contact={'L':False,'R':False};info['grounded_body']=True
    elif 42<=n<=45:
        ready();direction=(0,-1) if n==42 else (0,1) if n==43 else (1,0) if n==44 else (-1,0)
        attack=n==42;take=9 if attack else 6;land=14 if attack else 16
        z=envelope(t,[(0,0),(4,-.60),(take,0),(land,-.05),(land+3,-.65),(N,0)])
        delta('CTRL.pelvis',(.3*pulse(t,0,9) if attack else 0,-.2*pulse(t,4,18) if attack else 0,z))
        if take<t<land:shift((0,0,(.38 if attack else .85)*math.sin(math.pi*(t-take)/(land-take))))
        lead='L' if n==44 else 'R'
        for s in ['L','R']:
            release=3 if attack and s==lead else take;end=land if s==lead else land+5
            p=max(0,min(1,(t-release)/(end-release)))
            travel=envelope(t,[(0,0),(release,-.45),(end,.55),(N,0)])
            delta('CTRL.foot_IK.'+s,(direction[0]*travel,direction[1]*travel,.65*math.sin(math.pi*p)))
            contact[s]=not release<t<end
        if attack:
            e=envelope(t,[(0,0),(4,-.15),(9,.55),(14,.75),(18,1),(23,.6),(N,0)])
            world_delta('CTRL.torso',angles=(12*max(0,e),0,44*e));world_delta('CTRL.cannon.aim',angles=(-20*max(0,e),0,0))
            world_delta('CTRL.arm.upper.L',angles=(-12*max(0,e),0,0))
        else:world_delta('CTRL.torso',angles=(-direction[1]*9*pulse(t,0,N),-direction[0]*7*pulse(t,0,N),0))
    elif n in [46,47]:
        ready();beat=t*(16 if n==46 else 32)/N;env=smooth(beat)*(1-smooth((beat-(14 if n==46 else 30))/2))
        if n==46:
            section=int(beat//4);groove=math.sin(math.pi*beat)
            delta('CTRL.pelvis',(.3*math.sin(math.pi*beat/2)*env,0,-.18*groove*groove*env))
            world_delta('CTRL.torso',angles=(2*groove*env,3*math.sin(math.pi*beat/2)*env,12*math.sin(math.pi*beat/2)*env))
            for s,off in [('L',0),('R',1)]:
                step=max(0,math.sin(math.pi*(beat+off)));delta('CTRL.foot_IK.'+s,((.35 if section==1 else 0)*groove*env,0,.30*step*env))
            world_delta('CTRL.arm.upper.L',angles=((-12 if section<3 else -65)*env,0,0))
            world_delta('CTRL.roof_gun.traverse',angles=(0,0,20*math.sin(math.pi*beat/2)*env))
        else:
            def ramp(a,b):return smooth((beat-a)/(b-a))
            narrow=ramp(10,14)*(1-ramp(24,28));center=.65*ramp(2,4)*(1-ramp(5,9))
            hop=.65*math.sin(math.pi*(beat-2)/2)**1.2 if 2<beat<4 else 0
            pulsehip=math.sin(math.pi*(beat-14))**2 if 14<beat<24 else 0
            delta('CTRL.pelvis',(center,-.22*pulsehip,-.25*narrow-.09*math.sin(math.pi*beat)**2*env))
            shift((0,0,hop));world_delta('CTRL.torso',angles=(5*pulsehip,0,8*math.sin(math.pi*beat/2)*env))
            for s,sign in [('L',1),('R',-1)]:
                x=center-sign*.24*narrow;lift=0
                if 5<beat<9:
                    a=7 if s=='L' else 5;p=max(0,min(1,(beat-a)/2));x=.65*(1-smooth(p));lift=.35*math.sin(math.pi*p)
                delta('CTRL.foot_IK.'+s,(x,0,lift))
                delta('CTRL.knee_pole.'+s,(-sign*.55*narrow,0,0))
            flourish=ramp(28,29)*(1-ramp(30,32));world_delta('CTRL.arm.upper.L',angles=(-55*flourish,0,0));world_delta('CTRL.roof_gun.traverse',angles=(0,0,20*flourish))
    else:raise ValueError(n)
    if not 39<=n<=41:limit_reach()
    if spec.get('terrain_mode'):
        for _ in range(2):
            correct_feet(spec,t,contact);limit_reach()
        correct_feet(spec,t,contact)
    bpy.context.view_layer.update()
    return {'contact':contact,**info}

specs=[]
for original in source['clips'][3:]:
    spec=dict(original);n=int(spec['label'].split()[0]);spec['number']=n;spec['action']='SW ANIM | '+spec['label'];spec['source_label']=spec['label'];spec['hellcat_source_action']=original['action']
    spec['revision']='Sherman full library 2';spec['preview_frame_step']=2;spec['controller_preview_travel']=False
    # Slower cadence for the heavier asymmetric model; match semantic events to its own cycle.
    if n==5:spec['duration_frames']=32
    if n in [7,8]:spec['duration_frames']=80 if n==7 else 72
    if n in [10,11,12]:spec['duration_frames']=[132,112,96][n-10]
    if 17<=n<=25:
        k=n-17 if n<=19 else (n-20)//2
        spec['terrain_mode']='rough' if n<=19 else 'uphill' if n%2==0 else 'downhill'
        spec['duration_frames']=gait_configs[k]['frames']*(4 if n==17 else 2)
        spec['terrain_period']=gait_configs[k]['stride']*.82/gait_configs[k]['duty']*(4 if n==17 else 2)
        spec['nominal_speed_units_per_s']=spec['terrain_period']*1.1/(spec['duration_frames']/24)
    if 9<=n<=12:
        lead=0 if n==9 else gait_configs[n-10]['frames'];take=lead+(18 if n==9 else 8);land=take+(32 if n<11 else 28)
        spec['markers']=[dict(name='Drive' if n>9 else 'Load',frame=lead+1),dict(name='Takeoff',frame=take+1),dict(name='Apex',frame=(take+land)//2+1),dict(name='Land R' if n>9 else 'Land',frame=land+1),dict(name='Resume gait' if n>9 else 'Ready',frame=spec['duration_frames']+1)]
    if 6<=n<=8:
        spec['markers']=[dict(name='Begin braking',frame=gait_configs[n-6]['frames']+1),dict(name='Feet settled',frame=spec['duration_frames']-11)]
    if n in [4,5]:
        c=gait_configs[n-4];spec['nominal_speed_units_per_s']=-c['stride']*.72*1.1/(c['duty']*c['frames']/24)
    if 13<=n<=16:
        c=gait_configs[0 if n<15 else 1];spec['nominal_speed_units_per_s']=(1.65 if n<15 else 2.4)*1.1/(c['duty']*spec['duration_frames']/24)
    if n in [15,16]:spec['markers']=[dict(name='Cannon fire',frame=9),dict(name='Cannon fire 2',frame=29)]
    if 6<=n<=12:
        k=n-6 if n<=8 else max(0,n-10);c=gait_configs[k];spec['nominal_speed_units_per_s']=0 if n==9 else c['stride']*1.1/(c['duty']*c['frames']/24)
    if 39<=n<=41:
        impact={39:61,40:56,41:66}[n];spec['markers']=[dict(name='Fatal hit',frame=1),dict(name='Loss of balance',frame=16),dict(name='Ground impact',frame=impact),dict(name='Settled',frame=impact+14)]
    if n in [36,37]:
        spec['markers']=[dict(name='Hull aim hold',frame=21),dict(name='Weapon elevation hold',frame=57),dict(name='Begin return to neutral',frame=81)]
    if 42<=n<=45:
        take=10 if n==42 else 7;land=15 if n==42 else 17
        spec['markers']=[dict(name='Anticipation',frame=1),dict(name='Takeoff',frame=take),dict(name='Lead foot landing',frame=land),dict(name='Trailing foot landing',frame=land+5),dict(name='Ready',frame=31)]
        if n==42:spec['markers'] += [dict(name='Left leg drive',frame=5),dict(name='Right foot plant / attack starts',frame=15),dict(name='Shoulder follow through',frame=19),dict(name='Attack ends',frame=21)]
    if n==47:
        spec['timing_note']='Same 32-beat choreography and approximate 175 BPM as the Hellcat gallery clip; no song audio or soundtrack alignment is included.'
        spec['markers']=[dict(m,name='Weapon flourish' if m['name']=='Pod flourish' else m['name']) for m in spec['markers']]
    specs.append(spec)
lib.update(specs=specs,motion=motion,world_points=world_points,terrain=terrain,controls=CONTROLS,modes=MODES)
selected=set(globals().get('BUILD_NUMBERS') or range(4,48))
for spec in specs:
    if spec['number'] not in selected:continue
    name=spec['action'];frames=list(globals().get('BUILD_FRAMES',range(1,spec['duration_frames']+2)))
    if frames[0]==1:
        prior=bpy.data.actions.get(name)
        if prior:prior.name=name+' | previous';prior.use_fake_user=True
        action=bpy.data.actions.new(name);action.use_fake_user=True
    else:action=bpy.data.actions[name]
    r.animation_data.action=action
    for f in frames:
        motion(spec,f-1)
        for n in CONTROLS:
            p=r.pose.bones[n];m=p.matrix_basis.copy();p.rotation_mode=MODES[n];p.matrix_basis=m
            p.keyframe_insert('location',frame=f,group=n)
            p.keyframe_insert('rotation_quaternion' if MODES[n]=='QUATERNION' else 'rotation_euler',frame=f,group=n)
    for l in action.layers:
        for strip in l.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:key.interpolation='LINEAR'
    for marker in list(action.pose_markers):action.pose_markers.remove(marker)
    for marker in spec['markers']:action.pose_markers.new(marker['name']).frame=marker['frame']
    action['Root motion']='In-place. Root control remains identity; controller supplies travel.';action['FPS']=24;action['Loop']=spec['loop'];action['Sherman library']=True
    action.asset_mark();action.asset_data.description=spec['label']+' adapted for Sherman Walker. Straight left arm; native articulated ammunition feed.'
    print('Created '+name)
(ROOT/'build/sherman_full').mkdir(parents=True,exist_ok=True)
(ROOT/'build/sherman_full/specs.json').write_text(json.dumps(specs,indent=2),encoding='utf-8')
print('Authored requested Sherman Actions; .blend remains unsaved.')
