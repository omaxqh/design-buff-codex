#!/usr/bin/env python3

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Set


REQUIRED_TOP_LEVEL_KEYS: Set[str] = {
    "schema_version",
    "meta",
    "intake",
    "coverage",
    "background",
    "evidence",
    "issues",
    "priorities",
    "history",
}

FORBIDDEN_KEYS: Set[str] = {
    "what_i_see",
    "why_it_is_a_problem",
    "what_misunderstanding_it_reveals",
    "likely_consequence",
    "recommended_direction",
    "adopted_or_recommended_path",
    "executive_summary",
}

HTML_LANG_RE = re.compile(r"<html[^>]*\blang=[\"']([^\"']+)[\"']", re.IGNORECASE)
REQUIRED_SECTION_IDS: Set[str] = {
    "review-overview",
    "executive-summary",
    "highest-priority-issue",
    "background-and-evidence",
    "full-review",
    "issue-list",
    "three-flow-consistency",
    "resolution-tracks",
    "open-questions",
    "next-actions",
}
ENGLISH_SCAFFOLD_TOKENS: Set[str] = {
    "Executive Summary",
    "Issue List",
    "Resolution Tracks",
    "Open Questions",
    "Next Actions",
    "Background and Evidence",
    "Full Review",
    "Three-Flow Consistency",
    "Project",
    "Review Slug",
    "Review Date",
    "Top Priority",
    "Verdict",
    "Intake",
}


def collect_keys(value) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from collect_keys(child)
    elif isinstance(value, list):
        for item in value:
            yield from collect_keys(item)


def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate_report_html(report_path: Path, state: Dict, errors: List[str]) -> None:
    if not report_path.exists():
        errors.append(f"{report_path.parent}: missing report.html")
        return

    html = load_text(report_path)
    lowered = html.lower()

    if "<html" not in lowered or "</html>" not in lowered:
        errors.append(f"{report_path}: does not look like a complete HTML document")

    if 'data-design-buff-report="v1"' not in html and "data-design-buff-report='v1'" not in html:
        errors.append(f"{report_path}: missing body marker data-design-buff-report=\"v1\"")

    if "design-buff-template" not in html or "human-report-html-v1" not in html:
        errors.append(f"{report_path}: missing design-buff HTML template marker")

    lang_match = HTML_LANG_RE.search(html)
    if not lang_match:
        errors.append(f"{report_path}: missing <html lang=\"...\"> attribute")
    else:
        report_language = state.get("meta", {}).get("report_language")
        if report_language and lang_match.group(1) != report_language:
            errors.append(
                f"{report_path}: html lang '{lang_match.group(1)}' does not match meta.report_language '{report_language}'"
            )

    for section_id in REQUIRED_SECTION_IDS:
        if f'id="{section_id}"' not in html and f"id='{section_id}'" not in html:
            errors.append(f"{report_path}: missing required section id '{section_id}'")

    issues = state.get("issues", [])
    for issue in issues:
        stable_id = issue.get("stable_id")
        display_number = issue.get("display_number")
        if stable_id and stable_id not in html:
            errors.append(f"{report_path}: missing issue stable_id '{stable_id}' in human report")
        if display_number and display_number not in html:
            errors.append(f"{report_path}: missing issue display number '{display_number}' in human report")

    report_language = state.get("meta", {}).get("report_language", "")
    if report_language.startswith("zh"):
        for token in sorted(ENGLISH_SCAFFOLD_TOKENS):
            if token in html:
                errors.append(
                    f"{report_path}: report_language is '{report_language}' but contains English scaffold token '{token}'"
                )


def validate_review_root(review_root: Path, errors: List[str], warnings: List[str]) -> None:
    report_path = review_root / "report.html"
    state_path = review_root / "review-state.json"

    if not state_path.exists():
        errors.append(f"{review_root}: missing review-state.json")
        return

    try:
        state = load_json(state_path)
    except Exception as exc:  # pragma: no cover - defensive
        errors.append(f"{state_path}: invalid JSON ({exc})")
        return

    validate_report_html(report_path, state, errors)

    missing_top_level = REQUIRED_TOP_LEVEL_KEYS - set(state.keys())
    if missing_top_level:
        errors.append(f"{state_path}: missing top-level keys: {', '.join(sorted(missing_top_level))}")

    if state.get("schema_version") != "v1":
        errors.append(f"{state_path}: schema_version must be 'v1'")

    meta = state.get("meta", {})
    if meta.get("review_slug") != review_root.name:
        errors.append(
            f"{state_path}: meta.review_slug='{meta.get('review_slug')}' does not match folder '{review_root.name}'"
        )

    if not meta.get("report_language"):
        errors.append(f"{state_path}: meta.report_language is required")

    if not meta.get("language_source"):
        errors.append(f"{state_path}: meta.language_source is required")

    issues = state.get("issues", [])
    for index, issue in enumerate(issues):
        stable_id = issue.get("stable_id")
        display_number = issue.get("display_number")
        if not stable_id:
            errors.append(f"{state_path}: issues[{index}] missing stable_id")
        if not display_number:
            errors.append(f"{state_path}: issues[{index}] missing display_number")

    forbidden_found = sorted(FORBIDDEN_KEYS.intersection(set(collect_keys(state))))
    if forbidden_found:
        errors.append(
            f"{state_path}: contains forbidden human-facing prose keys: {', '.join(forbidden_found)}"
        )

    priorities = state.get("priorities", {})
    if priorities.get("highest_priority_issue_id") and priorities.get("highest_priority_issue_id") not in {
        issue.get("stable_id") for issue in issues
    }:
        warnings.append(f"{state_path}: priorities.highest_priority_issue_id does not match any issue stable_id")


def validate_hidden_scratch(hidden_root: Path, errors: List[str]) -> None:
    if not hidden_root.exists():
        return

    for path in hidden_root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".md":
            errors.append(f"{path}: hidden scratch may not contain Markdown review artifacts")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate design-buff review roots and hidden scratch.")
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Project root containing design-buff-reviews/ and optional .design-buff/",
    )
    args = parser.parse_args()

    project_root = Path(args.root).resolve()
    review_root = project_root / "design-buff-reviews"
    hidden_root = project_root / ".design-buff"

    errors: List[str] = []
    warnings: List[str] = []

    if not review_root.exists():
        errors.append(f"{review_root}: missing design-buff-reviews directory")
    else:
        for child in sorted(review_root.iterdir()):
            if child.name.startswith(".") or not child.is_dir():
                continue
            validate_review_root(child, errors, warnings)

    validate_hidden_scratch(hidden_root, errors)

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"- {warning}")
        return 1

    print("Validation passed.")
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
