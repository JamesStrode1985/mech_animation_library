"""Package Dance Party for the offline gallery. Requires Pillow."""
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
def main():
    clip=json.loads((ROOT/'build/dance_action.json').read_text())
    report=json.loads((ROOT/'data/verification/dance_party.json').read_text())
    assert not report['intersections'] and report['minimum_body_surface_z']>=0
    assert report['root_error']<1e-6 and report['loop_seam']<1e-6
    assert report['maximum_planted_foot_slide']<1e-4
    frames=[]
    for f in range(1,193,2):
        with Image.open(ROOT/'build/dance_previews/46_dance_party'/f'frame_{f:03d}.png') as image:
            im=image.convert('RGB');im.thumbnail((540,480),Image.Resampling.LANCZOS);frames.append(im.copy())
    atlas=Image.new('RGB',(900,160))
    for j,k in enumerate([3,27,51,75,87]):
        im=frames[k].copy();im.thumbnail((180,160));atlas.paste(im,(j*180,0))
    palette=atlas.quantize(colors=224,method=Image.Quantize.MEDIANCUT)
    encoded=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
    durations=[round((i+1)*100/12)*10-round(i*100/12)*10 for i in range(len(frames))]
    target=ROOT/'assets/animations/46_dance_party.gif'
    encoded[0].save(target,save_all=True,append_images=encoded[1:],duration=durations,loop=0,optimize=True,disposal=1)
    with Image.open(target) as im:assert im.n_frames==96
    path=ROOT/'data/manifest.json';data=json.loads(path.read_text(encoding='utf-8'))
    data['clips']=[c for c in data['clips'] if c['action']!=clip['action']]+[clip]
    data['clips'].sort(key=lambda c:int(c['label'].split()[0]))
    if not any(g['id']=='emotes' for g in data['gallery_groups']):data['gallery_groups'].append({'id':'emotes','title':'Emotes'})
    data['dance_party_verification']=report
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    readme=ROOT/'README.md';readme.write_text(readme.read_text(encoding='utf-8').replace('45 in-place','46 in-place').replace('01–45','01–46'),encoding='utf-8')
    print('Packaged 46 Dance Party: 96 preview frames, 8 seconds, 120 BPM.')
if __name__=='__main__':main()
