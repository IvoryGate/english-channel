from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "workspace" / "shows" / "tools"
WORKER_ROOT = REPO_ROOT / "apps" / "worker-py"
SCRIPT_VALIDATOR_DIR = REPO_ROOT / ".cursor" / "skills" / "dialogue-podcast-scriptwriting" / "scripts"
for import_path in (TOOLS_DIR, WORKER_ROOT, SCRIPT_VALIDATOR_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from episode_artifacts import artifact_paths, load_json  # noqa: E402
from episode_workspace import (  # noqa: E402
    canonical_episode_workspace,
    episode_number,
    normalize_episode_id,
    validate_show_id,
)
from episode_youtube_meta import sync_youtube_json  # noqa: E402
from prepare_episode_manifest import manifest_coverage  # noqa: E402
from validate_podcast_script import validate_script_text  # noqa: E402


MIN_FREE_GIB = 10.0
MIN_AVAILABLE_MEMORY_GIB = 8.0
YOUTUBE_TITLE_MAX = 100


@dataclass(frozen=True)
class EpisodeContext:
    repo_root: Path
    show_id: str
    episode_id: str
    episode_num: int
    workspace: Path
    youtube_root: Path


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class PreflightReport:
    show_id: str
    episode_id: str
    workspace: str
    checks: tuple[CheckResult, ...]

    @property
    def ok(self) -> bool:
        return not any(check.status == "error" for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "showId": self.show_id,
            "episodeId": self.episode_id,
            "workspace": self.workspace,
            "checks": [asdict(check) for check in self.checks],
        }


def build_context(
    repo_root: Path,
    show_id: str,
    episode: str | int,
    youtube_root: Path,
) -> EpisodeContext:
    show = validate_show_id(show_id)
    episode_id = normalize_episode_id(episode)
    return EpisodeContext(
        repo_root=repo_root.resolve(),
        show_id=show,
        episode_id=episode_id,
        episode_num=episode_number(episode_id),
        workspace=canonical_episode_workspace(repo_root, show, episode_id),
        youtube_root=youtube_root.resolve(),
    )


def _check_file(checks: list[CheckResult], name: str, path: Path) -> bool:
    if path.is_file() and path.stat().st_size > 0:
        checks.append(CheckResult(name, "pass", str(path)))
        return True
    checks.append(CheckResult(name, "error", f"Missing or empty: {path}"))
    return False


def _disk_check(checks: list[CheckResult], name: str, path: Path) -> None:
    probe = path
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    try:
        free_gib = shutil.disk_usage(probe).free / 1024**3
    except OSError as exc:
        checks.append(CheckResult(name, "error", f"Cannot inspect {probe}: {exc}"))
        return
    status = "pass" if free_gib >= MIN_FREE_GIB else "error"
    checks.append(CheckResult(name, status, f"{free_gib:.1f} GiB free at {probe} (minimum {MIN_FREE_GIB:.0f} GiB)"))


def _runtime_checks(checks: list[CheckResult], repo_root: Path) -> None:
    python = repo_root / ".conda-env" / "python.exe"
    if not _check_file(checks, "python-runtime", python):
        return
    model_dir = repo_root / "pretrained_models" / "VoxCPM2"
    required_model_files = (model_dir / "config.json", model_dir / "model.safetensors", model_dir / "audiovae.pth")
    missing = [str(path) for path in required_model_files if not path.is_file() or path.stat().st_size == 0]
    if missing:
        checks.append(CheckResult("voxcpm-model", "error", "Missing: " + ", ".join(missing)))
    else:
        checks.append(CheckResult("voxcpm-model", "pass", str(model_dir)))

    smoke = "import _ctypes, soundfile, torch; print('cuda=' + str(torch.cuda.is_available()).lower())"
    try:
        result = subprocess.run(
            [str(python), "-c", smoke],
            cwd=str(repo_root),
            text=True,
            capture_output=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        checks.append(CheckResult("runtime-imports", "error", f"Runtime smoke check failed: {exc}"))
    else:
        output = (result.stdout + " " + result.stderr).strip()
        if result.returncode != 0 or "cuda=true" not in result.stdout.lower():
            checks.append(CheckResult("runtime-imports", "error", output or f"exit={result.returncode}"))
        else:
            checks.append(CheckResult("runtime-imports", "pass", output))

    try:
        import psutil

        available_gib = psutil.virtual_memory().available / 1024**3
        status = "pass" if available_gib >= MIN_AVAILABLE_MEMORY_GIB else "error"
        checks.append(
            CheckResult(
                "available-memory",
                status,
                f"{available_gib:.1f} GiB available (minimum {MIN_AVAILABLE_MEMORY_GIB:.0f} GiB)",
            )
        )
    except Exception as exc:
        checks.append(CheckResult("available-memory", "warn", f"Could not inspect memory: {exc}"))


def preflight_episode(
    context: EpisodeContext,
    *,
    runtime_checks: bool = True,
    scaffold_metadata: bool = True,
) -> PreflightReport:
    checks: list[CheckResult] = []
    paths = artifact_paths(context.workspace, context.episode_id)

    if not context.workspace.is_dir():
        checks.append(CheckResult("workspace", "error", f"Missing canonical workspace: {context.workspace}"))
        return PreflightReport(context.show_id, context.episode_id, str(context.workspace), tuple(checks))
    checks.append(CheckResult("workspace", "pass", str(context.workspace)))

    draft_ok = _check_file(checks, "draft", paths["draft"])
    manifest_ok = _check_file(checks, "manifest", paths["manifest"])
    manifest: dict[str, Any] = {}
    draft_text = ""
    if draft_ok:
        draft_text = paths["draft"].read_text(encoding="utf-8")
    if manifest_ok:
        try:
            manifest = load_json(paths["manifest"])
        except (OSError, json.JSONDecodeError) as exc:
            checks.append(CheckResult("manifest-json", "error", str(exc)))
            manifest_ok = False

    config_path = TOOLS_DIR / "show_config.json"
    config = load_json(config_path)["shows"][context.show_id]
    if draft_ok:
        min_words, max_words = (int(value) for value in config["wordCountRange"])
        validation = validate_script_text(
            draft_text,
            min_words=min_words,
            max_words=max_words,
            profile=context.show_id,
        )
        if validation["ok"]:
            checks.append(CheckResult("script-quality", "pass", f"{validation['word_count']} spoken words"))
        else:
            summary = "; ".join(f"{issue['code']}: {issue['message']}" for issue in validation["issues"])
            checks.append(CheckResult("script-quality", "error", summary))

    if manifest_ok:
        if manifest.get("showId") != context.show_id or manifest.get("episodeId") != context.episode_id:
            checks.append(
                CheckResult(
                    "manifest-identity",
                    "error",
                    f"Expected {context.show_id}/{context.episode_id}, got {manifest.get('showId')}/{manifest.get('episodeId')}",
                )
            )
        else:
            checks.append(CheckResult("manifest-identity", "pass", f"{context.show_id}/{context.episode_id}"))

        turns = list(manifest.get("turns") or [])
        if draft_ok and turns:
            coverage = manifest_coverage(draft_text, config, turns)
            ratio = float(coverage["ratio"])
            status = "pass" if 0.98 <= ratio <= 1.02 else "error"
            checks.append(
                CheckResult(
                    "manifest-coverage",
                    status,
                    f"{ratio * 100:.1f}% ({coverage['manifestWords']}/{coverage['sourceWords']} spoken words)",
                )
            )
        else:
            checks.append(CheckResult("manifest-turns", "error", "Manifest contains no turns."))

        for host, profile in (manifest.get("hosts") or {}).items():
            reference = Path(str(profile.get("referenceAudioClean") or ""))
            reference_path = reference if reference.is_absolute() else context.repo_root / reference
            _check_file(checks, f"voice-reference-{host}", reference_path)

        title = str(manifest.get("title") or "").strip()
        if not title:
            checks.append(CheckResult("youtube-title", "error", "Manifest title is empty."))
        elif len(title) > YOUTUBE_TITLE_MAX:
            checks.append(CheckResult("youtube-title", "error", f"{len(title)} chars; YouTube maximum is {YOUTUBE_TITLE_MAX}."))
        else:
            checks.append(CheckResult("youtube-title", "pass", f"{len(title)} chars"))

        sync = sync_youtube_json(
            context.workspace,
            context.episode_id,
            manifest=manifest,
            write=scaffold_metadata,
        )
        if sync.get("reason"):
            checks.append(CheckResult("youtube-metadata", "error", str(sync["reason"])))
        else:
            action = "created" if sync.get("created") else "synchronized"
            checks.append(CheckResult("youtube-metadata", "pass", f"{action}: {sync['path']}"))

    cover_ready = paths["coverBakedScene"].is_file() or paths["thumbnailPng"].is_file()
    background_ready = paths["videoBgSource16x9"].is_file() or paths["videoBgJpg"].is_file()
    checks.append(
        CheckResult(
            "cover-16x9",
            "pass" if cover_ready else "error",
            str(paths["coverBakedScene"] if paths["coverBakedScene"].is_file() else paths["thumbnailPng"]),
        )
    )
    checks.append(
        CheckResult(
            "background-16x9",
            "pass" if background_ready else "error",
            str(paths["videoBgSource16x9"] if paths["videoBgSource16x9"].is_file() else paths["videoBgJpg"]),
        )
    )
    for name in ("english-listening-room-intro.mp4", "english-listening-room-outro.mp4"):
        _check_file(checks, f"branding-{name}", context.repo_root / "workspace" / "branding" / name)

    _disk_check(checks, "workspace-disk", context.workspace)
    _disk_check(checks, "export-disk", context.youtube_root)
    if runtime_checks:
        _runtime_checks(checks, context.repo_root)

    return PreflightReport(context.show_id, context.episode_id, str(context.workspace), tuple(checks))


def reports_ok(reports: list[PreflightReport]) -> bool:
    return all(report.ok for report in reports)
