from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MEDIA_SCRIPTS = REPO_ROOT / ".cursor" / "skills" / "audiobook-chapter-tts" / "scripts"
sys.path.insert(0, str(MEDIA_SCRIPTS))

from media.cover_pipeline import build_prompt_bundle  # noqa: E402
from media.host_visuals import get_show_visual, parse_cover_text_layers  # noqa: E402


def test_show_hosts_are_same_age_band_within_series() -> None:
    for show_id in ("series_a", "series_b", "series_c"):
        show = get_show_visual(show_id)
        assert show.female_host.age_band == show.male_host.age_band


def test_hosts_are_distinct_across_registry() -> None:
    names = set()
    for show_id in ("series_a", "series_b", "series_c"):
        show = get_show_visual(show_id)
        names.add(show.female_host.name)
        names.add(show.male_host.name)
    assert names == {"Ethan", "Nora", "Riley", "Sam", "Leo", "Mia"}


def test_scene_prompt_includes_fixed_hosts_and_no_text_rule() -> None:
    bundle = build_prompt_bundle(
        show_id="series_b",
        hook_text="Practice English Alone Every Day (Only 15 Minutes!)",
        youtube_payload={"coverScene": "home desk"},
    )
    prompt = bundle["sceneImagePrompt"]
    assert "Riley" in prompt
    assert "Sam" in prompt
    assert "no text" in prompt.lower()
    assert "left" in prompt
    assert "right" in prompt


def test_parse_cover_text_prefers_structured_payload() -> None:
    layers = parse_cover_text_layers(
        "ignored",
        {"coverText": {"prefix": "Talk About", "main": "COFFEE", "suffix": "IN ENGLISH", "badge": "Real Talk"}},
    )
    assert layers["main"] == "COFFEE"
    assert layers["badge"] == "Real Talk"
