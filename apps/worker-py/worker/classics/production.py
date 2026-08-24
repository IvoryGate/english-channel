from __future__ import annotations

import gc
import subprocess
from pathlib import Path
from typing import Any

from .audio_render import _default_model_factory, render_audio
from .brand_voice import render_chapter_brand_voice
from .chapter_package import ChapterPackageError, package_chapter
from .config import BookConfig
from .paths import ClassicPaths
from .run_state import RunStateStore


class ProductionError(RuntimeError):
    pass


def _render(repo_root: Path, arguments: list[str]) -> None:
    remotion = repo_root / "node_modules" / ".bin" / "remotion.cmd"
    if not remotion.is_file():
        raise ProductionError(f"Remotion CLI is missing: {remotion}")
    result = subprocess.run(
        ["cmd.exe", "/d", "/s", "/c", str(remotion), *arguments],
        cwd=repo_root,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise ProductionError(f"Remotion failed ({result.returncode}):\n{result.stdout[-2000:]}\n{result.stderr[-4000:]}")


def render_chapter_visuals(
    repo_root: Path, config: BookConfig, chapters: list[int], *, force: bool = False
) -> list[dict[str, str]]:
    paths = ClassicPaths(repo_root, config.slug)
    rendered: list[dict[str, str]] = []
    for chapter in chapters:
        paths.video_dir(chapter).mkdir(parents=True, exist_ok=True)
        jobs = [
            (
                paths.thumbnail(chapter),
                ["still", "src/classics/index.ts", f"PersuasionChapter{chapter}Cover", str(paths.thumbnail(chapter))],
            ),
            (
                paths.intro_video(chapter),
                ["render", "src/classics/index.ts", f"PersuasionChapter{chapter}Intro", str(paths.intro_video(chapter))],
            ),
            (
                paths.outro_video(chapter),
                ["render", "src/classics/index.ts", f"PersuasionChapter{chapter}Outro", str(paths.outro_video(chapter))],
            ),
        ]
        for output, arguments in jobs:
            if force or not output.is_file():
                _render(repo_root, arguments)
        rendered.append(
            {
                "thumbnail": paths.thumbnail(chapter).relative_to(repo_root).as_posix(),
                "intro": paths.intro_video(chapter).relative_to(repo_root).as_posix(),
                "outro": paths.outro_video(chapter).relative_to(repo_root).as_posix(),
            }
        )
    return rendered


def produce_chapters(
    repo_root: Path, config: BookConfig, chapters: list[int], *, force: bool = False
) -> dict[str, Any]:
    paths = ClassicPaths(repo_root, config.slug)
    state = RunStateStore(paths.state)
    state.update(status="RUNNING", phase="CHAPTER_BRANDING", activeChapters=chapters)
    model_path = config.runtime_path(repo_root, str(config.render["modelId"]))
    model = _default_model_factory(str(model_path), str(config.render.get("device", "cuda")))
    def shared_factory(*_: object) -> object:
        return model
    brand_trace = render_chapter_brand_voice(
        repo_root, config, chapters, force=force, model_factory=shared_factory
    )
    audio: list[dict[str, Any]] = []
    try:
        state.update(status="RUNNING", phase="AUDIO_RENDER", activeChapters=chapters)
        for chapter in chapters:
            trace = render_audio(
                repo_root, config, chapter, force=force, model_factory=shared_factory
            )
            audio.append(
                {
                    "chapter": chapter,
                    "segments": len(trace["segments"]),
                    "rawPath": trace["rawPath"],
                    "tracePath": trace["tracePath"],
                }
            )
    finally:
        del model
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    state.update(status="RUNNING", phase="VISUAL_RENDER", activeChapters=chapters)
    visuals = render_chapter_visuals(repo_root, config, chapters, force=force)
    state.update(status="RUNNING", phase="PACKAGE", activeChapters=chapters)
    packages = [package_chapter(repo_root, config, chapter, force=force) for chapter in chapters]
    current_state = state.read() or {}
    chapter_state = dict(current_state.get("chapterState") or {})
    chapter_state.update({f"chapter_{chapter:03d}": "EXPORTED" for chapter in chapters})
    state.update(status="READY", phase="EXPORTED", activeChapters=[], chapterState=chapter_state)
    return {
        "bookSlug": config.slug,
        "chapters": chapters,
        "brandTrace": brand_trace["tracePath"],
        "audio": audio,
        "visuals": visuals,
        "packages": packages,
    }
