"""Verify terrain clips against the reference surface. Supply PROJECT_ROOT and HC_CHECK_LABELS."""
import bpy,json,math
from mathutils import Vector
rig=bpy.data.objects['HELLCAT | CURRENT MECH RIG'];scene=bpy.context.scene;ctx=bpy.app.driver_namespace['HC animation build context'];ext=bpy.app.driver_namespace['HC terrain revision context']
old=rig.animation_data.action;slot=rig.animation_data.action_slot;fr=scene.frame_current;saved={p.name:p.matrix_basis.copy() for p in rig.pose.bones};reports=[]
labels=globals().get('HC_CHECK_LABELS',[s['label'] for s in bpy.app.driver_namespace['HC animation library specs'] if int(s['label'][:2])>=21])
try:
 for spec in bpy.app.driver_namespace['HC animation library specs']:
  if spec['label'] not in labels:continue
  ctx['reset']();rig.animation_data.action=bpy.data.actions[spec['name']];root=reach=plant=seam=hinge=0;ground=100;first=None;hits={}
  for f in range(1,spec['duration']+2):
   scene.frame_set(f);st=spec['fn'](f-1);root=max(root,rig.pose.bones['CTRL.root'].location.length)
   pose={n:rig.pose.bones[n].matrix.copy() for n in ['CTRL.pelvis','CTRL.torso','DEF.thigh.L','DEF.shin.L','DEF.hock.L','DEF.foot.L','DEF.thigh.R','DEF.shin.R','DEF.hock.R','DEF.foot.R']}
   if first is None:first=pose
   if f==spec['duration']+1 and spec['loop']:seam=max(abs(a-b) for n,m in pose.items() for ra,rb in zip(m,first[n]) for a,b in zip(ra,rb))
   for side in ['L','R']:
    reach=max(reach,(rig.pose.bones['DEF.foot.'+side].head-rig.pose.bones['CTRL.foot_IK.'+side].head).length)
    mats={bn:rig.pose.bones[bn].matrix@rig.data.bones[bn].matrix_local.inverted() for bn in ['DEF.foot.'+side,'CTRL.toes.'+side]};ps=[mats[bn]@p for bn,p in ctx['sole'][side]]
    if 'terrain' in st:
     k,mode,d,h0=st['terrain'];low=min(p.z-(ext['terrain_height'](k,mode,p.x,p.y-d)-h0) for p in ps);target=.004
    else:low=min(p.z for p in ps);target=.003
    ground=min(ground,low)
    if st['contact'][side]:plant=max(plant,abs(low-target))
    for a,b in [('DEF.thigh.','DEF.shin.'),('DEF.shin.','DEF.hock.')]:
     ax=(rig.pose.bones[a+side].matrix.to_3x3()@Vector((1,0,0))).normalized();bx=(rig.pose.bones[b+side].matrix.to_3x3()@Vector((1,0,0))).normalized();hinge=max(hinge,1-abs(ax.dot(bx)))
   cache={}
   def get(n,p=None):
       if (n,p) not in cache:cache[n,p]=bpy.app.driver_namespace['HC weapon mesh_tree'](n,p)
       return cache[n,p]
   def pair(a,b,pa=None,pb=None):
       overlap=get(a,pa).overlap(get(b,pb))
       if overlap:hits.setdefault(a+' / '+b,[]).append({'frame':f,'faces':len(overlap)})
   for side in ['L','R']:
       pre='HC V2 '+side+' | '
       pair(pre+'02 layered thigh shells',pre+'03 curved knee guards')
       pair(pre+'07 load frames and brackets',pre+'02 layered thigh shells')
       for part in ['01 shaped hip armor','02 layered thigh shells']:
           pair(pre+part,'HC Hull | closed faceted lower tub')
           pair(pre+part,'HC Pods | twin armored sponsons',None,'CTRL.pod_aim')
       pair(pre+'05 faceted shin housings',pre+'08 layered toe and instep armor')
       pair(pre+'12 reverse hock to ankle links',pre+'08 layered toe and instep armor')
       pair(pre+'02 layered thigh shells','HC Cannon | continuous barrel and open bore')
  reports.append(dict(intersections=hits,name=spec['name'],frames_checked=spec['duration']+1,root_translation_max=root,foot_target_error_max=reach,minimum_surface_clearance=ground,planted_clearance_error=plant,hinge_axis_error=hinge,loop_seam_max=seam))
finally:
 rig.animation_data.action=old
 if slot:rig.animation_data.action_slot=slot
 for n,m in saved.items():rig.pose.bones[n].matrix_basis=m
 scene.frame_set(fr)
from pathlib import Path
folder=Path(PROJECT_ROOT)/'build/terrain_verification';folder.mkdir(parents=True,exist_ok=True)
for report in reports:(folder/(report['name'].split('| ')[1].lower().replace(' ','_')+'.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(reports))
