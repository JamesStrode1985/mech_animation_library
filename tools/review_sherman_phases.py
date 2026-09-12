"""Create ignored four-pose review sheets from completed Sherman render sequences."""
import json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
specs=json.loads((ROOT/'build/sherman_full/specs.json').read_text())
completed=[]
for spec in specs:
    expected=list(range(1,spec['duration_frames']+1,spec['preview_frame_step']))
    if not spec['loop']:expected.append(spec['duration_frames']+1)
    folder=ROOT/'build/sherman_full'/spec['slug']
    if not all((folder/f'frame_{f:03d}.png').exists() for f in expected):continue
    completed.append((spec,folder,expected))
for start in range(0,len(completed),8):
    batch=completed[start:start+8];sheet=Image.new('RGB',(4*224,len(batch)*278),'#151a1d');draw=ImageDraw.Draw(sheet)
    for row,(spec,folder,frames) in enumerate(batch):
        requested=None;n=spec['number']
        if 9<=n<=12:
            markers={m['name']:m['frame'] for m in spec['markers']}
            requested=[1,markers['Takeoff']+2,markers['Apex'],next(v for k,v in markers.items() if k.startswith('Land'))+6]
        if n==35:requested=[1,11,13,spec['duration_frames']+1]
        if 36<=n<=38:requested=[1,21,57,spec['duration_frames']+1]
        if n==42:requested=[5,15,24,spec['duration_frames']+1]
        if 43<=n<=45:requested=[1,15,27,spec['duration_frames']+1]
        indices=[min(range(len(frames)),key=lambda i:abs(frames[i]-f)) for f in requested] if requested else [0,len(frames)//3,2*len(frames)//3,len(frames)-1]
        for column,i in enumerate(indices):
            with Image.open(folder/f'frame_{frames[i]:03d}.png') as im:sheet.paste(im.resize((224,252)),(column*224,row*278))
            draw.text((column*224+4,row*278+254),spec['label']+' / '+str(frames[i]),fill='white')
    path=ROOT/'build/sherman_full'/f'phase_review_{start//8+1}.png';sheet.save(path);print(path)
print(f'{len(completed)} complete sequences reviewed in sheets.')
