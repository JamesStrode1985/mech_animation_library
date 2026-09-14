"""HT-01's 47 hover adaptations. Run in Blender through MCP with PROJECT_ROOT.
Pure motion recipes plus Action baking. Gameplay ROOT remains stationary.
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector,Matrix
import numpy as np
ROOT=Path(PROJECT_ROOT);rig=bpy.data.objects['HT-01 | RIG'];scene=bpy.context.scene
if rig.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
rig.animation_data_create();assert not any(a.name.startswith('HT ANIM | ') for a in bpy.data.actions),'Hover library already exists'
source=json.loads((ROOT/'data/manifest.json').read_text());FPS=24
CONTROL=['ROOT','Hull','Turret','Cannon_Elevation','Cannon_Recoil','MG_Yaw','MG_Elevation']
for n in CONTROL:rig.pose.bones[n].rotation_mode='XYZ'
# A small, conservative underside cloud catches ground penetration in authored preview terrain.
cloud={}
for o in bpy.data.collections['HT-01 | Weighted geometry'].objects:
 name=o['rigid_bone'];vs=list(o.data.vertices);low=min(v.co.z for v in vs)
 points=[v.co.copy() for i,v in enumerate(vs) if i%max(1,len(vs)//100)==0 or v.co.z<low+.025]
 if len(points)>800:points=points[::max(1,len(points)//800)]
 cloud[name]=np.array([(*v,1.) for v in points])
def smooth(x):x=max(0.,min(1.,x));return x*x*(3-2*x)
def env(t,keys):
 for (a,x),(b,y) in zip(keys,keys[1:]):
  if t<=b:return x+(y-x)*smooth((t-a)/(b-a))
 return keys[-1][1]
def pulse(t,a,w):return math.sin(math.pi*(t-a)/w)**2 if a<t<a+w else 0.
def terrain(spec,x,y,t):
 mode=spec.get('terrain_mode')
 if mode in ['uphill','downhill']:return (-y)*math.tan(math.radians(18 if mode=='uphill' else -18))
 if mode=='rough':
  phase=math.tau*(y/6.4-t/spec['duration_frames']);return .62*np.sin(phase+.38*x)+.23*np.sin(2*phase-.65*x)+.12*np.cos(x*1.1)
 return 0.*x
SPEED=[1.6,4.8,9.6];PERIOD=[96,64,48]
def cruise(k,t,period,reverse=False):
 q=math.tau*t/period
 return [0.,0.,[.09,.15,.23][k]*math.sin(2*q)],[(-1 if not reverse else 1)*[3.5,7.,11.][k]+[.7,1.3,2.1][k]*math.sin(q),[.7,1.1,1.7][k]*math.sin(q),.35*math.sin(q)]
def motion(spec,t):
 n=spec['number'];N=spec['duration_frames'];u=t/N;loc=[0.,0.,0.];rot=[0.,0.,0.];yaw=0.;aim=0.;mgyaw=0.;mgaim=0.;recoil=0.;landing=0.;shot=0.
 e=env(u,[(0,0),(.28,1),(.70,1),(1,0)])
 if n<=5:loc,rot=cruise(n-1 if n<=3 else n-4,t,N,n>3)
 elif 6<=n<=8:
  k=n-6;loc,rot=cruise(k,t,PERIOD[k]);w=1-smooth((u-.30)/.52);loc=[v*w for v in loc];rot=[v*w for v in rot];rot[0]+=([7,12,17][k])*pulse(u,.28,.48);loc[2]-=.16*pulse(u,.60,.25)
 elif 9<=n<=12:
  k=max(0,n-10);lead=0 if n==9 else 32;launch=lead+14;touch=launch+34
  if n>9:loc,rot=cruise(k,t,PERIOD[k]);rot[0]*=.8
  if t>=lead:
   loc[2]-=.30*pulse(t,lead,14)
   if launch<t<touch:
    q=(t-launch)/34;loc[2]+=(1.9+.30*k if n>9 else 1.7)*4*q*(1-q);rot[0]+=(-7 if n>9 else -4)*math.sin(math.tau*q)
   loc[2]-=.40*pulse(t,touch,18);rot[0]+=7*pulse(t,touch,17)
  if n==9:
   w=1-smooth((t-touch-18)/10);loc=[v*w for v in loc];rot=[v*w for v in rot]
 elif 13<=n<=16:
  sign=-1 if n in [13,15] else 1;k=0 if n<15 else 1;loc,rot=cruise(k,t,N);rot[0]*=.25;rot[1]=-sign*(7 if n<15 else 11)+1.2*math.sin(math.tau*u)
  if n>=15:
   rot[2]=sign*35;yaw=-sign*70;mgyaw=sign*22;mgaim=-8;shot=max(pulse(t,a,6) for a in range(6,N,16));recoil=.10*shot;rot[0]+=1.5*shot
 elif 17<=n<=25:
  k=n-17 if n<=19 else (n-20)//2;loc,rot=cruise(k,t,N)
  if n<=19:loc[2]+=.23*math.sin(math.tau*u);rot[0]+=5*math.sin(math.tau*u);rot[1]+=4*math.sin(2*math.tau*u+.4)
  else:rot[0]+=(-18 if n%2==0 else 18);loc[2]+=.18
 elif 26<=n<=38:
  if n==26:loc[2]=.08*math.sin(math.tau*u);rot[1]=.6*math.sin(math.tau*u)
  elif n==27:yaw=42*math.sin(math.tau*u);mgyaw=-60*math.sin(math.tau*u);loc[2]=.06*math.sin(2*math.tau*u)
  elif n in [28,29]:yaw=(65 if n==28 else -65)*e;rot[1]=(2 if n==28 else -2)*math.sin(math.tau*u)
  elif n in [30,31]:rot[0]=(-12 if n==30 else 12)*e;loc[2]=.28*e
  elif n in [32,33]:rot[1]=(-14 if n==32 else 14)*e;loc[2]=.40*e
  elif n==34:landing=env(u,[(0,0),(.4,1),(.7,1),(1,0)]);loc[2]=.05*math.sin(math.tau*u);rot[0]=-2*e
  elif n==35:
   recoil=.63*env(t,[(0,0),(9,0),(11,1),(16,.85),(36,0),(N,0)])
   impact=env(t,[(0,0),(11,0),(17,1),(22,.65),(42,0),(N,0)])
   loc[1]=.40*impact;loc[2]=-.30*pulse(t,13,28);rot[0]=-6*impact;shot=pulse(t,9,5)
  else:
   coarse=env(u,[(0,0),(.22,1),(.73,1),(1,0)]);fine=env(u,[(0,0),(.22,0),(.52,1),(.73,1),(1,0)])
   if n in [36,37]:rot[0]=(-10 if n==36 else 8)*coarse;aim=(-32 if n==36 else 9)*fine;mgaim=(-65 if n==36 else 14)*fine;loc[2]=.25*coarse
   else:yaw=45*math.sin(math.tau*u)*coarse;aim=-18*fine;mgyaw=-100*math.sin(math.tau*u)*coarse;mgaim=-50*fine;shot=pulse(t,65,6);recoil=.12*shot
 elif 39<=n<=41:
  fall=smooth((t-12)/45);settle=smooth((t-55)/18);sgn=1 if n==39 else -1
  rot[0]=(8*sgn if n<41 else 2)*fall;rot[1]=(13 if n==41 else .8)*fall
  shake=math.sin(t*1.7)*math.exp(-max(0,t-12)/20)*smooth(t/12)*(1-settle)
  rot[1]+=2*shake;loc[2]=-.99*fall+.07*pulse(t,56,16);loc[0]=(.20 if n==41 else 0)*fall;aim=7*fall;mgaim=13*fall;yaw=9*fall
 elif 42<=n<=45:
  sign=-1 if n==44 else 1
  push=env(t,[(0,0),(7,-.2),(13,1),(23,1),(32,.3),(N,0)])
  loc[2]=1.05*pulse(t,7,26)-.23*pulse(t,0,9)-.28*pulse(t,33,11)
  if n in [42,43]:rot[0]=(-15 if n==42 else 16)*push
  else:rot[1]=-sign*23*push
  if n==42:yaw=-12*push;rot[2]=10*push;loc[1]=-.24*push;rot[0]+=11*pulse(t,27,10)
 elif n==46:
  beat=u*16;q=math.pi*beat;loc=[.45*math.sin(q/2),.16*math.sin(q),.18+.24*math.sin(q)**2];rot=[4*math.sin(q),7*math.sin(q/2),0];yaw=22*math.sin(q/2);mgyaw=-35*math.sin(q/2);mgaim=-15*(.5+.5*math.sin(q))
 elif n==47:
  beat=u*32;hop=sum(.75*math.sin(math.pi*(beat-a)/2)**2 if a<beat<a+2 else 0 for a in [2,4,6,26,28]);thrust=math.sin(math.pi*(beat-14))**2 if 14<beat<24 else 0
  loc=[env(beat,[(0,0),(2,0),(4,-.65),(6,-.65),(8,0),(32,0)]),env(beat,[(0,0),(4,0),(6,.65),(8,0),(32,0)])-.45*thrust,hop-.22*thrust]
  rot=[8*thrust,env(beat,[(0,0),(8,0),(10,-8),(12,8),(14,0),(32,0)]),0];yaw=18*math.sin(math.pi*(beat-14)/2) if 14<beat<24 else 0;mgaim=-12*thrust
 return dict(loc=loc,rot=rot,yaw=yaw,aim=aim,mgyaw=mgyaw,mgaim=mgaim,recoil=recoil,landing=landing,shot=shot)
def apply(spec,t,correct=True):
 st=motion(spec,t)
 for name in CONTROL:rig.pose.bones[name].matrix_basis=Matrix.Identity(4)
 rig.pose.bones['Hull'].location=st['loc'];rig.pose.bones['Hull'].rotation_euler=[math.radians(a) for a in st['rot']]
 rig.pose.bones['Turret'].rotation_euler.z=math.radians(st['yaw']);rig.pose.bones['Cannon_Elevation'].rotation_euler.x=math.radians(st['aim']);rig.pose.bones['Cannon_Recoil'].location.y=st['recoil'];rig.pose.bones['MG_Yaw'].rotation_euler.z=math.radians(st['mgyaw']);rig.pose.bones['MG_Elevation'].rotation_euler.x=math.radians(st['mgaim'])
 rig['landing_deploy']=st['landing'];rig['hatch_left_open']=0.;rig['hatch_right_open']=0.;rig.update_tag();bpy.context.view_layer.update()
 if correct:
  low=1000.
  for name,points in cloud.items():
   D=np.asarray(rig.pose.bones[name].matrix@rig.data.bones[name].matrix_local.inverted());w=(points@D.T)[:,:3];clear=w[:,2]-terrain(spec,w[:,0],w[:,1],t);low=min(low,float(clear.min()))
  minimum=.03 if spec['number'] in [34,39,40,41] else .18
  if low<minimum:rig.pose.bones['Hull'].location.z+=minimum-low;bpy.context.view_layer.update()
 return st
names={1:'Slow Hover',2:'Cruise',3:'Boost',4:'Reverse Hover',5:'Reverse Cruise',6:'Slow Hover To Stop',7:'Cruise To Stop',8:'Boost To Stop',9:'Vertical Hop',10:'Slow Hover Into Hop',11:'Cruise Into Hop',12:'Boost Into Hop',13:'Slide Left',14:'Slide Right',15:'Strafe Fire Left',16:'Strafe Fire Right',17:'Slow Hover Rough Terrain',18:'Cruise Rough Terrain',19:'Boost Rough Terrain',20:'Slow Hover Uphill',21:'Slow Hover Downhill',22:'Cruise Uphill',23:'Cruise Downhill',24:'Boost Uphill',25:'Boost Downhill',26:'Hover Idle',27:'Turret Scan',28:'Turret Turn Left',29:'Turret Turn Right',30:'Hull Pitch Up',31:'Hull Pitch Down',32:'Bank Left',33:'Bank Right',34:'Landing Brace',35:'Cannon Recoil',36:'Aim Track Up',37:'Aim Track Down',38:'Independent Weapon Aim',39:'Death Forward Settling',40:'Death Backward Settling',41:'Death Side Lift Failure',42:'Forward Hull Ram',43:'Dodge Backward',44:'Dodge Left',45:'Dodge Right',46:'Dance Party',47:'Time Warp'}
specs=[]
for original in source['clips']:
 n=int(original['label'].split()[0]);label=f'{n:02d} '+names[n];N=96
 if n<=5:N=PERIOD[n-1 if n<=3 else n-4]
 elif 6<=n<=8:N=96
 elif 9<=n<=12:N=96 if n==9 else 128
 elif 13<=n<=16:N=96 if n<15 else 64
 elif 17<=n<=25:N=96
 elif n in [26,27]:N=96
 elif 28<=n<=34:N=72
 elif n==35:N=56
 elif 36<=n<=38:N=112
 elif 39<=n<=41:N=108
 elif 42<=n<=45:N=48
 elif n==46:N=192
 elif n==47:N=264
 spec=dict(number=n,label=label,source_label=label,hellcat_equivalent=original['label'],action='HT ANIM | '+label,slug=label.lower().replace(' ','_'),fps=24,duration_frames=N,loop=original['loop'],category=original['category'],gallery_group=original['gallery_group'],revision=1,preview_frame_step=2,nominal_speed_units_per_s=0.,controller_preview_travel=False,markers=[])
 k=n-1 if n<=3 else n-4 if n<=5 else n-6 if n<=8 else max(0,n-10) if n<=12 else 0 if n<=14 else 1 if n<=16 else n-17 if n<=19 else (n-20)//2 if n<=25 else 0
 if n<=25 and n!=9:
  spec['nominal_speed_units_per_s']=SPEED[k]*(-1 if n in [4,5] else 1);spec['preview_scrolling_ground']=True
  spec['travel_direction']=[(-1 if n in [13,15] else 1),0,0] if 13<=n<=16 else [0,1 if n in [4,5] else -1,0]
 if 17<=n<=25:spec['terrain_mode']='rough' if n<=19 else 'uphill' if n%2==0 else 'downhill';spec['reference_slope_degrees']=0 if n<=19 else 18
 if 42<=n<=45:
  spec['controller_preview_travel']=True;spec['controller_distance_units']=6.5 if n==42 else 5.5;spec['controller_direction']={42:[0,-1,0],43:[0,1,0],44:[-1,0,0],45:[1,0,0]}[n];spec['markers']=[{'name':s,'frame':f} for s,f in [('Load',1),('Thrust',9),('Travel complete',34),('Recovered',49)]]
 if 9<=n<=12:
  lead=0 if n==9 else 32;spec['markers']=[{'name':s,'frame':f+lead} for s,f in [('Load',1),('Takeoff',15),('Apex',32),('Lift catches',49)]]
 if n==35:spec['preview_frame_step']=1;spec['markers']=[{'name':s,'frame':f} for s,f in [('Fire',10),('Barrel back',12),('Hull impulse',18),('Recovered',43)]]
 if 39<=n<=41:spec['markers']=[{'name':s,'frame':f} for s,f in [('Lift fails',13),('Ground contact',58),('Settled',80)]]
 specs.append(spec)
out=ROOT/'build/hover_library';out.mkdir(parents=True,exist_ok=True);(out/'specs.json').write_text(json.dumps(specs,indent=2))
def bake(numbers):
 for spec in specs:
  if spec['number'] not in numbers:continue
  action=bpy.data.actions.new(spec['action']);action.use_fake_user=True;rig.animation_data.action=action
  for t in sorted(set(range(0,spec['duration_frames']+1,2))|{spec['duration_frames']}):
   apply(spec,t)
   for name in CONTROL:
    p=rig.pose.bones[name];p.keyframe_insert('location',frame=t+1,group=name);p.keyframe_insert('rotation_euler',frame=t+1,group=name)
   rig.keyframe_insert('["landing_deploy"]',frame=t+1,group='Landing gear')
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for f in bag.fcurves:
      for key in f.keyframe_points:key.interpolation='LINEAR'
  for mark in spec['markers']:action.pose_markers.new(mark['name']).frame=mark['frame']
  action['mech']='HT-01 Hover Tank';action['in_place']=True;action['clip_number']=spec['number'];action['hellcat_equivalent']=spec['hellcat_equivalent']
 rig.animation_data.action=None
 print('Baked',numbers)
bpy.app.driver_namespace['HT library']={'rig':rig.name,'source_scene':scene.name,'specs':specs,'apply':apply,'motion':motion,'terrain':terrain,'cloud':cloud,'bake':bake,'controls':CONTROL}
print('Prepared',len(specs),'hover tank animation recipes')

