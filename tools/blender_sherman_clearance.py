"""Clear the rear knee folding space while preserving mesh backups and bindings."""
import bpy,json
from mathutils import Vector
r=bpy.data.objects['SHERMAN WALKER | ANIMATION RIG'];ctx=bpy.app.driver_namespace['SW locomotion context'];changed=[]
for o in bpy.context.scene.objects:
    if o.type!='MESH' or not o.visible_get():continue
    if o.name in ctx.get('clearance_backups',{}):
        o.data=ctx['clearance_backups'][o.name].copy()
    group=None
    if o.name.startswith(('R24 L |','R24 R |')):
        if any(x in o.name for x in ['rear thigh wrap','thigh access','rear guard mounting post']):group='rear_thigh'
        elif any(x in o.name for x in ['rear calf wrap','calf service hatch']):group='rear_calf'
    sidearmor=o.name in ['Left L3 | thigh side armor','Right L3 | thigh side armor']
    hardware=o.name.startswith(('Left L3 |','Right L3 |')) and any(x in o.name for x in ['recessed washers','edge chips'])
    if not group and not sidearmor and not hardware:continue
    T=r.matrix_world.inverted()@o.matrix_world;inv=T.inverted();edits=[]
    for v in o.data.vertices:
        p=T@v.co
        if group=='rear_thigh':
            p.z=4.92+(p.z-3.9586)*(6.7705-4.92)/(6.7705-3.9586)
            taper=max(0,min(1,(p.z-4.92)/1.85))
            if p.y>.025:p.y=.025+(p.y-.025)*(.15+.85*taper)
        elif group=='rear_calf':
            p.z=1.8912+(p.z-1.8912)*(2.58-1.8912)/(3.24-1.8912)
            taper=max(0,min(1,(p.z-1.8912)/.6888))
            if p.y>.35:p.y=.35+(p.y-.35)*(1-.8*taper)
        elif sidearmor or (hardware and 4.08<p.z<6.78 and any(o.vertex_groups[g.group].name.startswith('DEF.thigh.') and g.weight>.99 for g in v.groups)):
            p.z=4.80+(p.z-4.19)*(6.67-4.80)/(6.67-4.19)
        else:continue
        edits.append((v.index,inv@p))
    if not edits:continue
    if o.name not in ctx.setdefault('clearance_backups',{}):
        original=o.data;original.use_fake_user=True;ctx['clearance_backups'][o.name]=original
        o.data=original.copy();o.data.name='SW locomotion clearance | '+o.name
    for i,co in edits:o.data.vertices[i].co=co
    o.data.update();changed.append(o.name)
for key in ['proxies','foot_cloud','baseline_contacts']:ctx.pop(key,None)
ctx['clearance_changes']=changed
bpy.context.view_layer.update()
print(json.dumps({'adjusted_meshes':len(changed),'examples':changed[:12],'backups_retained':True,'saved_blend':False}))
