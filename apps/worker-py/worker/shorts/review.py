from __future__ import annotations

import json
import statistics
from datetime import date
from pathlib import Path
from typing import Any

from .analytics import derived_metrics, load_latest_metrics, median_metrics
from .workspace import atomic_write_json, operation_root


REVIEW_SCHEMA = "elr-shorts-weekly-review-v1"
WEIGHTS = {
    "engaged_view_rate": 0.35,
    "average_percentage_viewed": 0.30,
    "subscribers_per_1000_engaged": 0.15,
    "long_form_views_per_1000_engaged": 0.10,
    "interactions_per_1000_engaged": 0.10,
}


def _ratio(value: float, baseline: float) -> float:
    if baseline <= 0:
        return 1.0 if value > 0 else 0.0
    return max(0.0, min(2.0, value / baseline))


def score(row: dict[str, Any], baseline: dict[str, float]) -> float:
    metrics = derived_metrics(row)
    return sum(WEIGHTS[key] * _ratio(metrics[key], baseline.get(key, 0.0)) for key in WEIGHTS)


def _variant_summary(rows: list[dict[str, Any]], baseline: dict[str, float]) -> dict[str, Any]:
    metrics = [derived_metrics(row) for row in rows]
    return {
        "entryCount": len(rows),
        "engagedViews": round(sum(float(row.get("engaged_views", 0.0)) for row in rows), 3),
        "score": round(statistics.mean(score(row, baseline) for row in rows), 4),
        "engagedViewRate": round(statistics.mean(item["engaged_view_rate"] for item in metrics), 4),
        "averagePercentageViewed": round(
            statistics.mean(item["average_percentage_viewed"] for item in metrics), 3
        ),
        "subscribersPer1000Engaged": round(
            statistics.mean(item["subscribers_per_1000_engaged"] for item in metrics), 3
        ),
        "longFormViewsPer1000Engaged": round(
            statistics.mean(item["long_form_views_per_1000_engaged"] for item in metrics), 3
        ),
    }


def build_review(
    repo_root: Path,
    product: dict[str, Any],
    portfolio: dict[str, Any],
    *,
    cutoff: str | None = None,
) -> dict[str, Any]:
    cutoff = cutoff or date.today().isoformat()
    latest = load_latest_metrics(repo_root, cutoff=cutoff)
    available = [latest[str(entry["shortId"])] for entry in portfolio["entries"] if str(entry["shortId"]) in latest]
    baseline = median_metrics(available)
    experiments: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for entry in portfolio["entries"]:
        row = latest.get(str(entry["shortId"]))
        if row is None:
            continue
        for experiment, variant in dict(entry["experimentAssignments"]).items():
            experiments.setdefault(str(experiment), {}).setdefault(str(variant), []).append(row)
    minimum_entries = int(product["experiments"]["minimumEntriesPerVariant"])
    minimum_engaged = float(product["experiments"]["minimumEngagedViewsPerVariant"])
    required_lift = float(product["experiments"]["winnerRelativeLift"])
    guardrail_drop = float(product["experiments"]["secondaryGuardrailDrop"])
    decisions: list[dict[str, Any]] = []
    for experiment, variants in sorted(experiments.items()):
        summaries = {
            variant: _variant_summary(rows, baseline)
            for variant, rows in sorted(variants.items())
        }
        qualified = [
            variant
            for variant, summary in summaries.items()
            if summary["entryCount"] >= minimum_entries and summary["engagedViews"] >= minimum_engaged
        ]
        decision = "hold"
        winner = None
        loser = None
        reason = "Need more matched entries or engaged views."
        if len(qualified) >= 2:
            ranked = sorted(qualified, key=lambda variant: summaries[variant]["score"], reverse=True)
            winner, loser = ranked[0], ranked[1]
            winner_summary = summaries[winner]
            loser_summary = summaries[loser]
            relative_lift = (
                winner_summary["score"] / loser_summary["score"] - 1.0
                if loser_summary["score"] > 0
                else 1.0
            )
            primary_guardrail = (
                winner_summary["engagedViewRate"]
                >= loser_summary["engagedViewRate"] * (1.0 - guardrail_drop)
                and winner_summary["averagePercentageViewed"]
                >= loser_summary["averagePercentageViewed"] * (1.0 - guardrail_drop)
            )
            if relative_lift >= required_lift and primary_guardrail:
                decision = "scale"
                reason = f"{winner} leads {loser} by {relative_lift:.1%} with primary guardrails intact."
            else:
                reason = f"Observed lift {relative_lift:.1%} is below the decision threshold or breaks a guardrail."
        decisions.append(
            {
                "experiment": experiment,
                "decision": decision,
                "winner": winner if decision == "scale" else None,
                "loser": loser if decision == "scale" else None,
                "reason": reason,
                "variants": summaries,
            }
        )
    scored = [
        {
            "shortId": short_id,
            "score": round(score(row, baseline), 4),
            "metrics": derived_metrics(row),
            "observedOn": row["observedOn"],
        }
        for short_id, row in latest.items()
    ]
    entry_by_id = {str(entry["shortId"]): entry for entry in portfolio["entries"]}
    format_scores: dict[str, list[float]] = {}
    for item in scored:
        entry = entry_by_id.get(str(item["shortId"]))
        if entry is not None:
            format_scores.setdefault(str(entry["format"]), []).append(float(item["score"]))
    format_performance = {
        format_name: {
            "entryCount": len(values),
            "meanScore": round(statistics.mean(values), 4),
        }
        for format_name, values in sorted(format_scores.items())
    }
    next_formats = dict(product["formatAllocation"])
    if len(available) >= 8 and len(format_performance) >= 2:
        ranked_formats = sorted(
            format_performance,
            key=lambda format_name: format_performance[format_name]["meanScore"],
            reverse=True,
        )
        best_format = ranked_formats[0]
        weakest_format = ranked_formats[-1]
        best_score = float(format_performance[best_format]["meanScore"])
        weakest_score = float(format_performance[weakest_format]["meanScore"])
        if weakest_score > 0 and best_score / weakest_score - 1.0 >= required_lift:
            if next_formats[weakest_format] > 1 and next_formats[best_format] < 6:
                next_formats[weakest_format] -= 1
                next_formats[best_format] += 1
    defaults = {
        item["experiment"]: item["winner"]
        for item in decisions
        if item["decision"] == "scale" and item.get("winner")
    }
    repeat_experiments = [item["experiment"] for item in decisions if item["decision"] == "hold"]
    return {
        "schema": REVIEW_SCHEMA,
        "cycleId": portfolio["cycleId"],
        "cutoff": cutoff,
        "coverage": {"planned": len(portfolio["entries"]), "measured": len(available)},
        "baseline": baseline,
        "experiments": decisions,
        "formatPerformance": format_performance,
        "shorts": sorted(scored, key=lambda item: item["score"], reverse=True),
        "nextPlan": {
            "portfolioSize": int(product["pilotSize"]),
            "formatAllocation": next_formats,
            "contentAllocation": product["experiments"]["allocation"],
            "defaultWinningVariants": defaults,
            "repeatExperiments": repeat_experiments,
            "publishingSlots": product["publishing"]["slots"],
            "instruction": (
                "Create new concepts and shortIds; never reuse scripts or content keys. "
                "Apply winning variants to proven content and repeat only inconclusive tests."
            ),
        },
    }


def write_review(repo_root: Path, review: dict[str, Any]) -> tuple[Path, Path]:
    review_dir = operation_root(repo_root) / "reviews"
    review_id = str(review["cutoff"])
    json_path = review_dir / f"{review_id}.json"
    markdown_path = review_dir / f"{review_id}.md"
    atomic_write_json(json_path, review)
    lines = [
        f"# Shorts review — {review_id}",
        "",
        f"Coverage: {review['coverage']['measured']}/{review['coverage']['planned']} planned Shorts measured.",
        "",
        "## Experiment decisions",
        "",
    ]
    for experiment in review["experiments"]:
        winner = f"; winner: {experiment['winner']}" if experiment.get("winner") else ""
        lines.append(f"- **{experiment['experiment']}** — {experiment['decision']}{winner}. {experiment['reason']}")
    lines.extend(["", "## Ranked Shorts", ""])
    for item in review["shorts"]:
        lines.append(f"- `{item['shortId']}` — score {item['score']:.3f} ({item['observedOn']})")
    lines.extend(["", "## Next plan", ""])
    lines.append(
        "- Format allocation: "
        + ", ".join(
            f"{key}={value}" for key, value in sorted(review["nextPlan"]["formatAllocation"].items())
        )
    )
    if review["nextPlan"]["defaultWinningVariants"]:
        lines.append(
            "- Default winning variants: "
            + ", ".join(
                f"{key}={value}"
                for key, value in sorted(review["nextPlan"]["defaultWinningVariants"].items())
            )
        )
    if review["nextPlan"]["repeatExperiments"]:
        lines.append("- Repeat experiments: " + ", ".join(review["nextPlan"]["repeatExperiments"]))
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return json_path, markdown_path
