"""Verify the dance clip in live Blender. Supply PROJECT_ROOT."""
import bpy,json
from pathlib import Path
rig=bpy.data.objects['HELLCAT | CURRENT MECH RIG'];scene=bpy.context.scene
ctx=bpy.app.driver_namespace['HC animation build context'];dc=bpy.app.driver_namespace['HC time warp context']
tree=bpy.app.driver_namespace['HC weapon mesh_tree'];floor=bpy.app.driver_namespace['HC death context']['floor_low']
old=(rig.animation_data.action,scene.frame_current);root=slide=attachment=0;minimum=1e9;first=None;previous={};hits={}
try:
    ctx['reset']();rig.animation_data.action=bpy.data.actions['HC ANIM | 47 Time Warp']
    for f in range(1,266):
        scene.frame_set(f);st=dc['state'](f-1)
        p=rig.pose.bones['CTRL.root'];root=max(root,p.location.length,p.rotation_euler.to_matrix().to_quaternion().angle)
        minimum=min(minimum,floor()[0])
        if first is None:first={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
        for side in ['L','R']:
            point=rig.pose.bones['DEF.foot.'+side].head
            if st['contact'][side]:
                if side in previous:slide=max(slide,(point-previous[side]).xy.length)
                previous[side]=point.copy()
            else:previous.pop(side,None)
            for name in ['DEF.shin.','DEF.hock.','DEF.foot.']:
                p=rig.pose.bones[name+side];attachment=max(attachment,(p.head-p.parent.tail).length)
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

        for hull in ['HC Hull | closed faceted lower tub','HC Hull | layered casemate armor']:
            pair('HC Pods | twin armored sponsons',hull,'CTRL.pod_aim')
    seam=max(abs(p.matrix_basis[i][j]-first[p.name][i][j]) for p in rig.pose.bones for i in range(4) for j in range(4))
finally:
    ctx['reset']();rig.animation_data.action=old[0];scene.frame_set(old[1])
report={'clip':'47 Time Warp','frames_checked':265,'root_error':root,'minimum_body_surface_z':minimum,'maximum_planted_foot_slide':slide,'maximum_joint_attachment_error':attachment,'loop_seam':seam,'intersections':hits,'scope':'All frames: stationary root, conservative body floor clearance, planted-foot movement, leg joint attachment, loop endpoints, selected leg armor pairs and moving pod armor against the hull. Not an exhaustive all-object collision check.'}
(Path(PROJECT_ROOT)/'data/verification/time_warp.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
