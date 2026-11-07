import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'workspace/shows/tools'))
from prepare_episode_manifest import parse_turns, manifest_coverage

SHOW = {'showId': 'series_b', 'hosts': ['Riley', 'Sam'], 'hostLinePattern': r'^(Riley|Sam):'}


def test_explicit_practice_pause_survives_manifest_regeneration():
    draft = '[Practice Prompt]\n[Pause After: 6]\nRiley: Say your answer.\nSam: Here is one answer.\n'
    first = parse_turns(draft, SHOW)
    assert [turn['pauseAfterSec'] for turn in first] == [6, 0.26]
    assert [turn['section'] for turn in first] == ['Practice Prompt', 'Practice Prompt']
    assert first == parse_turns(draft, SHOW)
    assert manifest_coverage(draft, SHOW, first)['ratio'] == 1
    assert all('Pause' not in turn['text'] for turn in first)


@pytest.mark.parametrize('value', ['nan', 'inf', '-1', '31', 'six'])
def test_invalid_pause_is_rejected(value):
    with pytest.raises(ValueError):
        parse_turns(f'[Practice Prompt]\n[Pause After: {value}]\nRiley: Try it.\n', SHOW)


def test_orphan_pause_is_rejected():
    with pytest.raises(ValueError):
        parse_turns('[Practice Prompt]\n[Pause After: 6]\n[Closing]\nSam: Bye.\n', SHOW)
