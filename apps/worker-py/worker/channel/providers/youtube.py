from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..types import YouTubeReleaseSpec, YouTubeRemoteVideo


YOUTUBE_SCOPES = (
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
)


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
    token_path = (
        Path(token_value).resolve()
        if token_value
        else (repo_root / "workspace" / "channel" / "youtube" / "youtube_token.json").resolve()
    )
    if not client_path.is_file():
        raise FileNotFoundError(f"YouTube OAuth client file does not exist: {client_path}")
    return client_path, token_path


def authorize(repo_root: Path) -> Path:
    _request, _credentials, installed_flow, _build, _media = _google_modules()
    client_path, token_path = credential_paths(repo_root)
    flow = installed_flow.from_client_secrets_file(str(client_path), list(YOUTUBE_SCOPES))
    credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json() + "\n", encoding="utf-8", newline="\n")
    return token_path


def credentials(repo_root: Path) -> Any:
    request, credentials_type, _flow, _build, _media = _google_modules()
    _client_path, token_path = credential_paths(repo_root)
    if not token_path.is_file():
        raise RuntimeError(f"YouTube token is missing: {token_path}. Run scripts/youtube.py auth once.")
    value = credentials_type.from_authorized_user_file(str(token_path), list(YOUTUBE_SCOPES))
    if value.expired and value.refresh_token:
        value.refresh(request())
        token_path.write_text(value.to_json() + "\n", encoding="utf-8", newline="\n")
    if not value.valid:
        raise RuntimeError("YouTube OAuth token is invalid. Run scripts/youtube.py auth again.")
    return value


class YouTubeApiProvider:
    def __init__(self, repo_root: Path, *, service: Any | None = None) -> None:
        self.repo_root = repo_root.resolve()
        self._service = service

    @property
    def service(self) -> Any:
        if self._service is None:
            _request, _credentials, _flow, build, _media = _google_modules()
            self._service = build(
                "youtube", "v3", credentials=credentials(self.repo_root), cache_discovery=False
            )
        return self._service

    def channel_id(self) -> str:
        response = self.service.channels().list(part="id", mine=True).execute(num_retries=3)
        items = response.get("items") or []
        if len(items) != 1 or not items[0].get("id"):
            raise RuntimeError("OAuth credentials do not resolve to exactly one YouTube channel")
        return str(items[0]["id"])

    def upload_private(self, spec: YouTubeReleaseSpec) -> str:
        _request, _credentials, _flow, _build, media_file_upload = _google_modules()
        request = self.service.videos().insert(
            part="snippet,status",
            notifySubscribers=spec.notify_subscribers,
            body={
                "snippet": {
                    "title": spec.title,
                    "description": spec.description,
                    "tags": list(spec.tags),
                    "categoryId": spec.category_id,
                    "defaultLanguage": spec.language,
                },
                "status": {
                    "privacyStatus": "private",
                    "selfDeclaredMadeForKids": spec.made_for_kids,
                    "containsSyntheticMedia": spec.contains_synthetic_media,
                },
            },
            media_body=media_file_upload(
                str(spec.video_path), chunksize=8 * 1024 * 1024, resumable=True
            ),
        )
        response = None
        while response is None:
            _progress, response = request.next_chunk(num_retries=5)
        video_id = response.get("id")
        if not video_id:
            raise RuntimeError("YouTube upload completed without returning a video ID")
        return str(video_id)

    def set_thumbnail(self, video_id: str, path: Path) -> None:
        _request, _credentials, _flow, _build, media_file_upload = _google_modules()
        self.service.thumbnails().set(
            videoId=video_id,
            media_body=media_file_upload(str(path), resumable=False),
        ).execute(num_retries=3)

    def upsert_captions(
        self, video_id: str, path: Path, *, language: str, name: str = "ELR English"
    ) -> str:
        _request, _credentials, _flow, _build, media_file_upload = _google_modules()
        response = self.service.captions().list(part="snippet", videoId=video_id).execute(
            num_retries=3
        )
        existing = next(
            (
                item for item in response.get("items", [])
                if item.get("snippet", {}).get("language") == language
                and item.get("snippet", {}).get("name") == name
            ),
            None,
        )
        media = media_file_upload(str(path), mimetype="application/octet-stream", resumable=False)
        if existing:
            result = self.service.captions().update(
                part="snippet",
                body={"id": existing["id"], "snippet": {"isDraft": False}},
                media_body=media,
            ).execute(num_retries=3)
        else:
            result = self.service.captions().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "language": language,
                        "name": name,
                        "isDraft": False,
                    }
                },
                media_body=media,
            ).execute(num_retries=3)
        return str(result["id"])

    def add_to_playlist(self, video_id: str, playlist_id: str) -> str:
        response = self.service.playlistItems().list(
            part="id,snippet", playlistId=playlist_id, videoId=video_id, maxResults=1
        ).execute(num_retries=3)
        items = response.get("items") or []
        if items:
            return str(items[0]["id"])
        result = self.service.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id},
                }
            },
        ).execute(num_retries=3)
        return str(result["id"])

    def fetch(self, video_id: str) -> YouTubeRemoteVideo:
        response = self.service.videos().list(
            part="snippet,status,processingDetails", id=video_id
        ).execute(num_retries=3)
        items = response.get("items") or []
        if len(items) != 1:
            raise RuntimeError(f"YouTube video is missing or inaccessible: {video_id}")
        item = items[0]
        snippet = item.get("snippet", {})
        status = item.get("status", {})
        processing = item.get("processingDetails", {})
        return YouTubeRemoteVideo(
            video_id=video_id,
            title=str(snippet.get("title", "")),
            privacy_status=str(status.get("privacyStatus", "")),
            publish_at=str(status["publishAt"]) if status.get("publishAt") else None,
            upload_status=str(status.get("uploadStatus", "")),
            processing_status=(
                str(processing["processingStatus"]) if processing.get("processingStatus") else None
            ),
            failure_reason=(str(status["failureReason"]) if status.get("failureReason") else None),
            rejection_reason=(
                str(status["rejectionReason"]) if status.get("rejectionReason") else None
            ),
        )

    def schedule(self, video_id: str, scheduled_at_utc: str, spec: YouTubeReleaseSpec) -> None:
        self.service.videos().update(
            part="status",
            body={
                "id": video_id,
                "status": {
                    "privacyStatus": "private",
                    "publishAt": scheduled_at_utc,
                    "license": "youtube",
                    "embeddable": True,
                    "publicStatsViewable": True,
                    "selfDeclaredMadeForKids": spec.made_for_kids,
                    "containsSyntheticMedia": spec.contains_synthetic_media,
                },
            },
        ).execute(num_retries=3)
