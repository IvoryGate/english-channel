"""Render a real-audio body preview without altering any episode artifacts."""
from pathlib import Path
import argparse
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.cursor/skills/audiobook-chapter-tts/scripts'))
from media.compose_media_video import compose_media_video
from media.generate_karaoke_ass import write_karaoke_ass
from media.thumbnail_tokens import DEFAULT_TOKENS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, default=16)
    parser.add_argument('--output-dir', default='workspace/branding/body-v7')
    parser.add_argument('--reuse-overlay', action='store_true',
                        help='Recovery only: reuse an overlay made with the same audio and style')
    args = parser.parse_args()
    source = ROOT / 'workspace/shows/series_a/episode_039'
    target = ROOT / args.output_dir
    target.mkdir(parents=True, exist_ok=True)
    audio = target / 'body.wav'
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(source / 'audio/000_episode_039.master.wav'),
                    '-t', str(args.seconds), '-c:a', 'pcm_s16le', str(audio)], check=True)
    alignment = json.loads((source / 'subtitles/000_episode_039.words.json').read_text(encoding='utf-8'))
    words = [word for word in alignment['words'] if float(word['end']) <= args.seconds]
    subtitles = target / 'body.ass'
    write_karaoke_ass(subtitles, words, DEFAULT_TOKENS['series_a'])
    report = compose_media_video(background_jpg=source / 'video/000_episode_039.video_bg.jpg',
        audio_wav=audio, ass_path=subtitles, output_mp4=target / 'body-preview.mp4',
        tokens=DEFAULT_TOKENS['series_a'], fonts_dir=ROOT / 'assets/fonts',
        waveform_mov=(target / 'body-preview.barwave.mov') if args.reuse_overlay else None,
        report_path=target / 'body-preview.report.json', encoder='libx264')
    print(json.dumps({'output': report['outputMp4'], 'verification': report['verification']}))


if __name__ == '__main__':
    main()
