"""Validate selected full-library Actions; supply VERIFY_NUMBERS through Blender MCP."""
import bpy,math,json,itertools
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(PROJECT_ROOT);r=bpy.data.objects['SHERMAN WALKER | ANIMATION RIG'];scene=bpy.context.scene
lib=bpy.app.driver_namespace['SW full library'];base=bpy.app.driver_namespace['SW locomotion context']
proxies=base['proxies'];baseline=base['baseline_contacts']
feet={s:np.array([(*v,1) for v in base['foot_cloud'][s]]) for s in ['L','R']}
from mathutils import Vector
view=Vector((24,-34,12)).normalized();q=(-view).to_track_quat('-Z','Y');axes=np.array([q@Vector((1,0,0)),q@Vector((0,1,0))]).T
out=ROOT/'build/sherman_full/verification';out.mkdir(parents=True,exist_ok=True)

def contacts():
    trees={name:BVHTree.FromPolygons([r.pose.bones[bone].matrix@v for v in vs],fs) for name,(bone,vs,fs) in proxies.items()};hits=[]
    for a,b in itertools.combinations(proxies,2):
        ba=proxies[a][0];bb=proxies[b][0]
        if ba==bb or (ba.startswith('CTRL') and bb.startswith('CTRL')):continue
        if (a,b) in baseline:continue
        h=trees[a].overlap(trees[b])
        if h:hits.append([a,b,len(h)])
    return hits
for spec in lib['specs']:
    if spec['number'] not in VERIFY_NUMBERS:continue
    r.animation_data.action=bpy.data.actions[spec['action']];N=spec['duration_frames']
    report=dict(label=spec['label'],action=spec['action'],frames=N,loop=spec['loop'],samples=[],contacts=[],invalid_drivers=0)
    sample_frames=set(range(1,N+1,max(1,N//10)))|{min(N,m['frame']) for m in spec['markers']}|{N}
    lo=np.array([1e9,1e9]);hi=-lo
    for f in range(1,N+2):
        scene.frame_set(f);bpy.context.view_layer.update();row={'frame':f,'ik':0,'floor':1e9,'arm':0}
        for s in ['L','R']:
            sh=r.pose.bones['DEF.shin.'+s];target=r.pose.bones['CTRL.foot_IK.'+s];foot=r.pose.bones['DEF.foot.'+s]
            row['ik']=max(row['ik'],(sh.tail-target.head).length)
            T=np.asarray(foot.matrix@foot.bone.matrix_local.inverted());ps=feet[s]@T.T
            if spec.get('terrain_mode'):
                h=np.array([lib['terrain'](spec,x,y,f-1) for x,y in ps[:,:2]])
                low=(ps[:,2]-h).min()
            else:low=ps[:,2].min()
            row['floor']=min(row['floor'],float(low))
        a=r.pose.bones['CTRL.arm.upper.L'];b=r.pose.bones['CTRL.arm.forearm.L'];g=r.pose.bones['CTRL.arm.gun.L'];axis=(a.tail-a.head).normalized()
        row['arm']=max(((v-a.head).cross(axis)).length for v in [a.tail,b.head,b.tail,g.head,g.tail])
        row['root']=max(abs(r.pose.bones['CTRL.root'].matrix_basis[i][j]-(1 if i==j else 0)) for i in range(4) for j in range(4))
        if f==1:first={p.name:p.matrix.copy() for p in r.pose.bones}
        if f==N+1:report['seam']=max(abs(p.matrix[i][j]-first[p.name][i][j]) for p in r.pose.bones for i in range(4) for j in range(4))
        report['samples'].append(row)
        if f in sample_frames:
            hits=contacts()
            if hits:report['contacts'].append({'frame':f,'pairs':hits})
            ps=lib['world_points']();projected=ps@axes
            lo=np.minimum(lo,projected.min(axis=0));hi=np.maximum(hi,projected.max(axis=0))
            if 39<=spec['number']<=41:row['body_floor_world']=float(ps[:,2].min())
    report['max_ik']=max(x['ik'] for x in report['samples']);report['min_floor']=min(x['floor'] for x in report['samples']);report['max_arm_error']=max(x['arm'] for x in report['samples']);report['root_error']=max(x['root'] for x in report['samples'])
    report['invalid_drivers']=sum(not d.driver.is_valid for o in scene.objects if o.animation_data for d in o.animation_data.drivers)
    report['view_bounds']=[list(lo),list(hi)]
    (out/(spec['slug']+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    lib.setdefault('verification',{})[spec['slug']]=report
    print(json.dumps({k:v for k,v in report.items() if k not in ['samples','contacts']}|{'contact_frames':len(report['contacts']),'pairs':list({(a,b) for x in report['contacts'] for a,b,n in x['pairs']})}))
