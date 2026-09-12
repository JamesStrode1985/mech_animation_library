"""Publish only verified, rendered Sherman counterparts; requires Pillow."""
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

def main():
    manifest_path=ROOT/'data/mechs/sherman-walker.json'
    manifest=json.loads(manifest_path.read_text())
    original=json.loads((ROOT/'data/manifest.json').read_text())
    specs=json.loads((ROOT/'build/sherman_full/specs.json').read_text())
    clips=manifest['clips'][:3];reports={}
    for clip,source in zip(clips,original['clips'][:3]):clip['hellcat_source_action']=source['action']
    fields=['label','source_label','action','slug','duration_frames','fps','loop','category','gallery_group','markers','revision','preview_frame_step','controller_preview_travel','hellcat_source_action','nominal_speed_units_per_s','terrain_mode','terrain_period','timing_note']
    for spec in specs:
        slug=spec['slug'];check=json.loads((ROOT/'build/sherman_full/verification'/(slug+'.json')).read_text())
        assert check['frames']==spec['duration_frames'] and check['action']==spec['action'], (slug,'report mismatch')
        assert all(1<=m['frame']<=spec['duration_frames']+1 for m in spec['markers']), (slug,'marker range')
        assert check['max_ik']<.001 and check['min_floor']>=0, (slug,'feet')
        assert check['max_arm_error']<1e-4 and check['root_error']<1e-6, (slug,'alignment/root')
        assert not check['contacts'] and check['invalid_drivers']==0, (slug,'contacts/drivers')
        assert not check['loop'] or check['seam']<1e-4, (slug,'loop')
        surface=ROOT/'build/sherman_full/surfaces'/(slug+'.json')
        if surface.exists():
            check['evaluated_checks']=json.loads(surface.read_text())
            assert all(not s['evaluated_surface_contacts'] and not s['feed_overreach'] for s in check['evaluated_checks']), (slug,'evaluated surfaces')
        reports[slug]=check
        frame_numbers=list(range(1,spec['duration_frames']+1,2))
        if not spec['loop']:frame_numbers.append(spec['duration_frames']+1)
        frames=[]
        for f in frame_numbers:
            with Image.open(ROOT/'build/sherman_full'/slug/f'frame_{f:03d}.png') as im:frames.append(im.convert('RGB'))
        atlas=Image.new('RGB',(640*4,720))
        for i in range(4):atlas.paste(frames[i*(len(frames)-1)//3],(640*i,0))
        palette=atlas.quantize(colors=224,method=Image.Quantize.MEDIANCUT)
        encoded=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
        durations=[round((i+1)*100/12)*10-round(i*100/12)*10 for i in range(len(frames))]
        if not spec['loop']:durations[-1]=700
        target=ROOT/'assets/animations/sherman-walker'/(slug+'.gif')
        encoded[0].save(target,save_all=True,append_images=encoded[1:],duration=durations,loop=0,optimize=True,disposal=1)
        with Image.open(target) as gif:
            total=0
            for i in range(gif.n_frames):gif.seek(i);total+=gif.info['duration']
            assert abs(total-sum(durations))<=10,(slug,total,sum(durations))
        c={k:spec[k] for k in fields if k in spec}
        c['preview_fps']=12
        if not c['loop']:c['preview_end_hold_ms']=700
        if c.get('terrain_mode'):
            c['reference_slope_degrees']=22 if c['terrain_mode']!='rough' else 0
            c['terrain_use']='Authored reference surface; use runtime foot IK for actual game ground.'
        clips.append(c)
        print(f"Packaged {spec['label']}: {len(frames)} images, {total} ms")
    assert len(clips)==len(original['clips'])==47
    assert [c['label'] for c in clips]==[c['label'] for c in original['clips']]
    result=dict(mech_id='sherman-walker',revision=2,gallery_groups=original['gallery_groups'],clips=clips,verification_report='data/verification/sherman_full_library.json')
    verification=dict(scope='All integer frames: IK, sole clearance, root and straight arm; sampled rigid armor regions and selected evaluated feed/surface poses. Not exhaustive collision certification.',base_locomotion_report='data/verification/sherman_locomotion.json',clips=reports)
    (ROOT/'data/verification/sherman_full_library.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf-8')
    manifest_path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
