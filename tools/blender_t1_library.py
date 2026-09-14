"""T1-specific 47-action quadruped library. Run through Blender MCP with PROJECT_ROOT.
No source-model save. All gameplay Actions retain an identity root.
"""
import bpy,math,json
from pathlib import Path
from mathutils import Vector,Matrix,Euler
import numpy as np
ROOT=Path(PROJECT_ROOT);r=bpy.data.objects['T1 | ANIMATION RIG'];scene=bpy.context.scene
source=json.loads((ROOT/'data/manifest.json').read_text())
LEGS=['front.L','front.R','rear.L','rear.R']
CONTROL=['CTRL.root','CTRL.body','CTRL.turret','CTRL.cannon.aim','CTRL.cannon.recoil','CTRL.roof_turret.yaw','CTRL.roof_turret.elevation','CTRL.roof_turret.recoil.L','CTRL.roof_turret.recoil.R']+[f'CTRL.canine.{part}.{s}' for s in LEGS for part in ['paw','hock','pole','toes']]
for n in CONTROL:r.pose.bones[n].rotation_mode='QUATERNION'
for limit in r.pose.bones['CTRL.cannon.recoil'].constraints:
 if limit.type=='LIMIT_LOCATION':
  limit.min_y=-.90;limit.name='Recoil stroke 0 to 0.90 m'
if r.animation_data.action:r.animation_data.action.use_fake_user=True
r.animation_data.action=None
for p in r.pose.bones:
 if p.name.startswith('CTRL'):p.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
BASIS={n:r.data.bones[n].matrix_local.to_3x3() for n in CONTROL}
sole={s:[] for s in LEGS};cloud={}
for o in scene.objects:
 if o.type!='MESH' or not o.visible_get() or not any(m.type=='ARMATURE' and m.object==r for m in o.modifiers):continue
 T=r.matrix_world.inverted()@o.matrix_world;names={g.index:g.name for g in o.vertex_groups}
 for vert in o.data.vertices:
  if len(vert.groups)!=1 or vert.groups[0].weight<.99:continue
  n=names[vert.groups[0].group]
  if n not in r.data.bones:continue
  p=r.data.bones[n].matrix_local.inverted()@T@vert.co
  if vert.index%6==0:cloud.setdefault(n,[]).append((*p,1))
  for s in LEGS:
   if n in ['DEF.canine.paw.'+s,'CTRL.canine.toes.'+s]:sole[s].append((n,p))
cloud={n:np.asarray(v) for n,v in cloud.items()}
# Sole samples are vertices at the lowest rest elevation on each rigid component.
for s in LEGS:
 low=min((r.data.bones[n].matrix_local@p).z for n,p in sole[s])
 sole[s]=[(n,p) for n,p in sole[s] if (r.data.bones[n].matrix_local@p).z<low+.08]
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def env(t,keys):
 for (a,x),(b,y) in zip(keys,keys[1:]):
  if t<=b:return x+(y-x)*smooth((t-a)/(b-a))
 return keys[-1][1]
def pulse(t,a,w):return math.sin(math.pi*(t-a)/w)**2 if a<t<a+w else 0
def setctrl(n,v=(0,0,0),rot=(0,0,0)):
 p=r.pose.bones[n];B=BASIS[n];p.location=B.inverted()@Vector(v);p.rotation_quaternion=(B.inverted()@Euler(tuple(math.radians(a) for a in rot),'XYZ').to_matrix()@B).to_quaternion()
def delta(n,v):r.pose.bones[n].location+=BASIS[n].inverted()@Vector(v)
def terrain(spec,x,y,t):
 mode=spec.get('terrain_mode')
 if mode in ['uphill','downhill']:return (-1 if mode=='downhill' else 1)*math.tan(math.radians(22))*(-y)
 if mode=='rough':
  a=math.tau*(y/spec['terrain_period']-t/spec['duration_frames'])
  return .48*math.sin(a+.5*x)+.19*math.sin(2*a-.8*x)+.10*math.sin(1.1*x)
 return 0
def world_cloud():return np.concatenate([pts@np.asarray(r.matrix_world@r.pose.bones[n].matrix).T for n,pts in cloud.items()])[:,:3]
GAITS=[dict(N=64,stride=1.9,lift=.40,duty=.78,offset=[0,.5,.75,.25]),dict(N=40,stride=2.4,lift=.64,duty=.53,offset=[0,.5,.5,0]),dict(N=32,stride=2.7,lift=.83,duty=.38,offset=[.08,.20,.57,.69])]
def state():return dict(body=Vector((0,0,-.16)),angles=[0,0,0],hull=[0,0,0],feet={s:Vector((0,0,0)) for s in LEGS},tilt={s:[0,0,0] for s in LEGS},contact={s:True for s in LEGS},main=0,roof_yaw=0,roof_pitch=12,recoil=0,shot=0,death=0)
def gait(k,t,reverse=False):
 st=state();c=GAITS[k];phase=t/c['N'];cphase=phase%1
 for s,off in zip(LEGS,c['offset']):
  u=(phase+off)%1
  if u<c['duty']:y=c['stride']*(-.5+u/c['duty']);z=0
  else:
   q=(u-c['duty'])/(1-c['duty']);y=c['stride']*(.5-smooth(q));z=c['lift']*math.sin(math.pi*q)**1.35;st['contact'][s]=False
  st['feet'][s]=Vector((0,-y if reverse else y,z))
 st['body'].z+=(-.055 if k==0 else -.16 if k==1 else -.25)*math.cos(4*math.pi*cphase)
 st['angles']=[(1 if reverse else -1)*(1.5+1.3*k)+(.6 if k==0 else 1.6)*math.sin(math.tau*cphase),(.6 if k==0 else 1.0)*math.sin(math.tau*cphase),.5*math.sin(math.tau*cphase)]
 return st
def blend(a,b,w):
 for key in ['body']:a[key]=a[key].lerp(b[key],w)
 for key in ['angles','hull']:a[key]=[(1-w)*x+w*y for x,y in zip(a[key],b[key])]
 for s in LEGS:
  a['feet'][s]=a['feet'][s].lerp(b['feet'][s],w);a['tilt'][s]=[(1-w)*x+w*y for x,y in zip(a['tilt'][s],b['tilt'][s])]
  a['contact'][s]=a['contact'][s] if w<.5 else b['contact'][s]
 return a
def motion(spec,t):
 n=spec['number'];N=spec['duration_frames'];u=t/N;st=state();e=env(u,[(0,0),(.3,1),(.65,1),(1,0)])
 if n in [1,2,3,4,5]:st=gait(n-1 if n<=3 else n-4,t,n>3)
 elif 6<=n<=8:
  k=n-6;lead=GAITS[k]['N'];st=blend(gait(k,min(t,lead)+(max(0,t-lead)*.4)),state(),smooth((t-lead)/(N-lead-8)));st['angles'][0]-=4*pulse(t,lead,N-lead)
 elif 9<=n<=12:
  k=max(0,n-10);lead=0 if n==9 else GAITS[k]['N'];take=lead+16;land=take+28
  if t<lead:st=gait(k,t)
  elif t<take:
   q=(t-lead)/16;st=blend(gait(k,lead),state(),smooth(q)) if n>9 else state();st['body'].z-=.70*math.sin(math.pi*q)
   st['angles'][0]=-7*math.sin(math.pi*q)
   if n>9:
    for s in LEGS:st['feet'][s].y+=(-.35 if s.startswith('front') else .30)*math.sin(math.pi*q)
  elif t<land:
   q=(t-take)/(land-take);height=(1.65 if n==9 else 1.85+k*.22)*4*q*(1-q);st['body'].z+=height;st['angles'][0]=(-8 if n>9 else -3)*math.sin(math.tau*q)
   for s in LEGS:
    front=s.startswith('front');st['feet'][s]=Vector((0,(.6 if front else -.6)*math.sin(math.pi*q),height+.4*math.sin(math.pi*q)));st['contact'][s]=False
  else:
   st['body'].z-=.75*pulse(t,land,18)
   if n>9:st=blend(st,gait(k,t-land),smooth((t-land-12)/(N-land-12)))
 elif 13<=n<=16:
  side=1 if n in [13,15] else -1;st=gait(0 if n<15 else 1,t)
  if n<15:
   for s in LEGS:st['feet'][s].x=-side*st['feet'][s].y*.65;st['feet'][s].y=0
   st['angles'][1]=-side*2
  else:
   st['hull'][2]=side*42;st['roof_yaw']=-side*25;st['roof_pitch']=8;st['shot']=max(pulse(t,a,5) for a in range(3,N,10))
 elif 17<=n<=25:
  k=n-17 if n<=19 else (n-20)//2;st=gait(k,t)
  for s in LEGS:
   pos=r.data.bones['CTRL.canine.paw.'+s].head_local+st['feet'][s];st['feet'][s].z+=terrain(spec,pos.x,pos.y,t)
   gy=(terrain(spec,pos.x,pos.y+.02,t)-terrain(spec,pos.x,pos.y-.02,t))/.04;gx=(terrain(spec,pos.x+.02,pos.y,t)-terrain(spec,pos.x-.02,pos.y,t))/.04
   st['tilt'][s]=[max(-24,min(24,math.degrees(math.atan(gy)))),max(-12,min(12,-math.degrees(math.atan(gx)))),0]
  if spec['terrain_mode']=='rough':st['body'].z+=terrain(spec,0,0,t)*.40;st['angles'][0]+=2*math.sin(math.tau*u);st['angles'][1]+=2*math.sin(2*math.tau*u)
  else:st['angles'][0]=(-22 if spec['terrain_mode']=='uphill' else 22);st['body'].z+=.3
 elif 26<=n<=38:
  if n==26:st['hull'][0]=.65*math.sin(math.tau*u);st['roof_yaw']=3*math.sin(math.tau*u)
  elif n==27:st['hull'][2]=26*math.sin(math.tau*u);st['roof_yaw']=-38*math.sin(math.tau*u)
  elif n in [28,29]:st['hull'][2]=(40 if n==28 else -40)*e
  elif n in [30,31]:st['hull'][0]=(-9 if n==30 else 9)*e
  elif n in [32,33]:st['angles'][1]=(-7 if n==32 else 7)*e
  elif n==34:
   st['body'].z-=.7*e
   for s in LEGS:st['feet'][s].x=(.35 if s.endswith('L') else -.35)*e;st['feet'][s].y=(-.25 if s.startswith('front') else .25)*e
  elif n==35:
   # Fast barrel recoil leads the hull response; recuperator returns slowly.
   barrel=env(t,[(0,0),(9,0),(11,1),(15,.90),(31,0),(N,0)])
   shove=env(t,[(0,0),(11,0),(17,1),(22,.70),(36,0),(N,0)])
   compress=env(t,[(0,0),(13,0),(20,1),(27,.45),(38,0),(N,0)])
   st['recoil']=3.3*barrel;st['hull'][0]=-5.5*shove
   st['body'].y=.48*shove;st['body'].z-=.42*compress
   st['angles'][0]=-2.5*shove
  else:
   hull=env(u,[(0,0),(.2,1),(.72,1),(1,0)]);fine=env(u,[(0,0),(.2,0),(.52,1),(.72,1),(1,0)])
   st['hull'][0]=(-7 if n!=37 else 7)*hull;st['main']=(35 if n!=37 else -10)*fine;st['roof_pitch']=12+(65 if n!=37 else -20)*fine
   if n==38:st['main']=22*fine;st['roof_yaw']=120*math.sin(math.tau*u)*fine;st['hull'][2]=-15*e;st['shot']=pulse(t,60,10)
 elif 39<=n<=41:
  # Legs lose support first. Feet stay down while the hull sinks between them.
  first=smooth((t-10)/22);second=smooth((t-30)/25);settle=smooth((t-56)/18)
  st['body'].z-=.82*first+1.12*second-.08*settle
  if n in [39,40]:
   sign=1 if n==39 else -1
   st['angles'][0]=sign*(10*first-3*second)
   st['body'].y=-sign*.30*second
  else:
   st['angles'][1]=5*first-3*second
   st['angles'][0]=4*second
   st['body'].x=.22*first
  st['hull'][0]=1.5*math.sin((t-55)*.4)*math.exp(-max(0,t-55)/8)*second if t>55 else 0
  st['main']=-4*second;st['roof_pitch']=12-17*second
  for s in LEGS:
   front=s.startswith('front');early=(front if n==39 else not front if n==40 else s.endswith('L'))
   loss=first if early else second
   st['feet'][s].x=(.38 if s.endswith('L') else -.38)*loss
   st['feet'][s].y=(-.45 if front else .45)*loss
 elif 42<=n<=45:
  take=10;land=29;direction={42:(0,-1),43:(0,1),44:(1,0),45:(-1,0)}[n]
  air=math.sin(math.pi*(t-take)/(land-take)) if take<t<land else 0
  st['body'].z+=1.25*air-.6*pulse(t,0,take)-.7*pulse(t,land,12)
  for s in LEGS:
   front=s.startswith('front');lead=front if n in [42,43] else s.endswith('L') if n==44 else s.endswith('R')
   offset=.35*math.sin(math.pi*max(0,min(1,(t-(take-3 if lead else take))/(land-take+3))))
   st['feet'][s]=Vector((direction[0]*offset,direction[1]*offset,1.25*air+.35*air));st['contact'][s]=not take<t<land
  st['angles'][0]=-direction[1]*5*air;st['angles'][1]=-direction[0]*5*air
  if n==42:
   st['hull'][2]=22*env(u,[(0,0),(.25,-.25),(.58,.5),(.72,1),(1,0)]);st['main']=8*air
 elif n==46:
  beats=16;beat=u*beats;w=smooth(beat)*(1-smooth((beat-(beats-2))/2))
  st['body'].z-=.16*math.sin(math.pi*beat)**2*w;st['body'].x=.22*math.sin(math.pi*beat/2)*w;st['hull'][2]=13*math.sin(math.pi*beat/2)*w;st['hull'][0]=2*math.sin(math.pi*beat)*w;st['roof_yaw']=35*math.sin(math.pi*beat/2)*w
  for j,s in enumerate(LEGS):st['feet'][s].z=.34*max(0,math.sin(math.pi*(beat+j*.5)))*w;st['contact'][s]=st['feet'][s].z<.02
 elif n==47:
  beat=u*32
  # A separate phrase, rather than overlaying a hop on Dance Party's groove.
  x=env(beat,[(0,0),(2,0),(4,.85),(6,.85),(8,0),(32,0)])
  y=env(beat,[(0,0),(4,0),(6,.75),(8,0),(32,0)])
  hop=sum(.65*math.sin(math.pi*(beat-a)/2) if a<beat<a+2 else 0 for a in [2,4,6,26,28])
  squat=env(beat,[(0,0),(8,0),(10,1),(12,1),(14,.4),(24,.4),(26,0),(32,0)])
  wide=env(beat,[(0,0),(8,0),(10,1),(24,1),(26,0),(32,0)])
  thrust=math.sin(math.pi*(beat-14))**2 if 14<beat<24 else 0
  st['body']=Vector((x,y-.50*thrust,-.16+hop-.68*squat))
  st['hull'][0]=8*thrust;st['hull'][2]=0
  st['roof_yaw']=0;st['roof_pitch']=12
  for s in LEGS:
   st['feet'][s]=Vector((x+(.42 if s.endswith('L') else -.42)*wide,y,hop))
   st['contact'][s]=hop<.001
 return st
def apply(spec,t,correct=True):
 for n in CONTROL:r.pose.bones[n].matrix_basis=Matrix.Identity(4)
 st=motion(spec,t);setctrl('CTRL.body',st['body'],st['angles']);setctrl('CTRL.turret',rot=st['hull'])
 for s in LEGS:setctrl('CTRL.canine.paw.'+s,st['feet'][s],st['tilt'][s])
 # Main gun X points right, roof elevation X points left: opposite signs.
 r.pose.bones['CTRL.cannon.aim'].rotation_quaternion=Euler((math.radians(-st['main']),0,0)).to_quaternion()
 r.pose.bones['CTRL.cannon.recoil'].location.y=-.27*st['recoil']
 r.pose.bones['CTRL.roof_turret.yaw'].rotation_quaternion=Euler((0,math.radians(st['roof_yaw']),0)).to_quaternion()
 r.pose.bones['CTRL.roof_turret.elevation'].rotation_quaternion=Euler((math.radians(st['roof_pitch']),0,0)).to_quaternion()
 for s in ['L','R']:r.pose.bones['CTRL.roof_turret.recoil.'+s].location.y=-.085*st['shot']
 if correct:
  for _ in range(5 if spec.get('terrain_mode') else 2):
   bpy.context.view_layer.update()
   for s in LEGS:
    points=[r.matrix_world@r.pose.bones[n].matrix@p for n,p in sole[s]]
    low=min(p.z-terrain(spec,p.x,p.y,t) for p in points)
    dz=.04-low if st['contact'][s] else max(0,.045-low)
    if abs(dz)>.001:delta('CTRL.canine.paw.'+s,(0,0,dz))
   if spec.get('terrain_mode'):
    bpy.context.view_layer.update();low=-1e6;high=1e6
    for s in LEGS:
     H=r.pose.bones['DEF.canine.upper.'+s].head;T=r.pose.bones['MCH.canine.target.'+s].head
     reach=r.data.bones['DEF.canine.upper.'+s].length+r.data.bones['DEF.canine.lower.'+s].length-.035
     span=math.sqrt(max(.01,reach*reach-(H.x-T.x)**2-(H.y-T.y)**2))
     minimum=abs(r.data.bones['DEF.canine.upper.'+s].length-r.data.bones['DEF.canine.lower.'+s].length)+.30
     minspan=math.sqrt(max(0,minimum*minimum-(H.x-T.x)**2-(H.y-T.y)**2))
     low=max(low,T.z+minspan-H.z);high=min(high,T.z+span-H.z)
    dz=max(low,min(0,high)) if low<=high else high
    if abs(dz)>.0001:delta('CTRL.body',(0,0,dz))
 bpy.context.view_layer.update();return st
specs=[]
for original in source['clips']:
 n=int(original['label'].split()[0]);spec={k:original[k] for k in ['label','slug','loop','category','gallery_group']};spec.update(number=n,action='T1 ANIM | '+original['label'],source_label=original['label'],hellcat_source_action=original['action'],fps=24,revision=1,nominal_speed_units_per_s=0,controller_preview_travel=False,preview_frame_step=3,markers=[])
 N=original['duration_frames']
 if n<=5:N=GAITS[n-1 if n<=3 else n-4]['N']
 if 6<=n<=8:N=GAITS[n-6]['N']+48
 if 9<=n<=12:N=(0 if n==9 else GAITS[n-10]['N'])+84
 if 13<=n<=16:N=64 if n<15 else 40
 if 17<=n<=25:
  k=n-17 if n<=19 else (n-20)//2;N=GAITS[k]['N']*2;spec['terrain_mode']='rough' if n<=19 else 'uphill' if n%2==0 else 'downhill';spec['terrain_period']=GAITS[k]['stride']*2/GAITS[k]['duty'];spec['reference_slope_degrees']=0 if n<=19 else 22
 if 42<=n<=45:
  N=48;spec['controller_preview_travel']=True;spec['controller_distance_units']=5.5 if n==42 else 4.5;spec['controller_direction']={42:[0,-1,0],43:[0,1,0],44:[1,0,0],45:[-1,0,0]}[n]
  if n==42:spec['label']='42 Forward Hull Ram';spec['action']='T1 ANIM | 42 Forward Hull Ram'
 spec['duration_frames']=N
 if n<=5 or 6<=n<=8 or 10<=n<=25:
  k=n-1 if n<=3 else n-4 if n<=5 else n-6 if n<=8 else max(0,min(2,n-10)) if n<=12 else 0 if n<=14 else 1 if n<=16 else n-17 if n<=19 else (n-20)//2;c=GAITS[k];spec['nominal_speed_units_per_s']=round(c['stride']/(c['duty']*c['N']/24),3)*(-1 if n in [4,5] else 1)
 if n<=5:
  c=GAITS[n-1 if n<=3 else n-4];spec['markers']=[{'name':s+' touchdown','frame':1+int((-off)%1*N)} for s,off in zip(LEGS,c['offset'])]
 if 9<=n<=12:
  lead=0 if n==9 else GAITS[n-10]['N'];spec['markers']=[{'name':a,'frame':f+1} for a,f in [('Load',lead),('Takeoff',lead+16),('Apex',lead+30),('Land',lead+44)]]
 if 42<=n<=45:spec['markers']=[{'name':a,'frame':f} for a,f in [('Load',1),('Rear-leg drive',11),('Landing',30),('Follow through',35),('Ready',49)]]
 if n==47:spec['timing_note']='32-beat quadruped adaptation of the existing Time Warp emote; no soundtrack audio included.'
 if n in [35,39,40,41,46,47]:
  spec['revision']=2;spec['preview_frame_step']=2
  if n==35:
   spec['preview_frame_step']=1
   spec['markers']=[{'name':a,'frame':f} for a,f in [('Fire',10),('Barrel back',12),('Hull impact',18),('Leg compression',21),('Recovered',39)]]
  if n in [39,40,41]:
   spec['label']={39:'39 Death Forward Slump',40:'40 Death Backward Slump',41:'41 Death Staggered Collapse'}[n]
   spec['markers']=[{'name':a,'frame':f} for a,f in [('First legs fail',11),('Remaining legs fold',31),('Hull settles',57),('Rest',80)]]
 specs.append(spec)
ctx=dict(rig=r.name,source_scene=scene.name,specs=specs,apply=apply,terrain=terrain,cloud=world_cloud,sole=sole,controls=CONTROL)
bpy.app.driver_namespace['T1 library']=ctx
out=ROOT/'build/t1_library';out.mkdir(parents=True,exist_ok=True);(out/'specs.json').write_text(json.dumps(specs,indent=2))
def bake(numbers):
 records=[]
 for spec in specs:
  if spec['number'] not in numbers:continue
  existing=bpy.data.actions.get(spec['action'])
  if existing:existing.name=spec['action']+' | previous pass';existing.use_fake_user=True
  action=bpy.data.actions.new(spec['action']);action.use_fake_user=True;r.animation_data.action=action
  for t in sorted(set(range(0,spec['duration_frames']+1,1 if spec.get('terrain_mode') or spec['number']==35 else 2))|{spec['duration_frames']}):
   apply(spec,t)
   for n in CONTROL:
    p=r.pose.bones[n];p.keyframe_insert('location',frame=t+1,group=n);p.keyframe_insert('rotation_quaternion',frame=t+1,group=n)
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for f in bag.fcurves:
      for k in f.keyframe_points:k.interpolation='LINEAR'
  for mark in spec['markers']:action.pose_markers.new(mark['name']).frame=mark['frame']
  action['mech']='T1 Artillery Walker';action['in_place']=True;action['clip_number']=spec['number'];action['description']='Quadruped counterpart with protected telescopic hydraulics and independent roof turret.'
  records.append(spec['label'])
 r.animation_data.action=None;print('Baked:',records)
ctx['bake']=bake
print('T1 recipes ready:',len(specs),'clips; foot samples:',{s:len(v) for s,v in sole.items()})
