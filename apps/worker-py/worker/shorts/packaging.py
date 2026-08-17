from __future__ import annotations

from pathlib import Path
from typing import Any

from .ledger import record_publication
from .qc import check_manifest, check_video
from .workspace import atomic_write_json, ensure_workspace


def package_short(
    repo_root: Path,
    product: dict[str, Any],
    manifest: dict[str, Any],
    *,
    require_audio: bool = True,
) -> tuple[Path, dict[str, Any]]:
    workspace = ensure_workspace(repo_root, str(manifest["shortId"]))
    video_path = workspace / "video" / f"{manifest['shortId']}.mp4"
    content_qc = check_manifest(manifest, product)
    video_qc = check_video(video_path, manifest, require_audio=require_audio)
    status = "pass" if content_qc["status"] == "pass" and video_qc["status"] == "pass" else "fail"
    report = {
        "schema": "elr-short-package-v1",
        "shortId": manifest["shortId"],
        "contentKey": manifest["contentKey"],
        "status": status,
        "video": str(video_path),
        "contentQc": content_qc,
        "videoQc": video_qc,
        "upload": {
            "title": manifest["title"],
            "description": manifest["description"],
            "privacyStatus": "private",
            "madeForKids": False,
            "language": "en",
            "categoryId": "27",
            "relatedVideoId": manifest.get("relatedVideoId"),
        },
    }
    report_path = workspace / "package" / "upload.json"
    atomic_write_json(report_path, report)
    (workspace / "package" / "title.txt").write_text(
        str(manifest["title"]) + "\n", encoding="utf-8", newline="\n"
    )
    (workspace / "package" / "description.txt").write_text(
        str(manifest["description"]) + "\n", encoding="utf-8", newline="\n"
    )
    if status == "pass" and require_audio:
        record_publication(
            repo_root,
            short_id=str(manifest["shortId"]),
            content_key=str(manifest["contentKey"]),
            status="packaged",
        )
    return report_path, report
