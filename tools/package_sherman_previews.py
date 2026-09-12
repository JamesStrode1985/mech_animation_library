"""Package the three Sherman locomotion previews; requires Pillow."""
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

def main():
    configs=json.loads((ROOT/'build/sherman_locomotion/configs.json').read_text(encoding='utf-8'))
    report=json.loads((ROOT/'data/verification/sherman_locomotion.json').read_text(encoding='utf-8'))
    clips=[]
    for c in configs:
        check=report['clips'][c['slug']]
        assert check['max_arm_centerline_error']<1e-4
        assert not check['new_proxy_contacts'] and check['invalid_driver_count']==0
        assert check['max_ik_error']<.001 and check['min_sole_z']>=0 and check['loop_matrix_error']<1e-5
        assert all(abs(v)<1e-7 for row in check['kinematics'] for v in row['root_translation'])
        assert all(not x['evaluated_surface_contacts'] and not x['feed_overreach'] for x in check['evaluated_checks'])
        frames=[]
        for f in range(1,c['frames']+1):
            with Image.open(ROOT/'build/sherman_locomotion'/c['slug']/f'frame_{f:03d}.png') as image:
                frames.append(image.convert('RGB'))
        atlas=Image.new('RGB',(640*4,720))
        for i in range(4):atlas.paste(frames[i*len(frames)//4],(640*i,0))
        palette=atlas.quantize(colors=224,method=Image.Quantize.MEDIANCUT)
        encoded=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
        durations=[round((i+1)*100/24)*10-round(i*100/24)*10 for i in range(len(frames))]
        target=ROOT/'assets/animations/sherman-walker'/(c['slug']+'.gif')
        encoded[0].save(target,save_all=True,append_images=encoded[1:],duration=durations,loop=0,optimize=True,disposal=1)
        with Image.open(target) as gif:
            assert gif.n_frames==c['frames']
            total=0
            for i in range(gif.n_frames):gif.seek(i);total+=gif.info['duration']
            assert abs(total-c['frames']*1000/24)<=5
        clips.append(dict(label=c['label'],source_label=c['label'],action=c['action'],slug=c['slug'],
            duration_frames=c['frames'],fps=24,loop=True,category='Heavy locomotion',gallery_group='forward',
            nominal_speed_units_per_s=c['stride']*1.1/(c['duty']*c['frames']/24),
            controller_preview_travel=False,preview_frame_step=1,revision='Sherman locomotion 1',
            support_fraction=c['duty'],markers=[{'name':'L contact','frame':1},{'name':'R contact','frame':1+c['frames']//2}]))
        print(f"Packaged {c['label']}: {len(frames)} frames, {total} ms")
    manifest=dict(mech_id='sherman-walker',revision=1,gallery_groups=[dict(id='forward',title='Forward locomotion')],
        clips=clips,verification_report='data/verification/sherman_locomotion.json')
    (ROOT/'data/mechs/sherman-walker.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
