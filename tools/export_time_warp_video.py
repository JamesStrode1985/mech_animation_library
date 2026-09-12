"""Mux the soundtrack-cued Blender frames with a user-supplied audio excerpt.
Usage: python tools/export_time_warp_video.py AUDIO_PATH
Requires imageio-ffmpeg and av in build/media_runtime; outputs ignored dist/.
"""
import sys,json,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'build/media_runtime'))
import imageio_ffmpeg
import av
import numpy as np

def mono(path):
    chunks=[]
    with av.open(str(path)) as container:
        resampler=av.AudioResampler(format='fltp',layout='mono',rate=16000)
        for frame in container.decode(audio=0):
            for output in resampler.resample(frame):chunks.append(output.to_ndarray().reshape(-1))
        for output in resampler.resample(None):chunks.append(output.to_ndarray().reshape(-1))
    return np.concatenate(chunks)

def main():
    audio=Path(sys.argv[1]).resolve();assert audio.is_file()
    build=ROOT/'build/time_warp_video';sync=json.loads((build/'sync.json').read_text())
    checks=json.loads((build/'pose_verification.json').read_text())
    assert checks['minimum_body_floor_z']>=0 and not checks['pod_hull_intersections']
    count=sync['frame_count'];fps=sync['fps'];duration=count/fps
    for frame in range(1,count+1):assert (build/'frames'/f'frame_{frame:04d}.png').is_file(),frame
    out=ROOT/'dist';out.mkdir(exist_ok=True);video=out/'47_time_warp_synced.mp4'
    command=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','warning','-y',
             '-framerate',str(fps),'-start_number','1','-i',str(build/'frames/frame_%04d.png'),
             '-ss',str(sync['audio_start_seconds']),'-t',str(duration),'-i',str(audio),
             '-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','18',
             '-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',
             '-af',f'afade=t=in:st=0:d=0.04,afade=t=out:st={duration-.18}:d=0.18',
             '-t',str(duration),'-movflags','+faststart',str(video)]
    subprocess.run(command,check=True)
    with av.open(str(video)) as container:
        stream=container.streams.video[0];video_info={'width':stream.width,'height':stream.height,'fps':float(stream.average_rate),'codec':stream.codec_context.name}
        decoded=sum(1 for _ in container.decode(video=0))
    assert decoded==count and video_info['fps']==fps
    produced=mono(video);original=mono(audio)
    start=round(sync['audio_start_seconds']*16000);reference=original[start:start+len(produced)]
    # Check a central span: AAC is lossy, but the excerpt should remain closely aligned.
    a=produced[16000:-16000];b=reference[16000:len(produced)-16000]
    n=min(len(a),len(b));correlation=float(np.corrcoef(a[:n],b[:n])[0,1])
    assert correlation>.90,('Unexpected audio offset or encoding issue',correlation)
    report={'file':video.name,'duration_seconds':duration,'video':video_info,'decoded_frames':decoded,
            'audio_duration_seconds':len(produced)/16000,'audio_rms':float(np.sqrt(np.mean(produced**2))),
            'decoded_audio_correlation_to_selected_source_excerpt':correlation,
            'source_audio_sha256':hashlib.sha256(audio.read_bytes()).hexdigest(),
            'sync':sync,'pose_verification':checks}
    (build/'export_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
