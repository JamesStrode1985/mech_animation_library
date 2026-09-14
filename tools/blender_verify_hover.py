"""Verify baked hover Actions at every integer frame; no Blender save."""
import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Matrix
root=Path(PROJECT_ROOT);ctx=bpy.app.driver_namespace['HT library'];rig=bpy.data.objects[ctx['rig']];scene=bpy.data.scenes[ctx['source_scene']]
out=root/'build/hover_library/verification';out.mkdir(parents=True,exist_ok=True)
for spec in ctx['specs']:
 if spec['number'] not in globals().get('VERIFY_NUMBERS',range(1,48)):continue
 rig.animation_data.action=bpy.data.actions[spec['action']];ends=[];rooterr=0.;minclear=1000.;lo=np.array([1e6]*3);hi=-lo;maxrecoil=0.;maxlanding=0.
 for f in range(1,spec['duration_frames']+2):
  scene.frame_set(f);bpy.context.view_layer.update();p=rig.pose.bones['ROOT'];rooterr=max(rooterr,p.location.length,p.rotation_euler.to_quaternion().angle)
  if f in [1,spec['duration_frames']+1]:ends.append([p.matrix.copy() for p in rig.pose.bones])
  for name,pts in ctx['cloud'].items():
   D=np.asarray(rig.pose.bones[name].matrix@rig.data.bones[name].matrix_local.inverted());w=(pts@D.T)[:,:3];minclear=min(minclear,float((w[:,2]-ctx['terrain'](spec,w[:,0],w[:,1],f-1)).min()));lo=np.minimum(lo,w.min(axis=0));hi=np.maximum(hi,w.max(axis=0))
  maxrecoil=max(maxrecoil,rig.pose.bones['Cannon_Recoil'].location.y);maxlanding=max(maxlanding,float(rig['landing_deploy']))
 seam=max(abs(a[i][j]-b[i][j]) for a,b in zip(*ends) for i in range(4) for j in range(4))
 report=dict(action=spec['action'],frames=spec['duration_frames'],root_error=rooterr,min_sampled_clearance=minclear,loop=spec['loop'],loop_seam_error=seam,world_bounds=[lo.tolist(),hi.tolist()],max_recoil=maxrecoil,max_landing=maxlanding)
 (out/(spec['slug']+'.json')).write_text(json.dumps(report,indent=2));print(spec['number'],round(minclear,4),round(seam,5) if spec['loop'] else '-',round(maxlanding,2) if spec['number']==34 else '')
rig.animation_data.action=None
