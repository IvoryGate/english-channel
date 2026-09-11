from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CHANNEL_ID = "UC9QpAkVpv8l1ZQ3X4UtU37A"
PLAYLISTS = {
    "series_a": "PLUALyXHUPuM0",
    "series_b": "PLV6UzOzdXS_w",
    "series_c": "PLeDOm-qygJM4",
}


def build_release_item(slot: dict[str, Any]) -> dict[str, Any]:
    content_id = str(slot["contentId"])
    common = {
        "contentId": content_id,
        "scheduledAt": str(slot["scheduledAt"]),
        "categoryId": "27",
        "containsSyntheticMedia": True,
        "notifySubscribers": False,
        "qcStatus": "pass",
    }
    classic = re.fullmatch(r"content:classic_listening:persuasion_chapter_(\d{3})", content_id)
    if classic:
        chapter_id = f"chapter_{classic.group(1)}"
        stem = f"000_{chapter_id}"
        base = f"workspace/classics/persuasion/{chapter_id}"
        return {
            **common,
            "video": f"{base}/video/{stem}.mp4",
            "thumbnail": f"{base}/video/{stem}.thumbnail.png",
            "captions": f"{base}/subtitles/{stem}.youtube.srt",
            "metadataFile": f"{base}/reports/{stem}.youtube.json",
            "playlistId": "PLbM2xsP8plRg",
        }
    dialogue = re.fullmatch(r"content:(series_[abc]):episode_(\d{3})", content_id)
    if dialogue:
        series, number = dialogue.groups()
        episode_id = f"episode_{number}"
        stem = f"000_{episode_id}"
        base = f"workspace/shows/{series}/{episode_id}"
        return {
            **common,
            "video": f"{base}/video/{stem}.mp4",
            "thumbnail": f"{base}/video/{stem}.thumbnail.png",
            "captions": f"{base}/subtitles/{stem}.srt",
            "titleFile": f"{base}/reports/{stem}.youtube_title.txt",
            "descriptionFile": f"{base}/reports/{stem}.youtube_description.txt",
            "playlistId": PLAYLISTS[series],
        }
    short = re.fullmatch(r"content:shorts_main:(elr-s-\d{3})", content_id)
    if short:
        short_id = short.group(1)
        base = f"workspace/shorts/{short_id}"
        return {
            **common,
            "video": f"{base}/video/{short_id}.mp4",
            "thumbnail": f"{base}/package/{short_id}.thumbnail.png",
            "metadataFile": f"{base}/package/upload.json",
            "titleFile": f"{base}/package/title.txt",
            "descriptionFile": f"{base}/package/description.txt",
        }
    raise ValueError(f"Unsupported weekly-plan contentId: {content_id}")


def build_manifest(plan_path: Path) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    items = [build_release_item(slot) for slot in plan["publicationSlots"]]
    return {
        "schema": "youtube-release-manifest-v1",
        "youtubeChannelId": CHANNEL_ID,
        "weeklyPlan": plan_path.relative_to(REPO_ROOT).as_posix(),
        "items": items,
    }


def validate_artifacts(manifest: dict[str, Any]) -> None:
    missing: list[str] = []
    failed_packages: list[str] = []
    for item in manifest["items"]:
        for key in ("video", "thumbnail"):
            if not (REPO_ROOT / item[key]).is_file():
                missing.append(f"{item['contentId']}:{key}")
        metadata_file = item.get("metadataFile")
        if metadata_file and "/shorts/" in metadata_file:
            path = REPO_ROOT / metadata_file
            if not path.is_file():
                missing.append(f"{item['contentId']}:metadataFile")
            elif json.loads(path.read_text(encoding="utf-8")).get("status") != "pass":
                failed_packages.append(str(item["contentId"]))
    if missing or failed_packages:
        details = [
            *(f"missing {value}" for value in missing),
            *(f"failed package {value}" for value in failed_packages),
        ]
        raise ValueError("Release artifacts are not ready: " + "; ".join(details))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a YouTube release manifest from an approved weekly plan.")
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    manifest = build_manifest(args.plan.resolve())
    validate_artifacts(manifest)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"release_items={len(manifest['items'])} output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
