"""Browser-driven YouTube Studio uploads over the persistent session.

Flow per video (mirrors what the channel did manually all week):

1. attach to the Studio session over CDP,
2. open the upload dialog and feed the local file straight into the file
   chooser (Playwright sets paths directly — no size cap, unlike the
   harness RPC upload tools),
3. fill title/description/thumbnail/playlist/subtitles from the durable
   package artifacts declared in the release manifest,
4. store as private, then publish after platform checks pass.

Selector targets are the zh-CN Studio UI (``--lang=zh-CN`` session) and
prefer text/aria labels over brittle class names. Every upload writes a
result sidecar to ``workspace/runtime/studio-browser/uploads/<id>.json``
for traceability.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .session import CDP_URL, STUDIO_HOME_URL

REPO_ROOT = Path(__file__).resolve().parents[4]
UPLOAD_RESULTS_DIR = REPO_ROOT / "workspace" / "runtime" / "studio-browser" / "uploads"


class StudioUploadError(RuntimeError):
    """Raised when the Studio upload flow cannot proceed safely."""


@dataclass
class UploadSpec:
    content_id: str
    video_path: Path
    title: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    thumbnail_path: Path | None = None
    captions_path: Path | None = None
    playlist_id: str | None = None
    category_id: str = "27"
    made_for_kids: bool = False
    notify_subscribers: bool = False
    is_short: bool = False

    def validate(self) -> None:
        if not self.video_path.is_file():
            raise StudioUploadError(f"Missing video file: {self.video_path}")
        if not self.title.strip():
            raise StudioUploadError(f"{self.content_id}: empty title")
        if not self.description.strip():
            raise StudioUploadError(f"{self.content_id}: empty description")
        if self.thumbnail_path is not None and not self.thumbnail_path.is_file():
            raise StudioUploadError(f"{self.content_id}: missing thumbnail {self.thumbnail_path}")
        if self.captions_path is not None and not self.captions_path.is_file():
            raise StudioUploadError(f"{self.content_id}: missing captions {self.captions_path}")


def _read_optional_text(path_str: str | None) -> str | None:
    if not path_str:
        return None
    path = Path(path_str)
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip()


def _metadata_fields(item: dict[str, Any]) -> tuple[str, str, list[str], bool | None]:
    """Extract title/description/tags/madeForKids from the item metadata file.

    Two durable conventions coexist:

    - classic chapters ship ``*.youtube.json`` with top-level
      ``title``/``description``/``tags``,
    - shorts ship ``package/upload.json`` with an ``upload`` block.

    Returns empty values when no metadata file exists (series episodes
    carry title/description in ``titleFile``/``descriptionFile`` instead).
    """
    meta_file = item.get("metadataFile")
    if not meta_file:
        return "", "", [], None
    path = Path(meta_file)
    if not path.is_file():
        return "", "", [], None
    meta = json.loads(path.read_text(encoding="utf-8"))
    upload_block = meta.get("upload")
    if isinstance(upload_block, dict):
        return (
            upload_block.get("title", ""),
            upload_block.get("description", ""),
            list(upload_block.get("tags", [])),
            bool(upload_block.get("madeForKids", False)),
        )
    return (
        meta.get("title", ""),
        meta.get("description", ""),
        list(meta.get("tags", [])),
        None,
    )


def load_manifest_specs(manifest_path: Path, only: list[str] | None = None) -> list[UploadSpec]:
    """Build upload specs from a release manifest plus durable packages."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    specs: list[UploadSpec] = []
    for item in manifest["items"]:
        content_id = item["contentId"]
        if only and content_id not in only:
            continue
        video_path = Path(item["video"])
        meta_title, meta_description, tags, meta_kids = _metadata_fields(item)
        title = _read_optional_text(item.get("titleFile")) or meta_title
        description = _read_optional_text(item.get("descriptionFile")) or meta_description
        spec = UploadSpec(
            content_id=content_id,
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            thumbnail_path=Path(item["thumbnail"]) if item.get("thumbnail") else None,
            captions_path=Path(item["captions"]) if item.get("captions") else None,
            playlist_id=item.get("playlistId"),
            category_id=str(item.get("categoryId", "27")),
            made_for_kids=bool(item.get("madeForKids", meta_kids or False)),
            notify_subscribers=bool(item.get("notifySubscribers", False)),
            is_short=content_id.startswith("content:shorts_main:"),
        )
        spec.validate()
        specs.append(spec)
    if only:
        found = {spec.content_id for spec in specs}
        missing = set(only) - found
        if missing:
            raise StudioUploadError(f"Content ids not found in manifest: {sorted(missing)}")
    return specs


def extract_video_id(page_url: str) -> str | None:
    match = re.search(r"/video/([A-Za-z0-9_-]{11})(?:/|$|\?)", page_url)
    return match.group(1) if match else None


def _attach():
    from playwright.sync_api import sync_playwright

    p = sync_playwright().start()
    browser = p.chromium.connect_over_cdp(CDP_URL, timeout=15000)
    context = browser.contexts[0]
    return p, context


def _studio_page(context) -> Any:
    for page in context.pages:
        if "studio.youtube.com" in page.url:
            return page
    page = context.pages[0] if context.pages else context.new_page()
    page.goto(STUDIO_HOME_URL, wait_until="domcontentloaded")
    return page


def _open_upload_dialog(page) -> None:
    if page.locator("tp-yt-iron-overlay-backdrop.opened").count() > 0:
        _dismiss_dialogs(page)
    page.get_by_role("button", name="创建").first.click()
    page.get_by_text("上传视频", exact=True).first.click()
    page.wait_for_selector("text=拖放", timeout=20000)


def _fill_details(page, spec: UploadSpec) -> None:
    title_box = page.locator("#title-textarea [contenteditable=true], #title-textarea textarea").first
    title_box.wait_for(state="visible", timeout=30000)
    title_box.fill(spec.title)
    desc_box = page.locator("#description-textarea [contenteditable=true], #description-textarea textarea").first
    desc_box.wait_for(state="visible", timeout=10000)
    desc_box.fill(spec.description)
    if spec.thumbnail_path is not None:
        _set_thumbnail(page, spec.thumbnail_path)
    _show_more(page)
    if spec.category_id:
        _set_category(page, spec.category_id)
    if spec.tags:
        _set_tags(page, spec.tags)
    if spec.captions_path is not None:
        _upload_captions(page, spec.captions_path)
    if spec.playlist_id:
        _assign_playlist(page, spec.playlist_id)
    _set_audience(page, spec.made_for_kids)


def _show_more(page) -> None:
    more = page.get_by_role("button", name=re.compile("显示更多|更多选项")).first
    if more.count() > 0:
        more.click()
        page.wait_for_timeout(500)


_CATEGORY_NAMES = {"27": "教育", "22": "人物与博客", "24": "娱乐", "26": "如何与风格", "28": "科学与技术"}


def _set_category(page, category_id: str) -> None:
    name = _CATEGORY_NAMES.get(category_id)
    if not name:
        return
    combo = page.get_by_role("combobox", name=re.compile("类别|Category")).first
    if combo.count() == 0:
        return
    combo.click()
    page.get_by_role("option", name=name).first.click()


def _set_tags(page, tags: list[str]) -> None:
    tag_box = page.get_by_role("textbox", name=re.compile("标记|标签|Tags")).first
    if tag_box.count() == 0:
        return
    tag_box.click()
    for tag in tags:
        tag_box.fill(tag)
        page.keyboard.press("Enter")


def _set_thumbnail(page, thumbnail_path: Path) -> None:
    uploader = page.locator("ytcp-thumbnail-uploader button").first
    if uploader.count() == 0:
        uploader = page.get_by_role("button", name=re.compile("上传缩略图|上传文件|选择文件")).first
    if uploader.count() == 0:
        return
    with page.expect_file_chooser(timeout=15000) as fc:
        uploader.click()
    fc.value.set_files(str(_abs(thumbnail_path)), timeout=30000)


def _upload_captions(page, captions_path: Path) -> None:
    section = page.get_by_text(re.compile("^字幕$")).first
    if section.count() == 0:
        return
    upload_caption = page.get_by_role("button", name=re.compile("上传字幕")).first
    if upload_caption.count() == 0:
        return
    with page.expect_file_chooser(timeout=15000) as fc:
        upload_caption.click()
    fc.value.set_files(str(_abs(captions_path)))
    confirm = page.get_by_role("button", name=re.compile("^上传$")).last
    if confirm.count() > 0:
        confirm.click()


def _assign_playlist(page, playlist_id: str) -> None:
    playlist_button = page.get_by_role("button", name=re.compile("播放列表")).first
    if playlist_button.count() == 0:
        return
    playlist_button.click()
    dialog = page.get_by_role("dialog")
    dialog.wait_for(state="visible", timeout=10000)
    row = dialog.locator(f"a[href*='{playlist_id}']").first
    if row.count() == 0:
        page.keyboard.press("Escape")
        raise StudioUploadError(f"playlist {playlist_id} not found in Studio dialog")
    target = row.locator(
        "xpath=ancestor::*[self::tp-yt-paper-checkbox or self::yt-checkbox-renderer or self::tp-yt-paper-checkbox][1]"
    )
    (target if target.count() > 0 else row).first.click()
    dialog.get_by_role("button", name="完成").click()


def _set_audience(page, made_for_kids: bool) -> None:
    pattern = re.compile("是，内容面向儿童" if made_for_kids else "不，内容并非面向儿童")
    kids = page.get_by_text(pattern).first
    if kids.count() > 0:
        kids.click()


def _advance_wizard(page) -> None:
    for _ in range(5):
        next_button = page.get_by_role("button", name=re.compile("^(下一步|继续)$")).first
        if next_button.count() == 0:
            break
        next_button.click()
        page.wait_for_timeout(800)


def _store_private(page, spec: UploadSpec) -> None:
    radio = page.get_by_role("radio", name=re.compile("^私享$"))
    if radio.count() > 0:
        radio.first.click()
        page.wait_for_timeout(800)
        if radio.first.get_attribute("aria-checked") != "true":
            page.evaluate(
                "() => { const r = [...document.querySelectorAll('tp-yt-paper-radio-button')]"
                ".find(x => x.textContent.includes('私享')); if (r) r.click(); }"
            )
    else:
        page.evaluate(
            "() => { const r = [...document.querySelectorAll('tp-yt-paper-radio-button')]"
            ".find(x => x.textContent.includes('私享')); if (r) r.click(); }"
        )
    page.wait_for_timeout(800)
    if not spec.notify_subscribers:
        promo = page.get_by_text(re.compile("向订阅者宣传|在通知中心")).first
        if promo.count() > 0:
            try:
                promo.click()
            except Exception:  # noqa: BLE001
                pass
    save = page.get_by_role("button", name=re.compile("^(保存|存为私享)$")).first
    save.click()
    page.wait_for_timeout(4000)


def _dismiss_dialogs(page) -> None:
    """Close every Studio dialog/backdrop, including the late 'processing' popup."""
    deadline = time.time() + 75
    while time.time() < deadline:
        clicked = False
        for btn in reversed(page.get_by_role("button", name="关闭").all()):
            try:
                if btn.is_visible() and btn.is_enabled():
                    btn.click()
                    page.wait_for_timeout(1500)
                    clicked = True
                    break
            except Exception:  # noqa: BLE001
                continue
        if not clicked and page.locator("tp-yt-iron-overlay-backdrop.opened").count() == 0:
            page.wait_for_timeout(5000)
            if page.locator("tp-yt-iron-overlay-backdrop.opened").count() == 0:
                for btn in reversed(page.get_by_role("button", name="关闭").all()):
                    try:
                        if btn.is_visible() and btn.is_enabled():
                            btn.click()
                            page.wait_for_timeout(1500)
                            break
                    except Exception:  # noqa: BLE001
                        continue
            if page.locator("tp-yt-iron-overlay-backdrop.opened").count() == 0:
                return
        if not clicked:
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)


def _find_video_id(page, spec: UploadSpec) -> str | None:
    """Locate the freshly saved video in the content list and return its id."""
    vid = extract_video_id(page.url)
    if vid:
        return vid
    tab_name = "Shorts 短视频" if spec.is_short else "视频"
    page.goto(
        "https://studio.youtube.com/channel/UC9QpAkVpv8l1ZQ3X4UtU37A/videos",
        wait_until="domcontentloaded",
    )
    page.wait_for_timeout(3000)
    tab = page.get_by_text(tab_name, exact=True).first
    if tab.count() > 0:
        tab.click()
        page.wait_for_timeout(3000)
    row = page.get_by_text(spec.title, exact=False).first
    row.wait_for(state="visible", timeout=60000)
    row.click()
    try:
        page.wait_for_selector("#title-textarea", timeout=15000)
    except Exception:  # noqa: BLE001
        page.reload(wait_until="domcontentloaded")
        page.wait_for_selector("#title-textarea", timeout=30000)
    return extract_video_id(page.url)


def _abs(path: Path) -> Path:
    return path if path.is_absolute() else (REPO_ROOT / path)


def _set_video_file(page, video_path: Path) -> None:
    """Set the main video through CDP so there is no size cap.

    Playwright refuses to transfer files larger than 50MB over a CDP
    connection ("browser not co-located with the server") even though the
    browser is local. ``DOM.setFileInputFiles`` takes local paths and is
    performed by the browser itself — no transfer, no limit.
    """
    client = page.context.new_cdp_session(page)
    doc = client.send("DOM.getDocument", {"depth": -1})
    node = client.send("DOM.querySelector", {"nodeId": doc["root"]["nodeId"], "selector": "input[type=file]"})
    if not node.get("nodeId"):
        raise StudioUploadError(f"{page.url}: no file input found for video upload")
    client.send("DOM.setFileInputFiles", {"files": [str(video_path)], "nodeId": node["nodeId"]})


def upload_one(context, spec: UploadSpec) -> dict[str, Any]:
    spec.validate()
    page = _studio_page(context)
    if "studio.youtube.com" not in page.url or "/videos/upload" not in page.url:
        page.goto(
            "https://studio.youtube.com/channel/UC9QpAkVpv8l1ZQ3X4UtU37A/videos/upload",
            wait_until="domcontentloaded",
        )
    try:
        page.wait_for_selector("text=拖放", timeout=8000)
    except Exception:  # noqa: BLE001
        _open_upload_dialog(page)
    _set_video_file(page, _abs(spec.video_path))
    _fill_details(page, spec)
    _advance_wizard(page)
    _store_private(page, spec)
    video_id = None
    dialogs = page.locator("ytcp-uploads-dialog")
    if dialogs.count() > 0:
        video_id = dialogs.first.get_attribute("video-id")
    _dismiss_dialogs(page)
    if not video_id:
        video_id = _find_video_id(page, spec)
    result: dict[str, Any] = {
        "contentId": spec.content_id,
        "title": spec.title,
        "video": str(spec.video_path),
        "videoId": video_id,
        "visibility": "private",
        "uploadedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    UPLOAD_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = _sidecar_path(spec.content_id)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def publish_one(context, video_id: str) -> dict[str, Any]:
    """Flip a private video to public from its edit page."""
    page = _studio_page(context)
    page.goto(f"https://studio.youtube.com/video/{video_id}/edit", wait_until="domcontentloaded")
    page.wait_for_selector("#title-textarea", timeout=30000)
    page.wait_for_timeout(2000)
    vis_card = page.get_by_text("公开范围", exact=True).first
    vis_card.wait_for(state="visible", timeout=20000)
    vis_card.click()
    page.wait_for_timeout(1000)
    radio = page.get_by_role("radio", name=re.compile("^公开$")).first
    radio.wait_for(state="visible", timeout=10000)
    radio.click()
    page.wait_for_timeout(1000)
    save = page.get_by_role("button", name=re.compile("^(保存|发布)$")).first
    save.click()
    page.wait_for_timeout(2000)
    confirm = page.get_by_role("button", name=re.compile("^(发布|确认)$")).first
    if confirm.count() > 0 and confirm.is_visible() and confirm.is_enabled():
        confirm.click()
    page.wait_for_timeout(3000)
    return {"videoId": video_id, "visibility": "public", "publishedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z")}


def _sidecar_path(content_id: str) -> Path:
    return UPLOAD_RESULTS_DIR / (re.sub(r"[^A-Za-z0-9_.-]", "_", content_id) + ".json")


def _load_sidecar(content_id: str) -> dict[str, Any] | None:
    path = _sidecar_path(content_id)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def publish_many(content_ids: list[str]) -> list[dict[str, Any]]:
    """Publish previously uploaded (private) videos by content id sidecar."""
    targets: list[tuple[str, str]] = []
    for content_id in content_ids:
        sidecar = _load_sidecar(content_id)
        if not sidecar or not sidecar.get("videoId"):
            raise StudioUploadError(f"{content_id}: no upload sidecar with videoId in {UPLOAD_RESULTS_DIR}")
        targets.append((content_id, sidecar["videoId"]))
    p, context = _attach()
    results: list[dict[str, Any]] = []
    try:
        for content_id, video_id in targets:
            print(f"[studio] publishing {content_id} videoId={video_id}", flush=True)
            result = publish_one(context, video_id)
            result["contentId"] = content_id
            sidecar = _load_sidecar(content_id) or {}
            sidecar.update(result)
            _sidecar_path(content_id).write_text(
                json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            results.append(result)
            print(f"[studio] public: {content_id}", flush=True)
    finally:
        p.stop()
    return results


def upload_many(specs: list[UploadSpec]) -> list[dict[str, Any]]:
    p, context = _attach()
    results: list[dict[str, Any]] = []
    try:
        for spec in specs:
            print(f"[studio] uploading {spec.content_id} <- {spec.video_path}", flush=True)
            results.append(upload_one(context, spec))
            print(f"[studio] stored private: {spec.content_id} videoId={results[-1]['videoId']}", flush=True)
    finally:
        p.stop()
    return results
