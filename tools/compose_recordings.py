"""Compose the five user-recorded Ade clips without uploading raw recordings.

Requires Python 3, imageio-ffmpeg. Run with --source-dir and --output-dir.
Output uses only the video stream; source microphone audio is excluded.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import tempfile
import imageio_ffmpeg

SOURCES = [
    '64258107a84437fbf7bd966dcf19be0a.mp4',
    'cbda065fffc6fa7e5630c96733cff944.mp4',
    'e78beafb926601e87bcd04d7a632e5ea.mp4',
    '1a6acea2b9c36af025bd6a591eebd389.mp4',
    'a8b3404dcc6e5f77230792382db4ada6.mp4',
]
# Source index, start seconds, selected duration. All playback remains 1x.
EDITS = {
    'ade-recording-highlight-10s.mp4': [(0,.5,2),(4,.4,2),(2,3,2),(1,.6,2),(3,.4,2)],
    'ade-recording-full.mp4': [(0,.4,14.4),(4,.2,4.9),(2,.4,20),(1,.4,26.8),(3,.3,6.1)],
}

def run(args):
    subprocess.run(args, check=True)

def compose(source_dir, output_dir):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    output_dir.mkdir(parents=True, exist_ok=True)
    source_records = []
    for name in SOURCES:
        path = source_dir / name
        source_records.append({'filename':name, 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    results = []
    with tempfile.TemporaryDirectory(prefix='ade-recording-edit-') as tmp:
        tmp = Path(tmp)
        for filename, cuts in EDITS.items():
            paths = []
            for i, (index, start, duration) in enumerate(cuts):
                part = tmp / f'{Path(filename).stem}-{i}.mp4'
                # Crop the bottom control bar, preserve the full horizontal field,
                # and keep native 720p detail. Fade uses black, never overlapping poses.
                crop_height = 1024 if index == 1 else 1120
                pad_top = (1280-crop_height)//2
                vf = (
                    f'crop=720:{crop_height}:0:0,setsar=1,fps=30,'
                    f'pad=720:1280:0:{pad_top}:color=0x151218,'
                    f'fade=t=in:st=0:d=0.066667,fade=t=out:st={duration-.066667:.6f}:d=0.066667,'
                    'format=yuv420p'
                )
                run([ff,'-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',str(source_dir/SOURCES[index]),
                     '-t',str(duration),'-map','0:v:0','-an','-vf',vf,'-c:v','libx264','-preset','medium',
                     '-crf','18','-movflags','+faststart','-map_metadata','-1',str(part)])
                paths.append(part)
            concat_file = tmp/'concat.txt'
            concat_file.write_text(''.join(f"file '{p.as_posix()}'\n" for p in paths),encoding='utf-8')
            output = output_dir/filename
            run([ff,'-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat_file),
                 '-map','0:v:0','-an','-c:v','copy','-movflags','+faststart','-map_metadata','-1',str(output)])
            # Decode the entire export; corrupt frames fail the task.
            run([ff,'-hide_banner','-loglevel','error','-xerror','-i',str(output),'-f','null','-'])
            reader = imageio_ffmpeg.read_frames(str(output))
            metadata = next(reader)
            reader.close()
            expected = round(sum(c[2] for c in cuts),3)
            if abs(metadata['duration']-expected) > .05:
                raise ValueError(f'Unexpected duration: {metadata["duration"]} vs {expected}')
            count, seconds = imageio_ffmpeg.count_frames_and_secs(str(output))
            if count != round(expected*30):
                raise ValueError(f'Unexpected frame count: {count}')
            results.append({'filename':filename,'duration':metadata['duration'],'frames':count,
                            'size':metadata['size'],'fps':metadata['fps'],'audio':False,
                            'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
                            'cuts':[{'source':SOURCES[c[0]],'start':c[1],'duration':c[2]} for c in cuts]})
    (output_dir/'edit-manifest.json').write_text(json.dumps({'sources':source_records,'outputs':results},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    compose(args.source_dir,args.output_dir)
