"""Render a mobile-style review using existing Short audio/art, never its release path."""
from pathlib import Path
import argparse
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/worker-py'))
from worker.shorts.render import build_render_props, _remotion_command, _browser_executable, _run_quiet, _mux_audio
from worker.shorts.workspace import atomic_write_json
from worker.shorts.audio_visual import analyze_short_audio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stills-only', action='store_true')
    args = parser.parse_args()
    source = ROOT / 'workspace/shorts/elr-s-207'
    output = ROOT / 'workspace/branding/shorts-v4'
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
    props = output / 'render-props.json'
    values = build_render_props(manifest)
    values['spectrum'] = analyze_short_audio(source / 'audio/master.wav')
    atomic_write_json(props, values)
    silent = output / 'short-preview.silent.mp4'
    node = os.environ.get('ELR_RENDER_NODE')
    cli = [node, str(ROOT / 'node_modules/@remotion/cli/remotion-cli.js')] if node else _remotion_command(ROOT)
    command = [*cli, 'render', 'src/shorts/index.ts',
        'EnglishListeningRoomShort', str(silent), f'--props={props}',
        '--codec=h264', '--crf=18', '--pixel-format=yuv420p', '--image-format=jpeg',
        '--jpeg-quality=95', '--x264-preset=ultrafast', '--concurrency=1', '--scale=0.6666666666666666', '--log=info']
    bundled = ROOT / 'node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe'
    browser = bundled if bundled.is_file() else _browser_executable()
    if browser:
        command.append(f'--browser-executable={browser}')
    if args.stills_only:
        for name, frame in [('hook', 0), ('caption', 150), ('answer-cta', 960)]:
            still = [*cli, 'still', 'src/shorts/index.ts', 'EnglishListeningRoomShort',
                str(output / f'{name}.png'), f'--props={props}', f'--frame={frame}',
                '--scale=0.6666666666666666', '--log=error']
            if browser:
                still.append(f'--browser-executable={browser}')
            _run_quiet(still, cwd=ROOT)
        print(json.dumps({'stills': str(output), 'source': manifest['shortId']}))
        return
    _run_quiet(command, cwd=ROOT)
    final = output / 'short-preview.mp4'
    _mux_audio(silent, source / 'audio/master.wav', final)
    silent.unlink()
    print(json.dumps({'output': final.as_posix(), 'source': manifest['shortId'], 'releaseModified': False}))


if __name__ == '__main__':
    main()
