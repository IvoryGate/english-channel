from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

from worker.channel.providers.youtube import authorize, credentials

from .analytics import _number, normalize_row, store_snapshot
from .ledger import load_ledger, record_publication
from .workspace import read_json


def _google_modules() -> tuple[Any, Any, Any, Any, Any]:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise RuntimeError(
            "YouTube integration dependencies are missing. Install apps/worker-py/requirements.txt."
        ) from exc
    return Request, Credentials, InstalledAppFlow, build, MediaFileUpload


def upload_private(
    repo_root: Path,
    product: dict[str, Any],
    manifest: dict[str, Any],
    package_path: Path,
) -> dict[str, Any]:
    if product["publishing"].get("defaultPrivacy") != "private":
        raise PermissionError("The pilot upload policy must remain private")
    package = read_json(package_path)
    if package.get("status") != "pass":
        raise ValueError("Short package must pass QC before upload")
    ledger = load_ledger(repo_root)
    existing = next((item for item in ledger["entries"] if item.get("shortId") == manifest["shortId"]), None)
    if existing and existing.get("youtubeId"):
        return existing
    _request, _credentials, _flow, build, media_file_upload = _google_modules()
    service = build("youtube", "v3", credentials=credentials(repo_root), cache_discovery=False)
    video_path = Path(str(package["video"]))
    if not video_path.is_file():
        raise FileNotFoundError(f"Packaged Short video is missing: {video_path}")
    request = service.videos().insert(
        part="snippet,status",
        notifySubscribers=False,
        body={
            "snippet": {
                "title": package["upload"]["title"],
                "description": package["upload"]["description"],
                "categoryId": package["upload"]["categoryId"],
                "defaultLanguage": package["upload"]["language"],
            },
            "status": {
                "privacyStatus": "private",
                "selfDeclaredMadeForKids": bool(package["upload"]["madeForKids"]),
            },
        },
        media_body=media_file_upload(str(video_path), chunksize=8 * 1024 * 1024, resumable=True),
    )
    response = None
    while response is None:
        _progress, response = request.next_chunk(num_retries=3)
    youtube_id = str(response["id"])
    return record_publication(
        repo_root,
        short_id=str(manifest["shortId"]),
        content_key=str(manifest["contentKey"]),
        status="uploaded_private",
        youtube_id=youtube_id,
    )


def _report_values(response: dict[str, Any]) -> dict[str, float | None]:
    headers = [str(header["name"]) for header in response.get("columnHeaders", [])]
    rows = response.get("rows") or []
    if not rows:
        return {name: None for name in headers}
    if len(rows) != 1 or len(rows[0]) != len(headers):
        raise ValueError("Expected one aggregate analytics row matching its column headers")
    return {name: _number(value, name) for name, value in zip(headers, rows[0], strict=True)}


def sync_analytics(
    repo_root: Path,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
) -> Path:
    _request, _credentials, _flow, build, _media = _google_modules()
    credential_value = credentials(repo_root)
    service = build("youtubeAnalytics", "v2", credentials=credential_value, cache_discovery=False)
    end = date.fromisoformat(end_date) if end_date else date.today() - timedelta(days=1)
    start = date.fromisoformat(start_date) if start_date else end - timedelta(days=27)
    if start > end:
        raise ValueError("Analytics start date must not be after end date")
    ledger = load_ledger(repo_root)
    rows = []
    metrics = "views,engagedViews,averageViewPercentage,subscribersGained,likes,comments,shares"
    for item in ledger["entries"]:
        youtube_id = item.get("youtubeId")
        if not youtube_id:
            continue
        response = (
            service.reports()
            .query(
                ids="channel==MINE",
                startDate=start.isoformat(),
                endDate=end.isoformat(),
                metrics=metrics,
                filters=f"video=={youtube_id}",
            )
            .execute(num_retries=3)
        )
        values = _report_values(response)
        field_mapping = {"views": "views", "engaged_views": "engagedViews",
                         "average_percentage_viewed": "averageViewPercentage",
                         "subscribers_gained": "subscribersGained", "likes": "likes",
                         "comments": "comments", "shares": "shares"}
        row = {field: values.get(api_name) for field, api_name in field_mapping.items()}
        row.update(shortId=item["shortId"], observedOn=end.isoformat(), long_form_views=None)
        row["metricAvailability"] = {field: "observed" if value is not None else "not_returned"
                                     for field, value in row.items() if field in field_mapping}
        row["metricAvailability"]["long_form_views"] = "unsupported"
        rows.append(normalize_row(row))
    if not rows:
        raise RuntimeError("No uploaded Shorts with YouTube IDs are available for analytics sync")
    return store_snapshot(repo_root, rows, source="youtube-analytics-api",
                          window={"start": start.isoformat(), "end": end.isoformat()})
