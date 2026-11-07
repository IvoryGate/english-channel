import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from elr_production import build_context, preflight_episode
from episode_artifacts import artifact_paths


def setup_pilot(root, card):
    context = build_context(root, 'series_b', 52, root / 'exports')
    paths = artifact_paths(context.workspace, context.episode_id)
    context.workspace.mkdir(parents=True)
    paths['draft'].write_text('Title: Local pilot\nRiley: A useful offer.\nSam: Thank you.\n', encoding='utf-8')
    paths['manifest'].write_text(json.dumps({'episodeId': 'episode_052', 'showId': 'series_b',
        'title': 'Local pilot', 'hosts': {}, 'turns': [
            {'text': 'A useful offer.', 'wordCount': 3}, {'text': 'Thank you.', 'wordCount': 2}]}), encoding='utf-8')
    path = context.workspace / 'production/production_card.json'
    path.parent.mkdir()
    path.write_text(json.dumps(card), encoding='utf-8')
    return context


def test_local_pilot_requires_handoff_even_for_audio_only(tmp_path, monkeypatch):
    context = setup_pilot(tmp_path, {'format': 'local_pilot', 'publicReleaseAllowed': False})
    seen = {}
    def script_check(*args, **kwargs):
        seen.update(kwargs)
        return {'ok': True, 'word_count': 5, 'issues': []}
    monkeypatch.setattr('elr_production.validate_script_text', script_check)
    report = preflight_episode(context, runtime_checks=False, require_visuals=False)
    assert not report.ok
    assert any(row.name == 'production-handoff' and row.status == 'error' for row in report.checks)
    assert (seen['min_words'], seen['max_words']) == (800, 1400)


def test_audio_only_cannot_substitute_preparation_for_voice_acceptance(tmp_path, monkeypatch):
    context = setup_pilot(tmp_path, {'format': 'local_pilot', 'publicReleaseAllowed': False,
                                   'handoff': {'path': 'handoff.json', 'sha256': 'a' * 64}})
    monkeypatch.setattr('elr_production.validate_script_text', lambda *a, **k: {'ok': True, 'word_count': 5, 'issues': []})
    required = []
    def evaluate(root, reference, stage, *, expected_context):
        required.append(stage)
        assert expected_context['episodeId'] == context.episode_id
        assert expected_context['workspace'] == context.workspace
        assert expected_context['productionManifest'] == artifact_paths(context.workspace, context.episode_id)['manifest']
        return {'passed': False, 'stages': {'ready_to_prepare': True, 'local_production': False}}
    monkeypatch.setattr('elr_production.evaluate_reference', evaluate)
    report = preflight_episode(context, runtime_checks=False, require_visuals=False)
    assert not report.ok
    assert required == ['local_production']


def test_local_pilot_cannot_claim_public_release(tmp_path, monkeypatch):
    context = setup_pilot(tmp_path, {'format': 'local_pilot', 'publicReleaseAllowed': True,
                                   'handoff': {'path': 'handoff.json', 'sha256': 'a' * 64}})
    monkeypatch.setattr('elr_production.validate_script_text', lambda *a, **k: {'ok': True, 'word_count': 5, 'issues': []})
    monkeypatch.setattr('elr_production.evaluate_reference', lambda *a, **k: {'passed': True})
    report = preflight_episode(context, runtime_checks=False, require_visuals=False)
    assert not report.ok
    assert any(row.name == 'pilot-scope' and row.status == 'error' for row in report.checks)
