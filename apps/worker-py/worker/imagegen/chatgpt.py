"""Drive the web ChatGPT image generator through a persistent CDP session.

Ported from the proven vibecut implementation. Working modes:

- **Attach mode (default)**: connect to the daily session started by
  ``imagegen_session.py`` (CDP, default port 9334). No new window, no login
  dance; after generating, the browser stays open for the next task.
- **``--standalone``**: launch a one-shot browser for first login on a new
  machine.

Chat strategy ``--chat`` (keeps context pollution down):

- ``new`` (default): start a fresh conversation per generation
- ``continue``: keep writing into the current conversation
- ``<URL>``: continue a specific conversation (iterations of one scene)

Anti-fingerprint rules (see ``docs/IMAGEGEN_BROWSER.md``): segmented
per-character typing, real-entropy pauses between input and submit (no
fixed seed anywhere), backoff retries on challenge pages.

The ChatGPT UI strings below are Chinese because the session launches
Chromium with ``--lang=zh-CN``; keep them in sync with that locale.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterator

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_PROFILE_DIR = REPO_ROOT / "workspace" / "runtime" / "imagegen" / "chromium-profile"
PROFILE_DIR = Path(os.environ.get("EN_CHANNEL_PROFILE_DIR", str(DEFAULT_PROFILE_DIR)))
CDP_PORT = int(os.environ.get("EN_CHANNEL_CDP_PORT", "9334"))
CDP_URL = f"http://127.0.0.1:{CDP_PORT}"
LOGIN_WAIT_SEC = 300  # standalone first login: at most 5 minutes
IMAGE_WAIT_SEC = 240  # image generation: at most 4 minutes
CHALLENGE_MAX_RETRY = 2  # challenge backoff retries

TEXTBOX_NAME = "询问 ChatGPT"
LOGIN_BUTTON_NAME = "登录"
RETRY_BUTTON_NAME = "重试"
IMG_ALT = "已生成图像"
CHALLENGE_MARKER = "cloudflare_challenge"

MIME_EXTENSIONS = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
}


def jitter(lo: float, hi: float) -> float:
    """True random in range (system entropy), never a fixed seed."""
    return secrets.SystemRandom().uniform(lo, hi)


def iter_chunks(text: str, rand: Callable[[float, float], float]) -> Iterator[str]:
    """Split text into 5-13 character chunks for human-like typing."""
    position = 0
    while position < len(text):
        chunk_len = max(1, int(rand(5, 14)))
        yield text[position : position + chunk_len]
        position += chunk_len


def human_pause(lo: float = 2.5, hi: float = 6.5) -> float:
    """Random input-to-submit pause; returns the seconds actually used."""
    seconds = jitter(lo, hi)
    time.sleep(seconds)
    return seconds


def mime_to_ext(mime: str) -> str:
    return MIME_EXTENSIONS.get(mime, "bin")


def type_like_human(page: Any, text: str) -> None:
    """Segmented per-character typing; chunk size, delays and micro-pauses
    are all random."""
    box = page.get_by_role("textbox", name=TEXTBOX_NAME).first
    box.click()
    position = 0
    for chunk in iter_chunks(text, jitter):
        box.type(chunk, delay=int(jitter(30, 85)))
        position += len(chunk)
        if position < len(text):
            time.sleep(jitter(0.06, 0.28))


def dismiss_dialogs(page: Any) -> None:
    """Login/upsell dialogs cover the input box: pause, then close them."""
    time.sleep(jitter(1.0, 2.5))
    for _ in range(3):
        if page.locator('[role="dialog"]').count() == 0:
            break
        page.keyboard.press("Escape")
        time.sleep(jitter(0.8, 1.8))


def logged_in(page: Any) -> bool:
    """Three conditions: back on chatgpt.com, no login button, box visible."""
    try:
        if "chatgpt.com" not in page.url:
            return False
        if page.get_by_role("button", name=LOGIN_BUTTON_NAME).first.is_visible(timeout=1000):
            return False
        return page.get_by_role("textbox", name=TEXTBOX_NAME).first.is_visible(timeout=1000)
    except Exception:  # noqa: BLE001
        return False


def wait_for_login(page: Any) -> bool:
    """Standalone mode: wait for the human to finish logging in (first run)."""
    if logged_in(page):
        return True
    print("Not logged in: complete the ChatGPT login in the opened window (waiting up to 5 minutes)", flush=True)
    deadline = time.time() + LOGIN_WAIT_SEC
    while time.time() < deadline:
        time.sleep(jitter(1.5, 3.5))
        if logged_in(page):
            print("Login detected", flush=True)
            return True
    return False


IMG_COUNT_JS = (
    "[...document.querySelectorAll('img')]"
    ".filter(i => (i.alt || '').includes('" + IMG_ALT + "')).length"
)

IMG_LAST_READY_JS = (
    """() => {
        const imgs = [...document.querySelectorAll('img')]
            .filter(i => (i.alt || '').includes('""" + IMG_ALT + """'));
        const last = imgs[imgs.length - 1];
        return last && last.complete && last.naturalWidth > 0;
    }"""
)


def count_images(page: Any) -> int:
    """Number of generated images in the current conversation (used to spot
    the newly generated one)."""
    return page.evaluate(f"() => {IMG_COUNT_JS}")


def wait_for_image(page: Any, previous_count: int) -> bool:
    """Wait for the image count to exceed ``previous_count`` (must be the
    new one in multi-image conversations); back off on challenge pages."""
    for attempt in range(CHALLENGE_MAX_RETRY + 1):
        try:
            page.wait_for_function(
                f"() => {IMG_COUNT_JS} > {int(previous_count)}",
                timeout=IMAGE_WAIT_SEC * 1000,
            )
            # The newest image may still be decoding; wait until it is ready.
            page.wait_for_function(IMG_LAST_READY_JS, timeout=30000)
            return True
        except Exception:  # noqa: BLE001
            challenge = page.get_by_text(CHALLENGE_MARKER).count() > 0
            if not challenge or attempt == CHALLENGE_MAX_RETRY:
                return False
            backoff = jitter(8.0, 16.0) * (attempt + 1)
            print(f"Challenge page hit, backing off {backoff:.1f}s before retry ({attempt + 1}/{CHALLENGE_MAX_RETRY})", flush=True)
            time.sleep(backoff)
            retry_btn = page.get_by_role("button", name=RETRY_BUTTON_NAME).first
            if retry_btn.count() > 0 and retry_btn.is_visible():
                retry_btn.click()
    return False


def extract_image(page: Any) -> dict:
    """Pull the newest generated image out of the page as base64 (last image
    in multi-image conversations, so an older one is never captured)."""
    payload = page.evaluate(
        """async () => {
            const imgs = [...document.querySelectorAll('img')]
                .filter(i => (i.alt || '').includes('""" + IMG_ALT + """'));
            const img = imgs[imgs.length - 1];
            if (!img) return JSON.stringify({error: 'image not found'});
            const blob = await (await fetch(img.src)).blob();
            const bytes = new Uint8Array(await blob.arrayBuffer());
            let binary = '';
            const chunk = 0x8000;
            for (let i = 0; i < bytes.length; i += chunk) {
                binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
            }
            return JSON.stringify({mime: blob.type, size: blob.size, b64: btoa(binary)});
        }"""
    )
    data = json.loads(payload)
    if isinstance(data, str):
        data = json.loads(data)
    if "error" in data:
        raise RuntimeError(data["error"])
    return data


def run_generation(page: Any, prompt: str, out_path: Path) -> int:
    """One generation on the given page: type, pause, send, wait, download."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    dismiss_dialogs(page)
    previous_count = count_images(page)  # remember the current count
    type_like_human(page, prompt)
    pause = human_pause(2.5, 6.5)  # input-to-send random pause
    page.get_by_role("textbox", name=TEXTBOX_NAME).first.press("Enter")

    if not wait_for_image(page, previous_count):
        print("Error: image wait timed out or the challenge was not passed", file=sys.stderr)
        return 1

    data = extract_image(page)
    chat_url = page.url

    image_bytes = base64.b64decode(data["b64"])
    out_path.write_bytes(image_bytes)

    meta = {
        "prompt": prompt,
        "mime": data["mime"],
        "size": data["size"],
        "sha256": hashlib.sha256(image_bytes).hexdigest(),
        "chat_url": chat_url,
        "send_pauses_sec": [round(pause, 2)],
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    meta_path = out_path.parent / (out_path.name + ".meta.json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Done: {out_path} ({data['size']} bytes)", flush=True)
    print(f"Conversation: {chat_url}", flush=True)
    print(out_path)
    return 0


def select_attached_page(context: Any, chat: str) -> Any:
    """Pick/open the working page for the given ``--chat`` strategy.

    ``new``      -> reuse the first chatgpt page or open one, go to home
    ``continue`` -> reuse the current chatgpt page (no navigation)
    ``<URL>``    -> reuse the first chatgpt page or open one, go to that chat
    """
    pages = [pg for pg in context.pages if pg.url.startswith("http")]
    pages = [pg for pg in pages if "chatgpt.com" in pg.url]
    page = pages[0] if pages else context.new_page()

    if chat == "continue":
        return page
    target = "https://chatgpt.com/" if chat == "new" else chat
    page.goto(target, wait_until="domcontentloaded", timeout=60000)
    time.sleep(jitter(1.0, 2.0))
    return page


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate an image via the web ChatGPT image tool")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--prompt", help="image prompt text")
    source.add_argument("--prompt-file", help="read the prompt from a UTF-8 text file")
    parser.add_argument("--out", required=True, help="output image path (writes <out>.meta.json alongside)")
    parser.add_argument(
        "--chat",
        default="new",
        help="conversation strategy: new (default) | continue | <conversation URL>",
    )
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="launch a one-off browser instead of attaching (first login on a new machine)",
    )
    return parser


def load_prompt(args: argparse.Namespace, parser: argparse.ArgumentParser) -> str:
    prompt = (
        Path(args.prompt_file).read_text(encoding="utf-8").strip()
        if args.prompt_file
        else (args.prompt or "").strip()
    )
    if not prompt:
        parser.error("prompt is empty")
    return prompt


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    prompt = load_prompt(args, parser)
    out_path = Path(args.out)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        if args.standalone:
            # Standalone owns the browser lifecycle (first-login scenario).
            ctx = None
            last_error = None
            for channel in (None, "msedge", "chrome"):  # prefer bundled Chromium
                for sandbox in (True, False):  # prefer sandbox on
                    try:
                        ctx = p.chromium.launch_persistent_context(
                            str(PROFILE_DIR),
                            channel=channel,
                            headless=False,
                            locale="zh-CN",
                            viewport={"width": 1440, "height": 900},
                            chromium_sandbox=sandbox,
                        )
                        break
                    except Exception as exc:  # noqa: BLE001
                        last_error = exc
                if ctx is not None:
                    break
            if ctx is None:
                print(f"Error: cannot launch browser: {last_error}", file=sys.stderr)
                return 1

            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto("https://chatgpt.com", wait_until="domcontentloaded", timeout=60000)

            if not wait_for_login(page):
                print("Error: login timed out", file=sys.stderr)
                ctx.close()
                return 1
            result = run_generation(page, prompt, out_path)
            ctx.close()
            return result

        # Attach mode (default): connect to the daily session browser.
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL, timeout=3000)
        except Exception:  # noqa: BLE001
            print(
                "Error: persistent session is not running. Start it first:\n"
                "  python apps/worker-py/scripts/imagegen_session.py",
                file=sys.stderr,
            )
            return 1

        context = browser.contexts[0]
        page = select_attached_page(context, args.chat)
        if not logged_in(page):
            print("Error: session login expired; restart imagegen_session.py and log in", file=sys.stderr)
            return 1

        # Attach mode never closes the browser/context: only the CDP
        # connection drops when the `with` block exits, so the session
        # stays open for the next task.
        return run_generation(page, prompt, out_path)
