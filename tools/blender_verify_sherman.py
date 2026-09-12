"""Sample actual IK, soles, loop closure, native feed drivers and armor contacts."""
import bpy,math,json,itertools
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(PROJECT_ROOT);r=bpy.data.objects['SHERMAN WALKER | ANIMATION RIG'];scene=bpy.context.scene
ctx=bpy.app.driver_namespace['SW locomotion context']
if 'proxies' not in ctx:
    proxies={};foot={s:[] for s in ['L','R']}
    for o in scene.objects:
        if o.type!='MESH' or not o.visible_get():continue
        T=r.matrix_world.inverted()@o.matrix_world
        groups={g.index:g.name for g in o.vertex_groups}
        for side in foot:
            gs={i for i,n in groups.items() if n in ['DEF.foot.'+side,'CTRL.toe.'+side]}
            foot[side].extend(T@v.co for v in o.data.vertices if any(g.group in gs and g.weight>.99 for g in v.groups))
        selected=any(s in o.name for s in ['thigh side armor','rear thigh wrap','rear calf wrap','skeletal frames','hip | inner curved plate','hip | outer curved plate','broad belly armor','curved lower casting','closed armored belly pan','stepped front and neck armor','tapered forearm armor','curved armored ammunition magazine','shoulder | inner curved plate','shoulder | outer curved plate'])
        if not selected:continue
        for bone in set(groups.values()):
            if bone not in r.pose.bones:continue
            ids={v.index for v in o.data.vertices if any(groups[g.group]==bone and g.weight>.99 for g in v.groups)}
            faces=[tuple(p.vertices) for p in o.data.polygons if all(i in ids for i in p.vertices)]
            if not faces:continue
            transform=r.data.bones[bone].matrix_local.inverted()@T
            proxies[o.name+' :: '+bone]=(bone,[transform@v.co for v in o.data.vertices],faces)
    ctx['proxies']=proxies;ctx['foot_cloud']=foot
proxies=ctx['proxies'];foot=ctx['foot_cloud']
def trees():
    return {name:BVHTree.FromPolygons([r.pose.bones[bone].matrix@v for v in vs],fs) for name,(bone,vs,fs) in proxies.items()}
def contacts():
    ts=trees();hits=[]
    for a,b in itertools.combinations(proxies,2):
        ba=proxies[a][0];bb=proxies[b][0]
        if ba==bb:continue
        if ba.startswith('CTRL') and bb.startswith('CTRL'):continue
        h=ts[a].overlap(ts[b])
        if h:hits.append((a,b,len(h)))
    return hits
if 'baseline_contacts' not in ctx:
    action=r.animation_data.action;r.animation_data.action=None
    saved={p.name:p.matrix_basis.copy() for p in r.pose.bones}
    for p in r.pose.bones:p.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
    ctx['baseline_contacts']={(a,b):n for a,b,n in contacts()}
    r.animation_data.action=action
    for n,m in saved.items():r.pose.bones[n].matrix_basis=m
c=ctx['configs'][VERIFY_CLIP];r.animation_data.action=bpy.data.actions[c['action']]
report={'action':c['action'],'frames':c['frames'],'kinematics':[],'new_proxy_contacts':[],'baseline_contacts':len(ctx['baseline_contacts']),'proxy_count':len(proxies)}
start=None
for f in range(1,c['frames']+2):
    scene.frame_set(f);bpy.context.view_layer.update()
    row={'frame':f,'root_translation':list(r.pose.bones['CTRL.root'].location),'legs':{}}
    for s in ['L','R']:
        thigh=r.pose.bones['DEF.thigh.'+s];shin=r.pose.bones['DEF.shin.'+s];ft=r.pose.bones['DEF.foot.'+s];target=r.pose.bones['CTRL.foot_IK.'+s]
        mat=ft.matrix@ft.bone.matrix_local.inverted()
        minz=min((mat@v).z for v in foot[s])
        a=(thigh.tail-thigh.head).normalized();b=(shin.tail-shin.head).normalized()
        row['legs'][s]={'ik_error':(shin.tail-target.head).length,'sole_min_z':minz,'knee_flex_degrees':math.degrees(a.angle(b))}
    u=r.pose.bones['CTRL.arm.upper.L'];a=r.pose.bones['CTRL.arm.forearm.L'];g=r.pose.bones['CTRL.arm.gun.L']
    axis=(u.tail-u.head).normalized()
    row['arm_centerline_error']=max(((v-u.head).cross(axis)).length for v in [u.tail,a.head,a.tail,g.head,g.tail])
    report['kinematics'].append(row)
    if f==1:start={p.name:p.matrix.copy() for p in r.pose.bones}
    if f==c['frames']+1:report['loop_matrix_error']=max(abs(p.matrix[i][j]-start[p.name][i][j]) for p in r.pose.bones for i in range(4) for j in range(4))
    if f<=c['frames']:
        new=[(a,b,n) for a,b,n in contacts() if (a,b) not in ctx['baseline_contacts']]
        if new:report['new_proxy_contacts'].append({'frame':f,'pairs':new})
report['invalid_driver_count']=sum(not d.driver.is_valid for o in scene.objects if o.animation_data for d in o.animation_data.drivers)
report['max_arm_centerline_error']=max(row['arm_centerline_error'] for row in report['kinematics'])
report['max_ik_error']=max(leg['ik_error'] for x in report['kinematics'] for leg in x['legs'].values())
report['min_sole_z']=min(leg['sole_min_z'] for x in report['kinematics'] for leg in x['legs'].values())
ctx.setdefault('verification',{})[c['slug']]=report
out=ROOT/'build/sherman_locomotion';out.mkdir(parents=True,exist_ok=True)
(out/(c['slug']+'_verification.json')).write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='kinematics'}))
