"""Package verified hover render sequences; --available does not register/publish the library."""
import argparse,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];BUILD=ROOT/'build/hover_library';OUTPUT=ROOT/'assets/animations/hover-tank'
def package(available=False):
 specs=json.loads((BUILD/'specs.json').read_text());OUTPUT.mkdir(parents=True,exist_ok=True);reports=[]
 for spec in specs:
  n=spec['duration_frames'];frames=list(range(1,n+1,spec['preview_frame_step']))
  if not spec['loop']:frames.append(n+1)
  paths=[BUILD/spec['slug']/f'frame_{f:04d}.png' for f in frames]
  if available and not all(p.exists() for p in paths):continue
  assert all(p.exists() for p in paths),spec['label']
  report=json.loads((BUILD/'verification'/(spec['slug']+'.json')).read_text());assert report['root_error']<1e-6;assert report['min_sampled_clearance']>=-.005
  if spec['loop']:assert report['loop_seam_error']<1e-4
  dest=OUTPUT/(spec['slug']+'.gif')
  if not dest.exists() or dest.stat().st_mtime<max(p.stat().st_mtime for p in paths):
   images=[]
   for p in paths:
    with Image.open(p) as im:images.append(im.convert('RGB'))
   atlas=Image.new('RGB',(128*len(images),114))
   for i,im in enumerate(images):atlas.paste(im.resize((128,114)),(i*128,0))
   pal=atlas.quantize(colors=224);indexed=[im.quantize(palette=pal,dither=Image.Dither.NONE) for im in images]
   ends=frames[1:]+[n+1];delays=[round((b-1)/24*100)*10-round((a-1)/24*100)*10 for a,b in zip(frames,ends)]
   if not spec['loop']:delays[-1]=850
   indexed[0].save(dest,save_all=True,append_images=indexed[1:],duration=delays,loop=0,disposal=2,optimize=False)
  with Image.open(dest) as gif:
   assert gif.n_frames>1,spec['label'];report['preview_frames']=gif.n_frames;report['preview_resolution']=list(gif.size)
  reports.append(report);print('Packaged',spec['label'])
 if available:return
 assert len(reports)==47
 groups=json.loads((ROOT/'data/manifest.json').read_text())['gallery_groups']
 for group in groups:
  if group['id']=='dodges':group['title']='Boost dodges and ram'
  if group['id']=='lateral':group['title']='Slides and strafing'
 manifest=dict(mech_id='hover-tank',revision=1,gallery_groups=groups,clips=specs,verification_report='data/verification/hover_library.json',rig='HT-01 | RIG',source_scene='HoverTank1',notes='47 hover-specific adaptations; editable model and Actions maintained separately in Blender.')
 (ROOT/'data/mechs/hover-tank.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (ROOT/'data/verification/hover_library.json').write_text(json.dumps(dict(mech='HT-01 Hover Tank',fps=24,actions=47,checks='Every integer frame: stationary ROOT, sampled underside clearance, loop endpoints; rigid skin previously verified.',limitations='Not an exhaustive surface collision or physical suspension simulation. Preview ground travel and flashes are not gameplay root motion. Runtime hover terrain sensing remains required.',clips=reports),indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--available',action='store_true');package(p.parse_args().available)
