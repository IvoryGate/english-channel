"""Verified short lossless chunks for resumable, stateful frame generators."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Any, Callable


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write_checkpoint(path: Path, data: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + f'.{os.getpid()}.tmp')
    temporary.write_text(json.dumps(data, separators=(',', ':')) + '\n',
                         encoding='utf-8', newline='\n')
    for attempt in range(6):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(.05 * (attempt + 1))


def valid_media(path: Path, frames: int, width: int, height: int, fps: int) -> bool:
    if not path.is_file():
        return False
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=nb_frames,width,height,r_frame_rate,codec_name,pix_fmt',
        '-of', 'json', str(path)], capture_output=True, text=True)
    try:
        stream = json.loads(probe.stdout)['streams'][0]
        rate_n, rate_d = map(int, stream['r_frame_rate'].split('/'))
        return (probe.returncode == 0 and int(stream['nb_frames']) == frames
                and stream['width'] == width and stream['height'] == height
                and rate_n == fps * rate_d and stream['codec_name'] == 'ffv1'
                and stream['pix_fmt'] == 'yuva420p')
    except (KeyError, IndexError, ValueError, TypeError, ZeroDivisionError):
        return False


def render_resumable_frames(*, output: Path, total_frames: int, width: int,
        height: int, fps: int, identity: dict[str, Any],
        draw_frame: Callable[[int], Any], save_state: Callable[[], Any],
        restore_state: Callable[[Any], None], chunk_seconds: float = 30) -> Path:
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = output.with_suffix('.render.json')
    cache: dict[str, Any] = {}
    try:
        cache = json.loads(checkpoint.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        pass
    if cache.get('fingerprint') != fingerprint:
        cache = {'schema': 'resumable-frames-v1', 'fingerprint': fingerprint,
                 'identity': identity, 'chunks': {}, 'complete': False}
    if (cache.get('complete') and valid_media(output, total_frames, width, height, fps)
            and file_hash(output) == cache.get('outputSha256')):
        print(f'radial-cache complete frames={total_frames}/{total_frames}', flush=True)
        return output

    directory = output.parent / (output.stem + '.chunks') / fingerprint[:16]
    directory.mkdir(parents=True, exist_ok=True)
    chunk_frames = max(1, round(chunk_seconds * fps))
    count = math.ceil(total_frames / chunk_frames)
    cache.update(complete=False, pid=os.getpid(), totalFrames=total_frames)
    last_heartbeat = time.monotonic()

    def report(frame: int, chunk: int) -> None:
        cache.update(currentFrame=frame, currentChunk=chunk, heartbeatAt=time.time())
        write_checkpoint(checkpoint, cache)
        print(f'radial-progress frame={frame}/{total_frames} chunk={chunk}/{count}', flush=True)

    paths = []
    for index, start in enumerate(range(0, total_frames, chunk_frames)):
        end = min(total_frames, start + chunk_frames)
        path = directory / f'{index:05d}.mov'
        paths.append(path)
        record = cache['chunks'].get(str(index), {})
        if (record.get('start') == start and record.get('end') == end
                and valid_media(path, end-start, width, height, fps)
                and file_hash(path) == record.get('sha256')):
            try:
                restore_state(record['state'])
            except (KeyError, TypeError, ValueError):
                pass  # Invalid state cannot authorize skipping visual frames.
            else:
                report(end, index+1)
                continue
        partial = path.with_suffix('.partial.mov')
        command = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
            '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{width}x{height}',
            '-r', str(fps), '-i', 'pipe:0', '-c:v', 'ffv1',
            '-pix_fmt', 'yuva420p', '-threads', '1', str(partial)]
        report(start, index+1)
        with tempfile.TemporaryFile() as errors:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=errors)
            try:
                assert process.stdin is not None
                for frame in range(start, end):
                    process.stdin.write(draw_frame(frame).tobytes())
                    if time.monotonic() - last_heartbeat >= 15:
                        report(frame+1, index+1)
                        last_heartbeat = time.monotonic()
                process.stdin.close()
                if process.wait() != 0:
                    errors.seek(0)
                    raise RuntimeError(errors.read().decode(errors='replace')[-3000:])
            except BaseException as exc:
                if process.stdin and not process.stdin.closed:
                    try:
                        process.stdin.close()
                    except OSError:
                        pass
                if process.poll() is None:
                    process.terminate()
                process.wait()
                if isinstance(exc, OSError):
                    errors.seek(0)
                    detail = errors.read().decode(errors='replace')[-3000:]
                    raise RuntimeError(
                        f'Radial encoder pipe failed in chunk {index}; '
                        f'exit={process.returncode}; {detail or str(exc)}'
                    ) from exc
                raise
        if not valid_media(partial, end-start, width, height, fps):
            raise RuntimeError(f'Invalid radial chunk: {index}')
        os.replace(partial, path)
        cache['chunks'][str(index)] = {'start': start, 'end': end,
            'sha256': file_hash(path), 'state': save_state()}
        report(end, index+1)

    listing = directory / 'concat.txt'
    listing.write_text(''.join(f"file '{path.name}'\n" for path in paths),
                       encoding='utf-8', newline='\n')
    partial_output = output.with_suffix('.partial.mov')
    subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
        '-f', 'concat', '-safe', '1', '-i', str(listing), '-c', 'copy',
        str(partial_output)], check=True)
    if not valid_media(partial_output, total_frames, width, height, fps):
        raise RuntimeError('Concatenated radial overlay failed frame/geometry verification')
    os.replace(partial_output, output)
    cache.update(complete=True, outputSha256=file_hash(output), currentFrame=total_frames,
                 heartbeatAt=time.time())
    write_checkpoint(checkpoint, cache)
    # Only our exact chunk files, after a verified canonical overlay exists.
    for path in paths:
        path.unlink(missing_ok=True)
    listing.unlink(missing_ok=True)
    print(f'radial-complete frames={total_frames}/{total_frames}', flush=True)
    return output
