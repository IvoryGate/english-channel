from __future__ import annotations

import random
import re
import time
from typing import Any

# Conservative defaults — see docs in CORPUS.md § Rate limits.
DEFAULT_SLEEP_INTERVAL_SEC = 5.0
DEFAULT_MAX_SLEEP_INTERVAL_SEC = 10.0
DEFAULT_REQUEST_PAUSE_SEC = 5.0
DEFAULT_CHANNEL_PAUSE_SEC = 30.0
DEFAULT_ENRICH_PAUSE_SEC = 6.0

RATE_LIMIT_PATTERNS = (
    re.compile(r"rate.?limit", re.I),
    re.compile(r"try again later", re.I),
    re.compile(r"HTTP Error 429", re.I),
    re.compile(r"too many requests", re.I),
)


def is_rate_limit_error(exc: BaseException | str) -> bool:
    message = str(exc)
    return any(pattern.search(message) for pattern in RATE_LIMIT_PATTERNS)


class YouTubeRateLimitError(RuntimeError):
    """Raised when YouTube/yt-dlp signals throttling; stop the batch immediately."""


def pause_between_requests(
    seconds: float = DEFAULT_REQUEST_PAUSE_SEC,
    *,
    jitter: float = 0.25,
    label: str = "",
) -> None:
    if seconds <= 0:
        return
    delay = seconds
    if jitter > 0:
        delay += random.uniform(0, seconds * jitter)
    if label:
        print(f"rate_limit: sleeping {delay:.1f}s ({label})")
    time.sleep(delay)


def ydl_sleep_opts(
    sleep_interval: float = DEFAULT_SLEEP_INTERVAL_SEC,
    max_sleep_interval: float = DEFAULT_MAX_SLEEP_INTERVAL_SEC,
) -> dict[str, Any]:
    return {
        "sleep_interval": max(0.0, float(sleep_interval)),
        "max_sleep_interval": max(float(sleep_interval), float(max_sleep_interval)),
    }


def merge_ydl_opts(base: dict[str, Any], *, sleep_interval: float, max_sleep_interval: float) -> dict[str, Any]:
    merged = dict(base)
    merged.update(ydl_sleep_opts(sleep_interval, max_sleep_interval))
    return merged


def guard_rate_limit(exc: BaseException) -> None:
    if is_rate_limit_error(exc):
        raise YouTubeRateLimitError(
            "YouTube rate limit detected. Stop this batch, wait at least 60 minutes, "
            "then retry with --smoke or lower --candidate-limit / fewer --query values. "
            f"Original error: {exc}"
        ) from exc
