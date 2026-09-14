"""Package rendered T1 frames and verified inventory. Requires Pillow.

Run after Blender renders finish. --available packages finished clips for review
without publishing the manifest. Source Blender Actions remain in the open file.
"""
import argparse
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build/t1_library'
OUTPUT = ROOT / 'assets/animations/t1-artillery-walker'


def package(available=False):
    specs = json.loads((BUILD/'specs.json').read_text())
    OUTPUT.mkdir(parents=True, exist_ok=True)
    reports = []
    for spec in specs:
        n, step = spec['duration_frames'], spec['preview_frame_step']
        frames = list(range(1,n+1,step))
        if not spec['loop']:
            frames.append(n+1)
        paths = [BUILD/spec['slug']/f'frame_{f:04d}.png' for f in frames]
        if available and not all(p.exists() for p in paths):
            continue
        if not all(p.exists() for p in paths):
            raise ValueError(f"Incomplete render: {spec['label']}")
        report = json.loads((BUILD/'verification'/f"{spec['slug']}.json").read_text())
        assert report['max_ik_error'] < .001, report
        assert report['root_error'] < .000001, report
        assert report['min_sampled_sole_clearance'] > -.005, report
        if spec['loop']:
            assert report['loop_seam_error'] < .0001, report
        destination = OUTPUT/f"{spec['slug']}.gif"
        if not destination.exists() or destination.stat().st_mtime < max(p.stat().st_mtime for p in paths):
            images = []
            for path in paths:
                with Image.open(path) as im:
                    images.append(im.convert('RGB'))
            atlas = Image.new('RGB', (160*len(images),144))
            for i,im in enumerate(images):
                atlas.paste(im.resize((160,144)),(i*160,0))
            palette=atlas.quantize(colors=192)
            indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in images]
            # GIF delays are 10 ms units: cumulative rounding preserves 24 fps timing.
            ends=frames[1:]+[n+1]
            delays=[round((b-1)/24*100)*10-round((a-1)/24*100)*10 for a,b in zip(frames,ends)]
            if not spec['loop']: delays[-1]=750
            indexed[0].save(destination,save_all=True,append_images=indexed[1:],duration=delays,loop=0,disposal=2,optimize=False)
        with Image.open(destination) as gif:
            assert gif.n_frames > 1, f"Static preview: {destination}"
            report['preview_frames'] = gif.n_frames
            report['preview_resolution'] = list(gif.size)
        reports.append(report)
        print('Packaged',spec['label'])
    if available:
        return
    assert len(reports) == 47
    source=json.loads((ROOT/'data/manifest.json').read_text())
    manifest=dict(mech_id='t1-artillery-walker',revision=max(c['revision'] for c in specs),gallery_groups=source['gallery_groups'],clips=specs,
                  verification_report='data/verification/t1_library.json',
                  rig='T1 | ANIMATION RIG',source_scene='T1 ARTILLERY WALKER',
                  notes='47 quadruped adaptations. Source model and editable Actions are maintained in Blender, outside this repository.')
    (ROOT/'data/mechs/t1-artillery-walker.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    report=dict(mech='T1 Artillery Walker',fps=24,actions=47,
                checks='All integer frames: endpoint IK, sampled sole clearance, stationary root; loop endpoints. Sampled model bounds for framing.',
                limitations='Not an exhaustive surface collision or physics simulation. Runtime terrain IK and controller travel are required. Revised death clips use planted feet and folding legs.',
                clips=reports)
    metrics = BUILD/'revision2_metrics.json'
    if metrics.exists():
        report['revision_2_motion_samples'] = json.loads(metrics.read_text())
    (ROOT/'data/verification/t1_library.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--available',action='store_true')
    package(parser.parse_args().available)
