"""Upload release items to YouTube Studio over the persistent browser session.

Examples::

    python apps/worker-py/scripts/studio_upload.py list \
        --manifest configs/channel/youtube-release-2026-10-05.json \
        --only content:series_c:episode_029
    python apps/worker-py/scripts/studio_upload.py upload \
        --manifest configs/channel/youtube-release-2026-10-05.json \
        --only content:shorts_main:elr-s-161
    python apps/worker-py/scripts/studio_upload.py publish \
        --manifest configs/channel/youtube-release-2026-10-05.json \
        --only content:shorts_main:elr-s-161

Uploads land as private; ``publish`` flips them to public after the
platform checks pass (resolve video ids from the upload sidecars).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from worker.studio.upload import StudioUploadError, load_manifest_specs, upload_many

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["list", "upload", "publish"])
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--only", action="append", default=None, help="content id to include (repeatable)")
    args = parser.parse_args()

    try:
        specs = load_manifest_specs(Path(args.manifest), only=args.only)
    except StudioUploadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.command == "list":
        for spec in specs:
            thumb = spec.thumbnail_path.name if spec.thumbnail_path else "-"
            caps = spec.captions_path.name if spec.captions_path else "-"
            print(f"{spec.content_id} | short={spec.is_short} | thumb={thumb} | caps={caps} | {spec.title}")
        return 0
    if args.command == "publish":
        from worker.studio.upload import publish_many

        try:
            results = publish_many([spec.content_id for spec in specs])
        except StudioUploadError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        for result in results:
            print(f"public: {result['contentId']} | {result['videoId']}")
        return 0
    try:
        results = upload_many(specs)
    except StudioUploadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for result in results:
        print(f"stored private: {result['contentId']} | {result['videoId']} | {result['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
