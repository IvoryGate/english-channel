from pathlib import Path

import numpy as np
import soundfile as sf

from worker.shorts.audio_visual import analyze_short_audio


def test_horizontal_visual_is_deterministic_audio_driven_and_resolves_silence(tmp_path: Path):
    rate = 16000
    t = np.arange(rate//2)/rate
    voice = .15*np.sin(2*np.pi*440*t)
    audio = np.concatenate((np.zeros(rate//4), voice, np.zeros(rate)))
    path = tmp_path/'test.wav'
    sf.write(path, audio, rate)
    result = analyze_short_audio(path)
    values = np.array(result['frames'])
    assert values.shape == (105, 64)
    assert np.max(values[:15]) == 0
    assert np.max(values[20:45]) > .2
    assert np.max(values[-15:]) < .001
    assert np.allclose(values[:, :32], values[:, 32:][:, ::-1])
    assert len(result['particles']) == len(result['threads']) == len(values)
    assert result['sourceSha256']
    assert result == analyze_short_audio(path)


def test_centered_no_box_layout_contract():
    root = Path(__file__).resolve().parents[3]
    code = (root/'src/shorts/english-listening-room-short.tsx').read_text(encoding='utf-8')
    assert 'width: 208, height: 208' in code
    assert "textAlign: 'center'" in code
    assert 'HorizontalSpectrum data={props.spectrum}' in code
    assert 'frame/durationInFrames' not in code
    assert "rgba(12,40,34,.88)" not in code
    assert "top: '53%'" in code and 'width: 560, height: 132' in code
    assert '[1010, 710]' in code and 'bottom: 265' in code
    assert 'rgba(255,250,239,.78)' in code
