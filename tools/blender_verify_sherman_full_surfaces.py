"""Reuse the selected evaluated armor/feed audit for one full-library Action."""
from pathlib import Path
script=(Path(PROJECT_ROOT)/'tools/blender_verify_sherman_surfaces.py').read_text(encoding='utf-8-sig')
script=script.replace("c=ctx['configs'][VERIFY_CLIP];", "lib=bpy.app.driver_namespace['SW full library']; c=dict(next(s for s in lib['specs'] if s['number']==VERIFY_NUMBER));c['frames']=c['duration_frames'];")
script=script.replace("ctx['verification'][c['slug']]['evaluated_checks']=report", "out=ROOT/'build/sherman_full/surfaces';out.mkdir(parents=True,exist_ok=True);(out/(c['slug']+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')")
exec(compile(script,'sherman_evaluated_surfaces','exec'))
