"""Package revised terrain previews and checks. Requires Pillow; run from any directory."""
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

def main():
    path=ROOT/'data/manifest.json';manifest=json.loads(path.read_text(encoding='utf-8'))
    clips=[c for c in manifest['clips'] if c.get('terrain_mode') in ('rough','uphill','downhill')]
    reports=[]
    for clip in clips:
        source=clip['source_label'].lower().replace(' ','_')
        report=json.loads((ROOT/'build/terrain_verification'/f'{source}.json').read_text())
        assert not report['intersections'],clip['label']
        assert report['minimum_surface_clearance']>=0,clip['label']
        assert report['planted_clearance_error']<.001,clip['label']
        assert report['root_translation_max']<1e-6 and report['loop_seam_max']<1e-5,clip['label']
        reports.append(report)
        frames=[]
        for frame in range(1,clip['duration_frames']+1,2):
            with Image.open(ROOT/'build/terrain_previews'/source/f'frame_{frame:03d}.png') as im:
                rgb=im.convert('RGB');rgb.thumbnail((480,540),Image.Resampling.LANCZOS);frames.append(rgb.copy())
        atlas=Image.new('RGB',(800,180))
        for j in range(5):
            im=frames[min(len(frames)-1,j*len(frames)//5)].copy();im.thumbnail((160,180));atlas.paste(im,(j*160,0))
        palette=atlas.quantize(colors=224,method=Image.Quantize.MEDIANCUT)
        encoded=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
        # 12 rendered frames/s, sampled from the unchanged 24 fps Actions.
        durations=[round((i+1)*100/12)*10-round(i*100/12)*10 for i in range(len(frames))]
        output=ROOT/'assets/animations'/f"{clip['slug']}.gif"
        encoded[0].save(output,save_all=True,append_images=encoded[1:],duration=durations,loop=0,optimize=True,disposal=1)
        with Image.open(output) as check:
            assert check.n_frames==len(frames)
        clip['reference_slope_degrees']={'rough':0,'uphill':22,'downhill':-22}[clip['terrain_mode']]
        clip['revision']='Rough terrain 3x and steep 22 degree slopes'
        if clip['terrain_mode']=='rough':clip['roughness_amplitude_multiplier']=3
        print(f"{clip['label']}: {len(frames)} preview frames")
    report={'reports':reports,'scope':'All 681 Action frames: stationary roots, cached sole clearance against the analytic reference terrain, planted surface contact, foot targets, mechanical hinge axes, loop endpoints, and selected thigh/knee/load-frame/hull/pod/shin/instep/barrel mesh pairs. Not an exhaustive every-object collision check. Rendered terrain is a sampled approximation of the analytic surface.'}
    (ROOT/'data/verification/terrain_revision.json').write_text(json.dumps(report,indent=2)+'\n')
    manifest['terrain_revision_verification']=report
    path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
