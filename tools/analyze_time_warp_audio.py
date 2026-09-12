"""Find cue timestamps in a user-supplied recording using local faster-whisper.
Usage: python tools/analyze_time_warp_audio.py AUDIO_PATH
Install faster-whisper and imageio-ffmpeg into build/media_runtime first.
Model downloads are stored in ignored build/asr_models. Audio never leaves this machine.
"""
import sys,json,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'build/media_runtime'))
from faster_whisper import WhisperModel

def main():
    parser=argparse.ArgumentParser();parser.add_argument('audio');parser.add_argument('--model',default='base.en');parser.add_argument('--start',type=float,default=0);parser.add_argument('--end',type=float);args=parser.parse_args()
    from faster_whisper.audio import decode_audio
    audio=decode_audio(args.audio,sampling_rate=16000)
    audio=audio[int(args.start*16000):int(args.end*16000) if args.end else None]
    model=WhisperModel(args.model,device='cpu',compute_type='int8',cpu_threads=8,download_root=str(ROOT/'build/asr_models'))
    segments,info=model.transcribe(audio,language='en',beam_size=5,word_timestamps=True,vad_filter=False,condition_on_previous_text=False)
    rows=[]
    for segment in segments:
        row={'start':segment.start+args.start,'end':segment.end+args.start,'text':segment.text,'words':[{'start':w.start+args.start,'end':w.end+args.start,'word':w.word,'probability':w.probability} for w in segment.words]}
        rows.append(row)
        if any(word in segment.text.lower() for word in ['jump','step','knees','thrust','hips','left','right']):
            print(json.dumps({'start':row['start'],'end':row['end'],'cues':[w for w in row['words'] if w['word'].lower().strip(' ,.?!') in ['jump','step','knees','thrust','hips','left','right']]}),flush=True)
    out=ROOT/'build/time_warp_video';out.mkdir(parents=True,exist_ok=True)
    target=out/('transcript_excerpt.json' if args.start else 'transcript.json')
    target.write_text(json.dumps({'duration':info.duration,'segments':rows},indent=2),encoding='utf-8')
    print(json.dumps({'duration':info.duration,'segments':len(rows),'transcript':str(target)}))
if __name__=='__main__':main()
