"""Package rendered death previews and update the manifest. Requires Pillow."""
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]


def main():
    clips=json.loads((ROOT/'build/death_actions.json').read_text(encoding='utf-8'))
    manifest_path=ROOT/'data/manifest.json'
    data=json.loads(manifest_path.read_text(encoding='utf-8'))
    verification=json.loads((ROOT/'data/verification/death_animations.json').read_text(encoding='utf-8'))
    for report in verification['reports']:
        assert not report['intersections'], report['clip']
        assert report['root_error']<1e-5 and report['minimum_conservative_surface_z']>=0
        assert report['max_joint_attachment_error']<1e-4 and report['settled_matrix_delta']<1e-5
    for clip in clips:
        folder=ROOT/'build/death_previews'/clip['slug']
        paths=[folder/f'frame_{f:03d}.png' for f in range(1,clip['duration_frames']+2,2)]
        assert all(p.is_file() for p in paths), clip['label']
        frames=[]
        for path in paths:
            with Image.open(path) as im:
                im=im.convert('RGB');im.thumbnail((540,480),Image.Resampling.LANCZOS);frames.append(im.copy())
        samples=[0,len(frames)//4,len(frames)//2,3*len(frames)//4,len(frames)-1]
        atlas=Image.new('RGB',(180*len(samples),160))
        for i,k in enumerate(samples):
            thumb=frames[k].copy();thumb.thumbnail((180,160));atlas.paste(thumb,(180*i,0))
        palette=atlas.quantize(colors=224,method=Image.Quantize.MEDIANCUT)
        encoded=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
        durations=[80 if i%3!=2 else 90 for i in range(len(frames))];durations[-1]+=1200
        out=ROOT/'assets/animations'/(clip['slug']+'.gif')
        encoded[0].save(out,save_all=True,append_images=encoded[1:],duration=durations,loop=0,optimize=True,disposal=1)
        with Image.open(out) as check:
            assert check.n_frames>10
            print(f'{out.name}: {check.n_frames} encoded frames')
    incoming={c['action'] for c in clips}
    data['clips']=[c for c in data['clips'] if c['action'] not in incoming]+clips
    data['clips'].sort(key=lambda c:int(c['label'].split()[0]))
    if not any(g['id']=='deaths' for g in data['gallery_groups']):
        data['gallery_groups'].append({'id':'deaths','title':'Death animations'})
    data['death_animations_verification']=verification
    data['death_playback']='Non-looping local corpse collapses. Keep CTRL.root stationary; bake CTRL.death_fall and evaluated mechanical bones. Stop locomotion and hold the final frame, or transition to an engine ragdoll explicitly.'
    manifest_path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    readme=ROOT/'README.md';text=readme.read_text(encoding='utf-8').replace('38 in-place mech animation previews','41 in-place mech animation previews').replace('numbered 01–38','numbered 01–41');readme.write_text(text,encoding='utf-8')
    guide=ROOT/'docs/animation-guide.md';text=guide.read_text(encoding='utf-8')
    section='''### Death animations

| Gallery clip | Original Blender Action | Frames | Loop |
|---|---|---:|---|
| 39 Death Forward Collapse | HC ANIM \\| 39 Death Forward Collapse | 1–109 | No |
| 40 Death Backward Fall | HC ANIM \\| 40 Death Backward Fall | 1–101 | No |
| 41 Death Side Collapse | HC ANIM \\| 41 Death Side Collapse | 1–117 | No |

Play once, stop locomotion, and hold the last frame. `CTRL.root` stays fixed; `CTRL.death_fall` supplies the local whole-body collapse beneath it. The additional control is neutral in the existing 38 Actions. Bake its motion with the evaluated deform and mechanical bones when exporting. These are authored death motions, not a runtime ragdoll simulation.

Forward collapse buckles the knees and twists the hull before impact at frame 57; backward fall impacts at frame 47; sideways collapse follows a failed recovery step and impacts at frame 67. Each has Fatal hit, Loss of balance, Ground impact, and Settled markers. The GIF previews repeat for review, while the Actions themselves are non-looping.

All 327 frames were checked for stationary gameplay roots, conservative skinned-vertex ground clearance, joint attachment, hinge alignment, and a stable final hold. Sampled collision checks cover 86 poses for the listed armor and barrel pairs. See the [death verification report](../data/verification/death_animations.json) for the scope and measurements.

The project includes the new Blender creation, render, and verification scripts under `tools/blender_*deaths.py` and `tools/blender_death_animations.py`. They require the existing live HELLCAT rig and animation build context; they do not recreate the source model. Supply `PROJECT_ROOT` when running through Blender MCP. Generated preview frames and packaging metadata stay in ignored `build/`. Package them with `python tools/package_death_previews.py`, then run the standard gallery builders and validator.

'''
    if '### Death animations' not in text:text=text.replace('## Validation',section+'## Validation')
    guide.write_text(text,encoding='utf-8')


if __name__=='__main__':
    main()
