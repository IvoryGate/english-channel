from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


PRODUCT_SCHEMA = "elr-shorts-product-v1"
PORTFOLIO_SCHEMA = "elr-shorts-portfolio-v1"
MANIFEST_SCHEMA = "elr-short-manifest-v1"
VALID_FORMATS = {"micro_story", "listen_choose", "dialogue", "classic_cliffhanger"}
VALID_CEFR = {"A2", "B1"}
VALID_HOOK_STYLES = {"question", "statement"}
SHORT_ID_RE = re.compile(r"^elr-s-\d{3}$")


class ContractError(ValueError):
    """Raised when a durable Shorts contract is invalid."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"Missing contract: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"Expected a JSON object in {path}")
    return value


def _required_string(value: dict[str, Any], key: str, where: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise ContractError(f"{where}.{key} must be a non-empty string")
    return item.strip()


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)?", text))


def _normalized_text(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def content_key(entry: dict[str, Any]) -> str:
    payload = {
        "format": entry["format"],
        "hook": _normalized_text(str(entry["hook"])),
        "turns": [
            {
                "speaker": str(turn["speaker"]).casefold(),
                "text": _normalized_text(str(turn["text"])),
            }
            for turn in entry["turns"]
        ],
        "prompt": _normalized_text(str(entry["prompt"])),
        "answer": _normalized_text(str(entry["answer"])),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_product(product: dict[str, Any]) -> None:
    if product.get("schema") != PRODUCT_SCHEMA:
        raise ContractError(f"product.schema must be {PRODUCT_SCHEMA}")
    allocation = product.get("formatAllocation")
    if not isinstance(allocation, dict) or set(allocation) != VALID_FORMATS:
        raise ContractError(f"product.formatAllocation must define exactly {sorted(VALID_FORMATS)}")
    if any(not isinstance(value, int) or value < 0 for value in allocation.values()):
        raise ContractError("product.formatAllocation values must be non-negative integers")
    pilot_size = product.get("pilotSize")
    if pilot_size != sum(allocation.values()):
        raise ContractError("product.pilotSize must equal the format allocation total")
    quality = product.get("quality")
    if not isinstance(quality, dict):
        raise ContractError("product.quality must be an object")
    required_numbers = (
        "durationMinSec",
        "durationTargetMaxSec",
        "durationHardMaxSec",
        "titleTargetMaxChars",
        "titleHardMaxChars",
        "width",
        "height",
        "fps",
    )
    for key in required_numbers:
        if not isinstance(quality.get(key), (int, float)):
            raise ContractError(f"product.quality.{key} must be numeric")
    if quality["durationMinSec"] >= quality["durationHardMaxSec"]:
        raise ContractError("durationMinSec must be below durationHardMaxSec")
    cutoff = quality.get("durationVariantCutoffSec")
    if not isinstance(cutoff, (int, float)) or not (
        quality["durationMinSec"] <= cutoff < quality["durationHardMaxSec"]
    ):
        raise ContractError("durationVariantCutoffSec must sit inside the allowed duration range")
    visual = product.get("visual")
    if not isinstance(visual, dict) or visual.get("backgroundStrategy") != "generated_editorial_scene":
        raise ContractError("product.visual must define the generated editorial background strategy")
    _required_string(visual, "brandLogo", "product.visual")
    cta = product.get("cta")
    if not isinstance(cta, dict) or not cta.get("enabled"):
        raise ContractError("product.cta must be enabled")
    cta_copy = _required_string(cta, "defaultCopy", "product.cta")
    if len(cta_copy) > int(cta.get("maxChars", 0)):
        raise ContractError("product.cta.defaultCopy exceeds maxChars")
    publishing = product.get("publishing")
    if not isinstance(publishing, dict) or publishing.get("defaultPrivacy") != "private":
        raise ContractError("publishing.defaultPrivacy must remain private for the pilot")
    experiments = product.get("experiments")
    if not isinstance(experiments, dict) or int(experiments.get("minimumEntriesPerVariant", 0)) < 2:
        raise ContractError("experiments.minimumEntriesPerVariant must be at least 2")


def validate_entry(entry: dict[str, Any], product: dict[str, Any], where: str) -> None:
    short_id = _required_string(entry, "shortId", where)
    if not SHORT_ID_RE.fullmatch(short_id):
        raise ContractError(f"{where}.shortId must match elr-s-NNN")
    title = _required_string(entry, "title", where)
    hard_title_limit = int(product["quality"]["titleHardMaxChars"])
    if len(title) > hard_title_limit:
        raise ContractError(f"{where}.title exceeds {hard_title_limit} characters")
    format_name = _required_string(entry, "format", where)
    if format_name not in VALID_FORMATS:
        raise ContractError(f"{where}.format must be one of {sorted(VALID_FORMATS)}")
    cefr = _required_string(entry, "cefr", where)
    if cefr not in VALID_CEFR:
        raise ContractError(f"{where}.cefr must be one of {sorted(VALID_CEFR)}")
    duration = entry.get("durationSec")
    quality = product["quality"]
    if not isinstance(duration, (int, float)):
        raise ContractError(f"{where}.durationSec must be numeric")
    if not float(quality["durationMinSec"]) <= float(duration) <= float(quality["durationHardMaxSec"]):
        raise ContractError(
            f"{where}.durationSec must be between {quality['durationMinSec']} and "
            f"{quality['durationHardMaxSec']}"
        )
    hook_style = _required_string(entry, "hookStyle", where)
    if hook_style not in VALID_HOOK_STYLES:
        raise ContractError(f"{where}.hookStyle must be one of {sorted(VALID_HOOK_STYLES)}")
    _required_string(entry, "hook", where)
    thumbnail_headline = _required_string(entry, "thumbnailHeadline", where)
    if len(thumbnail_headline) > 32:
        raise ContractError(f"{where}.thumbnailHeadline exceeds 32 characters")
    _required_string(entry, "prompt", where)
    _required_string(entry, "answer", where)
    _required_string(entry, "relatedShow", where)
    _required_string(entry, "visualBrief", where)
    background_image = entry.get("backgroundImage")
    if background_image is not None and (
        not isinstance(background_image, str) or not background_image.strip()
    ):
        raise ContractError(f"{where}.backgroundImage must be null or a non-empty string")
    related_video = entry.get("relatedVideoId")
    if related_video is not None and (not isinstance(related_video, str) or not related_video.strip()):
        raise ContractError(f"{where}.relatedVideoId must be null or a non-empty string")
    turns = entry.get("turns")
    if not isinstance(turns, list) or not turns:
        raise ContractError(f"{where}.turns must contain at least one turn")
    speakers: set[str] = set()
    for index, turn in enumerate(turns):
        if not isinstance(turn, dict):
            raise ContractError(f"{where}.turns[{index}] must be an object")
        speakers.add(_required_string(turn, "speaker", f"{where}.turns[{index}]") )
        text = _required_string(turn, "text", f"{where}.turns[{index}]")
        if _word_count(text) > 45:
            raise ContractError(f"{where}.turns[{index}] is too dense for a mobile caption scene")
    if format_name == "dialogue" and len(speakers) < 2:
        raise ContractError(f"{where} dialogue must use at least two speakers")
    if format_name != "dialogue" and len(speakers) != 1:
        raise ContractError(f"{where} non-dialogue format must use exactly one speaker")
    assignments = entry.get("experimentAssignments")
    if not isinstance(assignments, dict) or not assignments:
        raise ContractError(f"{where}.experimentAssignments must be a non-empty object")
    if assignments.get("hook") != hook_style:
        raise ContractError(f"{where} hook experiment must match hookStyle")
    expected_duration = (
        "short" if float(duration) <= float(quality["durationVariantCutoffSec"]) else "long"
    )
    if assignments.get("duration") != expected_duration:
        raise ContractError(f"{where} duration experiment must be {expected_duration}")
    spoken_words = sum(
        _word_count(str(value))
        for value in [
            entry["hook"],
            *(turn["text"] for turn in turns),
            entry["prompt"],
            entry["answer"],
        ]
    )
    minimum_words = int(float(duration) * (2.1 if expected_duration == "short" else 2.15))
    if spoken_words < minimum_words:
        raise ContractError(
            f"{where} has {spoken_words} spoken words; at least {minimum_words} are required "
            f"for the {expected_duration} duration treatment"
        )


def validate_portfolio(portfolio: dict[str, Any], product: dict[str, Any]) -> None:
    if portfolio.get("schema") != PORTFOLIO_SCHEMA:
        raise ContractError(f"portfolio.schema must be {PORTFOLIO_SCHEMA}")
    _required_string(portfolio, "cycleId", "portfolio")
    entries = portfolio.get("entries")
    if not isinstance(entries, list) or len(entries) != int(product["pilotSize"]):
        raise ContractError(f"portfolio.entries must contain exactly {product['pilotSize']} entries")
    ids: set[str] = set()
    keys: set[str] = set()
    actual_allocation = {name: 0 for name in VALID_FORMATS}
    experiment_counts: dict[str, dict[str, int]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ContractError(f"portfolio.entries[{index}] must be an object")
        where = f"portfolio.entries[{index}]"
        validate_entry(entry, product, where)
        short_id = str(entry["shortId"])
        if short_id in ids:
            raise ContractError(f"Duplicate shortId: {short_id}")
        ids.add(short_id)
        key = content_key(entry)
        if key in keys:
            raise ContractError(f"Duplicate content detected at {short_id}")
        keys.add(key)
        actual_allocation[str(entry["format"])] += 1
        for experiment, variant in dict(entry["experimentAssignments"]).items():
            experiment_counts.setdefault(str(experiment), {}).setdefault(str(variant), 0)
            experiment_counts[str(experiment)][str(variant)] += 1
    if actual_allocation != product["formatAllocation"]:
        raise ContractError(
            f"Portfolio allocation {actual_allocation} does not match product allocation "
            f"{product['formatAllocation']}"
        )
    minimum = int(product["experiments"]["minimumEntriesPerVariant"])
    for experiment, variants in experiment_counts.items():
        if len(variants) < 2:
            raise ContractError(f"Experiment {experiment} must have at least two variants")
        for variant, count in variants.items():
            if count < minimum:
                raise ContractError(
                    f"Experiment {experiment}/{variant} has {count} entries; minimum is {minimum}"
                )


def load_and_validate(product_path: Path, portfolio_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    product = load_json(product_path)
    portfolio = load_json(portfolio_path)
    validate_product(product)
    validate_portfolio(portfolio, product)
    return product, portfolio


def build_manifest(entry: dict[str, Any], product: dict[str, Any], cycle_id: str) -> dict[str, Any]:
    duration = float(entry["durationSec"])
    turns = []
    spoken_weight = sum(max(1, _word_count(str(turn["text"]))) for turn in entry["turns"])
    body_start = 1.5
    body_end = max(body_start + 1.0, duration - 9.0)
    cursor = body_start
    for index, source in enumerate(entry["turns"], start=1):
        weight = max(1, _word_count(str(source["text"])))
        turn_duration = (body_end - body_start) * weight / spoken_weight
        turns.append(
            {
                "id": f"t{index:03d}",
                "order": index,
                "speaker": source["speaker"],
                "text": source["text"],
                "wordCount": weight,
                "startSec": round(cursor, 3),
                "endSec": round(cursor + turn_duration, 3),
                "filename": f"turn_{index:03d}.wav",
            }
        )
        cursor += turn_duration
    return {
        "schema": MANIFEST_SCHEMA,
        "shortId": entry["shortId"],
        "cycleId": cycle_id,
        "contentKey": content_key(entry),
        "format": entry["format"],
        "cefr": entry["cefr"],
        "durationPlannedSec": duration,
        "durationSec": duration,
        "fps": int(product["quality"]["fps"]),
        "width": int(product["quality"]["width"]),
        "height": int(product["quality"]["height"]),
        "title": entry["title"],
        "thumbnailHeadline": entry["thumbnailHeadline"],
        "description": (
            f"Practice {entry['cefr']} English listening in under one minute. "
            f"Answer: {entry['answer']}"
        ),
        "hookStyle": entry["hookStyle"],
        "hook": entry["hook"],
        "hookEndSec": body_start,
        "turns": turns,
        "prompt": entry["prompt"],
        "answer": entry["answer"],
        "promptStartSec": round(max(body_end, duration - 9.0), 3),
        "answerStartSec": round(max(body_end + 3.0, duration - 4.5), 3),
        "relatedShow": entry["relatedShow"],
        "relatedVideoId": entry.get("relatedVideoId"),
        "visual": {
            "brief": entry["visualBrief"],
            "backgroundImage": entry.get("backgroundImage"),
            "brandLogo": product["visual"]["brandLogo"],
            "artDirection": product["visual"]["artDirection"],
        },
        "cta": product["cta"]["defaultCopy"],
        "experimentAssignments": entry["experimentAssignments"],
        "publication": {"status": "planned", "privacy": "private"},
        "renderSettings": {
            "interTurnSilenceSec": 0.12,
            "durationVariantCutoffSec": product["quality"]["durationVariantCutoffSec"],
            "loudnessTargetLufs": product["quality"]["loudnessTargetLufs"],
            "truePeakMaxDb": product["quality"]["truePeakMaxDb"],
            "audioSampleRate": product["quality"]["audioSampleRate"],
        },
    }
