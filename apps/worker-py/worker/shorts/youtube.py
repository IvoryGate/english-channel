from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .analytics import ANALYTICS_SCHEMA
from .ledger import load_ledger, record_publication
from .workspace import atomic_write_json, operation_root, read_json


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


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


def credential_paths(repo_root: Path) -> tuple[Path, Path]:
    client_value = os.environ.get("YOUTUBE_CLIENT_SECRETS")
    if not client_value:
        raise RuntimeError("Set YOUTUBE_CLIENT_SECRETS to the Google OAuth desktop client JSON path.")
    client_path = Path(client_value).resolve()
    token_value = os.environ.get("YOUTUBE_TOKEN_PATH")
    token_path = Path(token_value).resolve() if token_value else operation_root(repo_root) / "youtube_token.json"
    if not client_path.is_file():
        raise FileNotFoundError(f"YouTube OAuth client file does not exist: {client_path}")
    return client_path, token_path


def authorize(repo_root: Path) -> Path:
    _request, _credentials, installed_flow, _build, _media = _google_modules()
    client_path, token_path = credential_paths(repo_root)
    flow = installed_flow.from_client_secrets_file(str(client_path), SCOPES)
    credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json() + "\n", encoding="utf-8", newline="\n")
    return token_path


def credentials(repo_root: Path) -> Any:
    request, credentials_type, _flow, _build, _media = _google_modules()
    _client_path, token_path = credential_paths(repo_root)
    if not token_path.is_file():
        raise RuntimeError(f"YouTube token is missing: {token_path}. Run shorts.py youtube-auth once.")
    credentials_value = credentials_type.from_authorized_user_file(str(token_path), SCOPES)
    if credentials_value.expired and credentials_value.refresh_token:
        credentials_value.refresh(request())
        token_path.write_text(credentials_value.to_json() + "\n", encoding="utf-8", newline="\n")
    if not credentials_value.valid:
        raise RuntimeError("YouTube OAuth token is invalid. Run shorts.py youtube-auth again.")
    return credentials_value


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


def _report_values(response: dict[str, Any]) -> dict[str, float]:
    headers = [str(header["name"]) for header in response.get("columnHeaders", [])]
    rows = response.get("rows") or []
    if not rows:
        return {name: 0.0 for name in headers}
    return {name: float(value) for name, value in zip(headers, rows[0], strict=False)}


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
        rows.append(
            {
                "shortId": item["shortId"],
                "observedOn": end.isoformat(),
                "views": values.get("views", 0.0),
                "engaged_views": values.get("engagedViews", 0.0),
                "average_percentage_viewed": values.get("averageViewPercentage", 0.0),
                "subscribers_gained": values.get("subscribersGained", 0.0),
                "likes": values.get("likes", 0.0),
                "comments": values.get("comments", 0.0),
                "shares": values.get("shares", 0.0),
                "long_form_views": 0.0,
            }
        )
    if not rows:
        raise RuntimeError("No uploaded Shorts with YouTube IDs are available for analytics sync")
    output = operation_root(repo_root) / "analytics" / f"{end.isoformat()}.json"
    atomic_write_json(
        output,
        {
            "schema": ANALYTICS_SCHEMA,
            "snapshotDate": end.isoformat(),
            "importedAt": date.today().isoformat(),
            "sourceFile": "youtube-analytics-api",
            "window": {"start": start.isoformat(), "end": end.isoformat()},
            "rows": rows,
        },
    )
    return output
