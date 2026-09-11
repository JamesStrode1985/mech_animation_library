"""Validate dodge Actions and the supplied controller trajectory. Supply PROJECT_ROOT."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector

rig=bpy.data.objects['HELLCAT | CURRENT MECH RIG'];scene=bpy.context.scene
ctx=bpy.app.driver_namespace['HC animation build context'];dc=bpy.app.driver_namespace['HC dodge context']
floor_low=bpy.app.driver_namespace['HC death context']['floor_low']
tree=bpy.app.driver_namespace['HC weapon mesh_tree']
original=(rig.animation_data.action,scene.frame_current);reports=[]
try:
    for c in dc['config']:
        ctx['reset']();rig.animation_data.action=bpy.data.actions['HC ANIM | '+c['label']]
        hits={};root_error=0;minimum_z=1e9;attachment=0;plant_slip=0;prior={};first=None;airborne=[];minimum_sole=1e9
        for f in range(1,32):
            scene.frame_set(f);t=f-1
            p=rig.pose.bones['CTRL.root'];root_error=max(root_error,p.location.length,p.rotation_euler.to_matrix().to_quaternion().angle)
            minimum_z=min(minimum_z,floor_low()[0]+dc['height'](c,t))
            travel=Vector(c['direction'])*dc['distance'](c,t);travel.z=dc['height'](c,t)
            feet=[]
            for side in ['L','R']:
                sole=min((rig.pose.bones[bn].matrix@rig.data.bones[bn].matrix_local.inverted()@point).z for bn,point in ctx['sole'][side])+travel.z
                feet.append(sole);minimum_sole=min(minimum_sole,sole)
                land=c['land'] if side==c['lead'] else c['trail_land']
                if t>=land:
                    point=rig.pose.bones['DEF.foot.'+side].head+travel
                    if side in prior:plant_slip=max(plant_slip,(point-prior[side]).xy.length)
                    prior[side]=point.copy()
                for name in ['DEF.shin.','DEF.hock.','DEF.foot.']:
                    p=rig.pose.bones[name+side];attachment=max(attachment,(p.head-p.parent.tail).length)
            if c['takeoff']<t<c['land']:airborne.append(min(feet))
            if f==1:first={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
            cache={}
            def get(n,p=None):
                if (n,p) not in cache:cache[n,p]=tree(n,p)
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
            if c.get('attack'):
                for hull in ['HC Hull | closed faceted lower tub','HC Hull | layered casemate armor']:
                    pair('HC Pods | twin armored sponsons',hull,'CTRL.pod_aim')
        neutral=max(abs(p.matrix_basis[i][j]-first[p.name][i][j]) for p in rig.pose.bones for i in range(4) for j in range(4))
        reports.append({'clip':c['label'],'frames_checked':31,'root_error':root_error,'minimum_surface_z_with_controller':minimum_z,'minimum_sole_z_with_controller':minimum_sole,'minimum_both_feet_airborne_clearance':min(airborne),'maximum_landing_foot_slide_per_frame':plant_slip,'maximum_joint_attachment_error':attachment,'start_end_pose_delta':neutral,'intersections':hits})
        if c.get('attack'):
            support=[];swing_clearance=[]
            for f in range(1,c['takeoff']+2):
                scene.frame_set(f)
                travel=Vector(c['direction'])*dc['distance'](c,f-1)
                support.append(rig.pose.bones['DEF.foot.L'].head+travel)
                if c['lead_release']+1<f<c['takeoff']+1:
                    swing_clearance.append(min((rig.pose.bones[bn].matrix@rig.data.bones[bn].matrix_local.inverted()@point).z for bn,point in ctx['sole']['R']))
            drive_slip=max((point-support[0]).xy.length for point in support)
            assert drive_slip<1e-4 and min(swing_clearance)>.02
            scene.frame_set(15);catch_yaw=rig.pose.bones['CTRL.torso'].rotation_euler.y
            scene.frame_set(18)
            follow_through=math.degrees(rig.pose.bones['CTRL.torso'].rotation_euler.y-catch_yaw)
            assert follow_through>15,'Shoulder drive must continue after the receiving foot plants.'
            transform=rig.pose.bones['CTRL.torso'].matrix@rig.data.bones['CTRL.torso'].matrix_local.inverted()
            right=transform@Vector((-1,0,4));left=transform@Vector((1,0,4))
            lead=left.y-right.y
            assert lead>1.5,'The right shoulder must lead along forward -Y at impact.'
            reports[-1]['ram']={'impact_frame':18,'right_shoulder_lead_over_left_units':lead,'active_frames':[15,20],'drive_leg':'left','catch_leg':'right','catch_frame':15,'drive_foot_world_slide':drive_slip,'minimum_receiving_foot_clearance_during_drive':min(swing_clearance),'shoulder_follow_through_degrees_after_plant':follow_through}
finally:
    ctx['reset']();rig.animation_data.action=original[0];scene.frame_set(original[1])
data={'reports':reports,'scope':'All 124 frames: stationary gameplay root, conservative body and exact cached sole clearance with supplied controller trajectory, airborne feet, landing foot locking, joint attachment, matching neutral endpoints, and intersections for listed thigh/knee/load-frame/hull/pod/shin/instep/barrel pairs. Ram also checks moving pod armor against both hull sections at all 31 frames and right shoulder leading at impact. Not an exhaustive every-object collision check.'}
(Path(PROJECT_ROOT)/'data/verification/dodge_animations.json').write_text(json.dumps(data,indent=2)+'\n')
bpy.app.driver_namespace['HC dodge verification']=data
print(json.dumps(data))
