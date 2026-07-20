from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401

from worker.youtube_podcast_research.browser import YouTubeBrowserSession, account_browser_config
from worker.youtube_podcast_research.workspace import analysis_dir, browser_profile_dir, ensure_dir, has_chrome_user_profile

DEFAULT_CHANNEL_ID = "UC9QpAkVpv8l1ZQ3X4UtU37A"
DEFAULT_AVATAR = Path(
    "workspace/dialogue_podcast_research/youtube_corpus/branding/channel_avatar_elr_800.png"
)
CUSTOMIZATION_URL = "https://studio.youtube.com/channel/{channel_id}/editing/profile"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload channel avatar via YouTube Studio (Playwright).")
    parser.add_argument("--workspace-root", default="workspace/dialogue_podcast_research/youtube_corpus")
    parser.add_argument("--channel-id", default=DEFAULT_CHANNEL_ID)
    parser.add_argument("--avatar", default=str(DEFAULT_AVATAR))
    parser.add_argument("--wait-sec", type=int, default=0, help="Keep browser open N seconds after upload (debug).")
    return parser.parse_args()


def dismiss_studio_browser_warning(page: Any, notes: list[str]) -> None:
    skip = page.locator('a:has-text("跳至 YOUTUBE 工作室"), a:has-text("Skip to YouTube Studio")').first
    try:
        if skip.count() and skip.is_visible(timeout=3000):
            skip.click()
            notes.append("skipped_browser_warning")
            page.wait_for_timeout(5000)
    except Exception:
        pass


def wait_for_customization(page: Any, notes: list[str]) -> None:
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)
    dismiss_studio_browser_warning(page, notes)
    page.get_by_text("频道自定义", exact=False).or_(page.get_by_text("Channel customization", exact=False)).first.wait_for(
        state="visible", timeout=20000
    )
    notes.append("customization_ready")


def click_profile_change(page: Any, notes: list[str]) -> None:
    # Banner 更改 is first on page; profile 更改 is second.
    change_buttons = page.locator('button:has-text("更改"), button:has-text("Change")')
    if change_buttons.count() >= 2:
        change_buttons.nth(1).click()
        notes.append("clicked_change_index_1")
        return
    photo_section = page.locator("ytcp-channel-editing-profile").first
    if photo_section.count():
        change = photo_section.get_by_role("button", name="更改").or_(photo_section.get_by_role("button", name="Change"))
        if change.count():
            change.first.click()
            notes.append("clicked_change_in_profile_section")
            return
    change_buttons.first.click()
    notes.append("clicked_change_first_fallback")


def confirm_crop_if_needed(page: Any, notes: list[str]) -> None:
    dialog = (
        page.locator("ytcp-dialog")
        .filter(has_text="自定义照片")
        .or_(page.locator("ytcp-dialog").filter(has_text="Customize photo"))
        .or_(page.locator("ytcp-dialog").last)
    ).first
    try:
        dialog.wait_for(state="visible", timeout=8000)
    except Exception:
        notes.append("crop_dialog_not_visible")
        return

    done = dialog.get_by_role("button", name="完成").or_(dialog.get_by_role("button", name="Done")).first
    done.click(timeout=5000)
    notes.append("crop_confirmed:dialog_done")
    dialog.wait_for(state="hidden", timeout=10000)
    notes.append("crop_dialog_closed")
    page.wait_for_timeout(2000)


def publish_changes(page: Any, notes: list[str]) -> bool:
    publish = page.get_by_role("button", name="发布").or_(page.get_by_role("button", name="Publish")).first
    try:
        publish.wait_for(state="visible", timeout=10000)
        for _ in range(60):
            if publish.is_enabled():
                break
            page.wait_for_timeout(500)
        else:
            notes.append("publish_still_disabled")
            return False
        publish.click(timeout=5000)
        notes.append("clicked_publish")
        page.wait_for_timeout(6000)
        if not publish.is_enabled():
            notes.append("publish_saved")
            return True
        notes.append("publish_clicked_but_still_enabled")
        return True
    except Exception as exc:
        notes.append(f"publish_failed:{exc}")
        return False


def upload_avatar(page: Any, avatar_path: Path) -> dict[str, object]:
    notes: list[str] = []
    result: dict[str, object] = {"upload_attempted": False, "upload_ok": False, "notes": notes}

    wait_for_customization(page, notes)

    # Profile picture is under 照片 — click its 更改 (not banner 更改 above).
    page.get_by_text("照片", exact=False).first.scroll_into_view_if_needed()
    page.wait_for_timeout(500)

    change_buttons = page.locator('button:has-text("更改"), button:has-text("Change")')
    if change_buttons.count() < 2:
        notes.append("profile_change_button_missing")
        return result

    with page.expect_file_chooser(timeout=10000) as fc_info:
        change_buttons.nth(1).click()
        notes.append("clicked_change_index_1")
    fc_info.value.set_files(str(avatar_path.resolve()))
    notes.append("file_set:file_chooser")
    result["upload_attempted"] = True

    page.wait_for_timeout(4000)
    debug_shot = ensure_dir(analysis_dir(Path("workspace/dialogue_podcast_research/youtube_corpus"))) / "avatar_upload_after_file.png"
    page.screenshot(path=str(debug_shot), full_page=True)
    notes.append(f"debug_after_file:{debug_shot.as_posix()}")

    confirm_crop_if_needed(page, notes)

    publish = page.get_by_role("button", name="发布").or_(page.get_by_role("button", name="Publish")).first
    for _ in range(40):
        if publish.is_enabled():
            break
        page.wait_for_timeout(500)

    result["upload_ok"] = publish_changes(page, notes)
    return result


def main() -> int:
    args = parse_args()
    corpus_root = Path(args.workspace_root)
    avatar_path = Path(args.avatar).resolve()
    if not avatar_path.is_file():
        print(json.dumps({"error": "avatar_not_found", "path": avatar_path.as_posix()}, ensure_ascii=False))
        return 1

    if not has_chrome_user_profile(corpus_root):
        print(
            "No Chrome profile. Run open_youtube_login.ps1 first.\n"
            f"Expected: {(browser_profile_dir(corpus_root) / 'chrome_user_data').as_posix()}",
            file=sys.stderr,
        )
        return 1

    profile_dir = browser_profile_dir(corpus_root)
    config = account_browser_config(profile_dir, headless=False)
    url = CUSTOMIZATION_URL.format(channel_id=args.channel_id)

    outcome: dict[str, object] = {
        "channel_id": args.channel_id,
        "avatar": avatar_path.as_posix(),
        "studio_url": url,
    }

    with YouTubeBrowserSession(config) as session:
        assert session._page is not None
        page = session._page
        session.goto(url)
        outcome["tabs_at_start"] = len(session._context.pages) if session._context else 0
        outcome.update(upload_avatar(page, avatar_path))
        outcome["tabs_at_end"] = len(session._context.pages) if session._context else 0
        if args.wait_sec > 0:
            time.sleep(args.wait_sec)

    print(json.dumps(outcome, ensure_ascii=False, indent=2))
    return 0 if outcome.get("upload_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
