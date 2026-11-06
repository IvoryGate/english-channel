"""Resolve approved shared plates while retaining published chapter branding."""
import json
from pathlib import Path


def approved_chapter_plate(repo_root: Path, slug: str, chapter: int, kind: str, legacy: Path) -> Path:
    policy = repo_root / 'configs/branding/approved-longform.json'
    if not policy.is_file():
        return legacy
    config = json.loads(policy.read_text(encoding='utf-8'))
    cutoff = config.get('classicLegacyThroughChapter', {}).get(slug, 0)
    if chapter <= int(cutoff):
        return legacy
    selected = (repo_root / config[kind]['path']).resolve()
    if not selected.is_relative_to(repo_root.resolve()) or not selected.is_file():
        raise FileNotFoundError(f'Approved {kind} plate is unavailable: {selected}')
    return selected


def uses_approved_body(repo_root: Path, slug: str, chapter: int) -> bool:
    policy = repo_root / 'configs/branding/approved-longform.json'
    if not policy.is_file():
        return False
    config = json.loads(policy.read_text(encoding='utf-8'))
    return bool(config.get('body')) and chapter > int(config.get('classicLegacyThroughChapter', {}).get(slug, 0))
