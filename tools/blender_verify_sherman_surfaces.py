"""Check evaluated bevel/subdivision armor and articulated feed at key gait poses."""
import bpy,json,itertools
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(PROJECT_ROOT);r=bpy.data.objects['SHERMAN WALKER | ANIMATION RIG'];ctx=bpy.app.driver_namespace['SW locomotion context']
c=ctx['configs'][VERIFY_CLIP];r.animation_data.action=bpy.data.actions[c['action']]
links=[o.name for o in bpy.data.collections['R36 | protected arm feed'].objects if ' link ' in o.name]
obstacles=['Hull R8 | broad belly armor 2','Hull R8 | curved lower casting 1','R33 L hip | inner curved plate','R33 L hip | outer curved plate','Right L3 | thigh side armor','R33 L shoulder | inner curved plate','R33 L shoulder | outer curved plate','R26 L | inner ball joint armored collar','Arm R5 | tapered forearm armor','Arm R5 | gun receiver and open action','Arm R5 | curved armored ammunition magazine','Arm R5 | enclosed elbow transmission']
pairs=[]
for side,label in [('L','Right'),('R','Left')]:
    for thigh in [f'R24 {side} | rear thigh wrap',f'{label} L3 | thigh side armor',f'R24 {side} | thigh access 3.92']:
        for shin in [f'R24 {side} | rear calf wrap',f'R24 {side} | calf service hatch']:pairs.append((thigh,shin))
report=[]
def tree(name,dg):
    o=bpy.data.objects[name].evaluated_get(dg);me=o.to_mesh()
    t=BVHTree.FromPolygons([o.matrix_world@v.co for v in me.vertices],[tuple(p.vertices) for p in me.polygons]);o.to_mesh_clear();return t
for f in range(1,c['frames']+1,max(1,c['frames']//8)):
    bpy.context.scene.frame_set(f);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    names=set(links+obstacles+[n for pair in pairs for n in pair]);ts={n:tree(n,dg) for n in names}
    hits=[]
    for a,b in pairs+list(itertools.product(links,obstacles)):
        count=len(ts[a].overlap(ts[b]))
        if count:hits.append([a,b,count])
    overreach=[]
    for label in ['shoulder','elbow','wrist']:
        solver=bpy.data.objects['R36 | '+label+' solver']
        if solver['distance']>solver['length']*solver['scale']+1e-5:overreach.append(label)
    report.append({'frame':f,'evaluated_surface_contacts':hits,'feed_overreach':overreach})
ctx['verification'][c['slug']]['evaluated_checks']=report
print(json.dumps({'clip':c['label'],'checks':report}))
