"""Check death animation geometry and root behavior. Supply PROJECT_ROOT."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

rig=bpy.data.objects['HELLCAT | CURRENT MECH RIG'];scene=bpy.context.scene
ctx=bpy.app.driver_namespace['HC animation build context'];dc=bpy.app.driver_namespace['HC death context']
original=(rig.animation_data.action,scene.frame_current)
def tree(name,prefix=None):
    o=bpy.data.objects[name]
    mats={g.index:rig.matrix_world@rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted()@rig.matrix_world.inverted()@o.matrix_world for g in o.vertex_groups if g.name in rig.pose.bones}
    vs=[sum((mats[g.group]@v.co*g.weight for g in v.groups if g.group in mats),Vector()) for v in o.data.vertices]
    ids={v.index for v in o.data.vertices if prefix is None or any(o.vertex_groups[g.group].name.startswith(prefix) and g.weight>.99 for g in v.groups)}
    return BVHTree.FromPolygons(vs,[tuple(p.vertices) for p in o.data.polygons if all(i in ids for i in p.vertices)])
reports=[]
try:
    for c in dc['config']:
        ctx['reset']();rig.animation_data.action=bpy.data.actions['HC ANIM | '+c['label']]
        hits={};low=1e9;root_error=0;attachment=0;hinge=0;settled=0;last=None;pose_count=0
        for f in range(1,c['duration']+2):
            scene.frame_set(f)
            root_error=max(root_error,rig.pose.bones['CTRL.root'].location.length,rig.pose.bones['CTRL.root'].rotation_euler.to_matrix().to_quaternion().angle)
            low=min(low,dc['floor_low']()[0])
            for side in ['L','R']:
                for bn in ['DEF.shin.','DEF.hock.','DEF.foot.']:
                    p=rig.pose.bones[bn+side];attachment=max(attachment,(p.head-p.parent.tail).length)
                a=rig.pose.bones['DEF.thigh.'+side].matrix.to_3x3().col[0].normalized();b=rig.pose.bones['DEF.shin.'+side].matrix.to_3x3().col[0].normalized()
                hinge=max(hinge,1-abs(a.dot(b)))
            if f>=c['impact']+36:
                now={p.name:p.matrix.copy() for p in rig.pose.bones}
                if last:
                    settled=max(settled,max(abs(now[n][i][j]-last[n][i][j]) for n in now for i in range(4) for j in range(4)))
                last=now
            if f%4==1 or f==c['impact']+1:
                pose_count+=1;cache={}
                def get(n,p=None):
                    if (n,p) not in cache:cache[n,p]=tree(n,p)
                    return cache[n,p]
                def pair(a,b,pa=None,pb=None):
                    h=get(a,pa).overlap(get(b,pb))
                    if h:hits.setdefault(a+' / '+b,[]).append({'frame':f,'faces':len(h)})
                for side in ['L','R']:
                    pre='HC V2 '+side+' | '
                    pair(pre+'02 layered thigh shells',pre+'03 curved knee guards')
                    pair(pre+'07 load frames and brackets',pre+'02 layered thigh shells')
                    for part in ['01 shaped hip armor','02 layered thigh shells']:
                        pair(pre+part,'HC Hull | closed faceted lower tub')
                        pair(pre+part,'HC Pods | twin armored sponsons',None,'CTRL.pod_aim')
                    for part in ['02 layered thigh shells','03 curved knee guards','05 faceted shin housings']:
                        pair(pre+part,'HC Cannon | continuous barrel and open bore')
        reports.append({'clip':c['label'],'frames_checked':c['duration']+1,'mesh_poses_checked':pose_count,'minimum_conservative_surface_z':low,'root_error':root_error,'max_joint_attachment_error':attachment,'max_hinge_axis_error':hinge,'settled_matrix_delta':settled,'intersections':hits})
finally:
    rig.animation_data.action=original[0];ctx['reset']();scene.frame_set(original[1])
data={'reports':reports,'scope':'Every frame: stationary gameplay root, conservative skinned-vertex floor clearance, leg attachment, hinge axes and final hold. Sampled frames: thigh/knee shells, load frames, upper legs versus hull/pods, and main barrel versus thigh/knee/shin armor. Embedded bearings/mantlet and all other unlisted pairs excluded.'}
path=Path(PROJECT_ROOT)/'data/verification/death_animations.json';path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
bpy.app.driver_namespace['HC death verification']=data
print(json.dumps(data))
