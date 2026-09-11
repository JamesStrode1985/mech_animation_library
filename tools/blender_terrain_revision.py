"""Rebuild rough terrain and 22-degree slopes. Run through Blender MCP with PROJECT_ROOT.
Requires the live HELLCAT rig and existing animation contexts. Does not save .blend.
Optional TERRAIN_LABELS restricts the Actions rebuilt.
"""
import bpy,math,json,hashlib
from mathutils import Vector
from pathlib import Path
ctx=bpy.app.driver_namespace['HC animation build context']
base=bpy.app.driver_namespace['HC extended locomotion context']
rig=bpy.data.objects['HELLCAT | CURRENT MECH RIG'];scene=bpy.context.scene
N=base['N'];SPEED=base['SPEED'];gait=base['gait'];rot=ctx['rot']
def terrain_height(k,mode,x,y):
 if mode in ['uphill','downhill']:return (-1 if mode=='downhill' else 1)*math.tan(math.radians(22))*(-y)
 period=SPEED[k]*N[k]*(4 if k=='walk' else 2)/24
 q=math.tau*y/period
 f=min(1,period/4)
 return .42+.225*f*math.sin(q)+.105*f*math.sin(2*q+.9*x)+.18*math.sin(1.5*x)+.06*f*math.sin(q+.9*x)+.035*f*math.sin(3*q-1.3*x)

def terrain_gait(k,mode,t):
 st=gait(k,t);d=SPEED[k]*t/24;h0=terrain_height(k,mode,0,-d);st['preview_z']=h0
 st['terrain']=(k,mode,d,h0)
 for side,sign in [('L',1),('R',-1)]:
  n='CTRL.foot_IK.'+side;v=list(st['loc'][n]);x=sign*.91+v[0];y=-.08+v[1]-d;h=terrain_height(k,mode,x,y)-h0
  v[2]*=1.5 if mode=='rough' else 1.2;st['lift'][side]=max(0,v[2]);v[2]+=h;st['loc'][n]=tuple(v)
  eps=.025;gx=(terrain_height(k,mode,x+eps,y)-terrain_height(k,mode,x-eps,y))/(2*eps);gy=(terrain_height(k,mode,x,y+eps)-terrain_height(k,mode,x,y-eps))/(2*eps)
  pitch=math.degrees(st['rot'].get('CTRL.ankle_tilt.'+side,(0,0,0))[0])*.5+math.degrees(math.atan(gy))
  roll=math.degrees(math.atan(gx));rot(st,'CTRL.ankle_tilt.'+side,(max(-24,min(24,pitch)),max(-11,min(11,roll)),0))
  if not st['contact'][side] and mode=='rough':
   st['loc'][n]=(v[0],v[1],v[2]+.04*math.sin(math.pi*((t/N[k]+(0 if side=='L' else .5))%1)))
 v=list(st['loc']['CTRL.pelvis']);v[2]-=.10 if mode=='rough' else .10
 if k=='sprint' and mode=='downhill':v[2]-=.10*math.cos(math.pi*((2*t/N[k])%1))**8
 st['loc']['CTRL.pelvis']=tuple(v)
 v=list(st['rot']['CTRL.torso']);v[0]+=math.radians(7 if mode=='uphill' else (-9 if mode=='downhill' else 0));
 if mode=='rough':
  eps=.08;gx=(terrain_height(k,mode,eps,-d)-terrain_height(k,mode,-eps,-d))/(2*eps);gy=(terrain_height(k,mode,0,-d+eps)-terrain_height(k,mode,0,-d-eps))/(2*eps)
  v[0]+=max(-.10,min(.10,-gy*.22));v[2]+=max(-.09,min(.09,-gx*.25))
 st['rot']['CTRL.torso']=tuple(v)
 return st

def apply_new(st,upper_only=False):
 if 'terrain' not in st:return ctx['apply'](st,upper_only)
 ctx['reset']()
 for n,v in st['loc'].items():rig.pose.bones[n].location=rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector(v)
 for n,v in st['rot'].items():rig.pose.bones[n].rotation_euler=v
 for n,v in st['scale'].items():rig.pose.bones[n].scale=v
 bpy.context.view_layer.update();k,mode,d,h0=st['terrain']
 for terrain_iteration in range(6):
  correction=0
  for side in ['L','R']:
   mats={bn:rig.pose.bones[bn].matrix@rig.data.bones[bn].matrix_local.inverted() for bn in ['DEF.foot.'+side,'CTRL.toes.'+side]}
   ps=[mats[bn]@p for bn,p in ctx['sole'][side]]
   low=min(p.z-(terrain_height(k,mode,p.x,p.y-d)-h0) for p in ps)
   desired=.004 if st['contact'][side] else .004+st['lift'][side]*.30
   if mode=='uphill' and k=='run' and not st['contact'][side]:desired=max(desired,.085)
   delta=desired-low if st['contact'][side] else max(0,desired-low)
   correction=max(correction,abs(delta))
   rig.pose.bones['CTRL.foot_IK.'+side].location+=rig.data.bones['CTRL.foot_IK.'+side].matrix_local.to_3x3().inverted()@Vector((0,0,delta))
  bpy.context.view_layer.update()
  for _ in range(4):
   dz=0
   for side in ['L','R']:
    H=rig.pose.bones['DEF.thigh.'+side].head;B=rig.pose.bones['MCH.hock_target.'+side].head;L=rig.data.bones['DEF.thigh.'+side].length+rig.data.bones['DEF.shin.'+side].length-.025
    desired=B.z+math.sqrt(max(.01,L*L-(H.x-B.x)**2-(H.y-B.y)**2));dz=min(dz,desired-H.z)
   if dz>=-.00001:break
   rig.pose.bones['CTRL.pelvis'].location+=rig.data.bones['CTRL.pelvis'].matrix_local.to_3x3().inverted()@Vector((0,0,dz));bpy.context.view_layer.update()
  if correction<.000005 and dz>=-.00001:break

bank=bpy.app.driver_namespace['HC animation library specs']
specs=[s for s in bank if s.get('terrain_mode') in ['rough','uphill','downhill']]
selected=set(globals().get('TERRAIN_LABELS') or [s['label'] for s in specs])
def digest(action):
 return hashlib.sha256(repr([(fc.data_path,fc.array_index,[(tuple(k.co),k.interpolation) for k in fc.keyframe_points]) for l in action.layers for s in l.strips for b in s.channelbags for fc in b.fcurves]).encode()).hexdigest()
if 'HC terrain protected actions' not in bpy.app.driver_namespace:
 bpy.app.driver_namespace['HC terrain protected actions']={a.name:digest(a) for a in bpy.data.actions if a.name.startswith('HC ANIM | ') and a.name not in [s['name'] for s in specs]}
original=(rig.animation_data.action,rig.animation_data.action_slot,scene.frame_current)
try:
 for spec in specs:
  if spec['label'] not in selected:continue
  k=spec['terrain_kind'];mode=spec['terrain_mode'];spec['fn']=lambda t,k=k,m=mode:terrain_gait(k,m,t)
  previous=bpy.data.actions.get(spec['name'])
  if previous:
   previous.name='HC ARCHIVE | '+spec['label']+' | previous terrain';previous.use_fake_user=True;previous.asset_clear()
  action=bpy.data.actions.new(spec['name']);action.use_fake_user=True;rig.animation_data.action=action;samples=[]
  for f in range(1,spec['duration']+2):
   scene.frame_set(f);st=spec['fn'](f-1);apply_new(st)
   for n in ctx['controls']:
    p=rig.pose.bones[n]
    if n in ctx['FX']:p.keyframe_insert(data_path='scale',frame=f,group='Optional weapon FX')
    else:
     p.keyframe_insert(data_path='location',frame=f,group=n);p.keyframe_insert(data_path='rotation_euler',frame=f,group=n)
   samples.append({'frame':f,'contacts':st['contact'],'controller_preview_z':st['preview_z']})
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for key in fc.keyframe_points:key.interpolation='LINEAR'
      fc.modifiers.new('CYCLES')
  action['HC animation library']='MECH_2026_09';action['FPS']=24;action['Loop']=True;action['Category']=spec['category']
  action['Root motion']='None. Game controller supplies horizontal travel and ground height.'
  action['Reference slope degrees']=22 if mode=='uphill' else -22 if mode=='downhill' else 0
  action['Revision']='Rough terrain 3x and steep 22 degree slopes';action['Nominal speed units_per_s']=spec['speed']
  action['Contact and preview samples']=json.dumps(samples);action.asset_mark();action.asset_data.description=action['Revision']+'; in-place; 24 fps.'
  spec['samples']=samples
finally:
 ctx['reset']();rig.animation_data.action=original[0]
 if original[1]:rig.animation_data.action_slot=original[1]
 scene.frame_set(original[2])
bpy.app.driver_namespace['HC terrain revision context']={'terrain_height':terrain_height,'terrain_gait':terrain_gait,'apply':apply_new,'specs':specs,'digest':digest}
print(json.dumps({'rebuilt':sorted(selected),'saved':False}))
