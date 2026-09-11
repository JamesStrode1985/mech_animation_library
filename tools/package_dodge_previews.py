"""Package the dodge render frames and controller metadata. Requires Pillow."""
import json, argparse
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--only',help='Only re-encode this source slug; metadata still includes all four clips.')
    args=parser.parse_args()
    clips=json.loads((ROOT/'build/dodge_actions.json').read_text(encoding='utf-8'))
    mp=ROOT/'data/manifest.json';data=json.loads(mp.read_text(encoding='utf-8'))
    verification=json.loads((ROOT/'data/verification/dodge_animations.json').read_text(encoding='utf-8'))
    for report in verification['reports']:
        assert not report['intersections'],report['clip']
        assert report['root_error']<1e-5 and report['start_end_pose_delta']<1e-5
        assert report['minimum_both_feet_airborne_clearance']>0
        assert report['minimum_surface_z_with_controller']>=0
        assert report['maximum_landing_foot_slide_per_frame']<1e-4
    for clip in clips:
        if args.only and clip['slug']!=args.only:continue
        frames=[]
        for f in range(1,clip['duration_frames']+2):
            path=ROOT/'build/dodge_previews'/clip['slug']/f'frame_{f:03d}.png'
            with Image.open(path) as source:
                im=source.convert('RGB');im.thumbnail((540,480),Image.Resampling.LANCZOS);frames.append(im.copy())
        atlas=Image.new('RGB',(900,160))
        for j,k in enumerate([0,6,11,17,30]):
            thumb=frames[k].copy();thumb.thumbnail((180,160));atlas.paste(thumb,(j*180,0))
        palette=atlas.quantize(colors=224,method=Image.Quantize.MEDIANCUT)
        encoded=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
        durations=[40 if i%6!=5 else 50 for i in range(len(encoded))];durations[-1]+=600
        path=ROOT/'assets/animations'/(clip['slug']+'.gif')
        encoded[0].save(path,save_all=True,append_images=encoded[1:],duration=durations,loop=0,optimize=True,disposal=1)
        with Image.open(path) as check:
            assert check.n_frames>=25
            print(f'{path.name}: {check.n_frames} encoded frames')
    incoming={c['action'] for c in clips}
    data['clips']=[c for c in data['clips'] if c['action'] not in incoming]+clips
    data['clips'].sort(key=lambda c:int(c['label'].split()[0]))
    if not any(g['id']=='dodges' for g in data['gallery_groups']):data['gallery_groups'].append({'id':'dodges','title':'Dodge leaps'})
    data['dodge_animations_verification']=verification
    data['dodge_controller_note']='Apply each clip controller_samples translation relative to dodge start, rotated by the character heading. Gameplay roots remain zero. Positive X is mech-left; negative Y is forward; positive Z is up. Do not also extract the preview movement as root motion.'
    mp.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    rp=ROOT/'README.md';text=rp.read_text(encoding='utf-8').replace('41 in-place mech animation previews','45 in-place mech animation previews').replace('numbered 01–41','numbered 01–45');rp.write_text(text,encoding='utf-8')
    gp=ROOT/'docs/animation-guide.md';text=gp.read_text(encoding='utf-8')
    section='''### Dodge leaps

| Gallery clip | Original Blender Action | Frames | Travel / peak height (model units) |
|---|---|---:|---:|
| 42 Forward Shoulder Ram | HC ANIM \\| 42 Dodge Forward | 1–31 | 2.35 / 0.12 |
| 43 Dodge Backward | HC ANIM \\| 43 Dodge Backward | 1–31 | 1.90 / 0.38 |
| 44 Dodge Left | HC ANIM \\| 44 Dodge Left | 1–31 | 2.10 / 0.42 |
| 45 Dodge Right | HC ANIM \\| 45 Dodge Right | 1–31 | 2.10 / 0.42 |

Each clip lasts 1.25 seconds at 24 fps and does not loop. Dodges 43–45 anticipate at frame 1, take off at frame 7, reach the apex at frame 12, land the lead foot at frame 17 and trailing foot at frame 19, finish braking at frame 23, and return to ready at frame 31. The initial and final poses match. Left and right are from the mech's perspective; the hull keeps facing forward during lateral dodges.

Clip 42 loads and drives from the left leg while the right foot swings forward. The left foot remains planted through frame 10; the right foot catches at frame 15. The hull then turns a further 22 degrees into the right-shoulder impact at frame 18, with the right foot planted throughout the follow-through. The left foot recovers at frame 21, braking ends at frame 25, and the mech returns to ready at frame 31. The attack window is frames 15–20. These are animation cues; the game controls hit detection, damage, and interruption. The original `HC ANIM | 42 Dodge Forward` identifier and `42_dodge_forward.gif` filename remain stable. The other three dodges are unchanged.

`CTRL.root` and `CTRL.death_fall` stay neutral. Apply `controller_samples` from each manifest clip relative to the dodge start and rotate that translation by the character's heading. In model coordinates, forward is -Y, backward +Y, left +X, and right -X. The samples include horizontal travel, vertical trajectory and foot contact states. They are also stored in the source Action's `Controller trajectory` custom property. Landing foot motion counters the final controller deceleration, so using the supplied curve preserves planted contacts. Movement over arbitrary terrain still needs the game controller's collision handling and ground adaptation.

The GIFs simulate controller travel using temporary render-only Actions and a reference grid. They repeat for review; the gameplay Actions do not loop. Author stamina cost, invulnerability, interruption, and recovery-cancel windows in the game controller using the animation markers; these clips provide animation and movement data, not combat logic.

All 124 frames passed stationary-root, ground-clearance, airborne-foot, planted-landing, joint-attachment, neutral-endpoint, and specified armor-pair checks. See [dodge verification](../data/verification/dodge_animations.json) for measurements and scope.

Creation, rendering and verification scripts are in `tools/blender_dodge_animations.py`, `tools/blender_render_dodges.py`, and `tools/blender_verify_dodges.py`. They require the existing live HELLCAT rig and its animation/geometry contexts. Supply `PROJECT_ROOT` through Blender MCP; intermediates go in ignored `build/`. Package with `python tools/package_dodge_previews.py`, then run the gallery builders and validator.

'''
    if '### Dodge leaps' not in text:text=text.replace('## Validation',section+'## Validation')
    gp.write_text(text,encoding='utf-8')


if __name__=='__main__':
    main()
