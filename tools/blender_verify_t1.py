"""Bounded per-Action checks. VERIFY_NUMBERS selects clips; no model save."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(PROJECT_ROOT);ctx=bpy.app.driver_namespace['T1 library'];r=bpy.data.objects[ctx['rig']];scene=bpy.context.scene
out=ROOT/'build/t1_library/verification';out.mkdir(parents=True,exist_ok=True)
VERIFY_NUMBERS=globals().get('VERIFY_NUMBERS',list(range(1,48)))
for spec in ctx['specs']:
 if spec['number'] not in VERIFY_NUMBERS:continue
 r.animation_data.action=bpy.data.actions[spec['action']];maxik=0;minfloor=1000;rooterr=0;ends=[];lo=Vector((1e6,)*3);hi=Vector((-1e6,)*3)
 for f in range(1,spec['duration_frames']+2):
  scene.frame_set(f);bpy.context.view_layer.update()
  for s in ['front.L','front.R','rear.L','rear.R']:
   maxik=max(maxik,(r.pose.bones['DEF.canine.lower.'+s].tail-r.pose.bones['MCH.canine.target.'+s].head).length)
   for n,p in ctx['sole'][s]:
    v=r.matrix_world@r.pose.bones[n].matrix@p;minfloor=min(minfloor,v.z-ctx['terrain'](spec,v.x,v.y,f-1))
  rooterr=max(rooterr,r.pose.bones['CTRL.root'].location.length,r.pose.bones['CTRL.root'].rotation_quaternion.angle)
  if f in [1,spec['duration_frames']+1]:ends.append([p.matrix.copy() for p in r.pose.bones])
  if f%8==1 or f==spec['duration_frames']+1:
   cloud=ctx['cloud']();vmin=cloud.min(axis=0);vmax=cloud.max(axis=0)
   for i in range(3):lo[i]=min(lo[i],vmin[i]);hi[i]=max(hi[i],vmax[i])
 seam=max(abs(a[i][j]-b[i][j]) for a,b in zip(*ends) for i in range(4) for j in range(4))
 report=dict(action=spec['action'],frames=spec['duration_frames'],max_ik_error=maxik,min_sampled_sole_clearance=minfloor if minfloor<1000 else None,root_error=rooterr,loop=spec['loop'],loop_seam_error=seam,world_bounds=[list(lo),list(hi)],scope='All integer frames: leg endpoint IK, sampled sole vertices, identity gameplay root. Sampled whole-model bounds; not exhaustive surface collision validation.')
 (out/(spec['slug']+'.json')).write_text(json.dumps(report,indent=2));print(spec['number'],round(maxik,5),round(minfloor,4),round(seam,5) if spec['loop'] else 'one shot')
r.animation_data.action=None
