"""Focused sonic-identity checks, without models or rendering."""
import importlib.util
import json
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('brand_audio', ROOT / 'scripts/build_brand_audio.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BrandAudioTest(unittest.TestCase):
    def test_deterministic_finite_stereo_and_timing(self):
        config = json.loads((ROOT / 'configs/branding/motion-v4.json').read_text(encoding='utf-8'))
        for kind, frame_key in [('intro', 'introFrames'), ('outro', 'outroFrames')]:
            with self.subTest(kind=kind):
                audio, events = MODULE.synthesize(config, kind)
                duplicate, _ = MODULE.synthesize(config, kind)
                self.assertTrue(np.array_equal(audio, duplicate))
                self.assertTrue(np.isfinite(audio).all())
                self.assertEqual(audio.shape, (round(config[frame_key] / config['fps'] * config['sampleRate']), 2))
                metrics = MODULE.measure(audio, config['sampleRate'])
                self.assertAlmostEqual(metrics['peakDbfs'], -6, places=3)
                # Peak is not a license to insert a discontinuity at the reveal.
                self.assertLess(metrics['maxSampleStep'], .08)
                reveal = round(config['impactFrame'] / config['fps'] * config['sampleRate'])
                self.assertLess(float(np.max(np.abs(audio[reveal] - audio[reveal - 1]))), .002)
                self.assertLess(metrics['tailRmsDbfs'], -55)
                self.assertTrue(np.all(audio[-1] == 0))
                self.assertEqual([event['frame'] for event in events if event['name'] == 'tine'], config['noteFrames'])
                if kind in ('intro', 'outro'):
                    self.assertEqual([event['frame'] for event in events if event['name'] == 'subscribe-press'], [config['ctaPressFrame']])
                    self.assertLess(config['ctaEnterFrame'], config['ctaPressFrame'])
                    self.assertLess(config['ctaBurstFrame'] + 24, config[frame_key])


if __name__ == '__main__':
    unittest.main()
