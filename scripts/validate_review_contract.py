#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set
from urllib.parse import parse_qs, urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = REPO_ROOT / "templates" / "report-shell.html"
HTML_LANG_RE = re.compile(r"<html[^>]*\blang=[\"']([^\"']+)[\"']", re.IGNORECASE)
CLASS_ATTR_RE = re.compile(r'class=["\']([^"\']+)["\']')
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
FORBIDDEN_KEYS: Set[str] = {
    "what_i_see",
    "why_it_is_a_problem",
    "what_misunderstanding_it_reveals",
    "likely_consequence",
    "recommended_direction",
    "adopted_or_recommended_path",
    "executive_summary",
}
FLOW_PROBLEM_LABELS = ("问题：", "Problem:", "Problem：")
FLOW_SOLUTION_LABELS = ("解法：", "Solution:", "Solution：", "Fix:", "Fix：")
RENDER_FRAGMENT_CLASSES: Set[str] = {
    "issue-card",
    "issue-meta",
    "timeline-node",
    "timeline-stage",
    "timeline-dot",
    "timeline-stage-text",
    "timeline-stage-title",
    "timeline-stage-summary",
    "timeline-card",
    "timeline-summary",
    "timeline-block",
    "inline-label",
}


@dataclass
class Node:
    tag: str
    attrs: Dict[str, str]
    parent: Optional["Node"] = None
    children: List["Node"] = field(default_factory=list)
    texts: List[str] = field(default_factory=list)

    @property
    def classes(self) -> Set[str]:
        value = self.attrs.get("class", "")
        return {item for item in value.split() if item}

    def append_child(self, node: "Node") -> None:
        self.children.append(node)


class MiniHTMLParser(HTMLParser):
    VOID_TAGS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("document", {})
        self.stack: List[Node] = [self.root]

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        normalized = {key: (value or "") for key, value in attrs}
        node = Node(tag.lower(), normalized, self.stack[-1])
        self.stack[-1].append_child(node)
        if tag.lower() not in self.VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        normalized = {key: (value or "") for key, value in attrs}
        node = Node(tag.lower(), normalized, self.stack[-1])
        self.stack[-1].append_child(node)

    def handle_endtag(self, tag: str) -> None:
        target = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == target:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if data:
            self.stack[-1].texts.append(data)


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


def normalize_node_id(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.replace("-", ":")


def intake_node_from_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    parsed = urlparse(str(url))
    return normalize_node_id(parse_qs(parsed.query).get("node-id", [None])[0])


def parse_html(html: str) -> Node:
    parser = MiniHTMLParser()
    parser.feed(html)
    parser.close()
    return parser.root


def walk(node: Node) -> Iterable[Node]:
    yield node
    for child in node.children:
        yield from walk(child)


def find_by_id(node: Node, target_id: str) -> Optional[Node]:
    for child in walk(node):
        if child.attrs.get("id") == target_id:
            return child
    return None


def find_first(node: Node, predicate) -> Optional[Node]:
    for child in walk(node):
        if predicate(child):
            return child
    return None


def find_all(node: Node, predicate) -> List[Node]:
    return [child for child in walk(node) if predicate(child)]


def text_content(node: Node) -> str:
    parts = list(node.texts)
    for child in node.children:
        parts.append(text_content(child))
    return "".join(parts)


def normalize_text(value: str) -> str:
    return " ".join(value.split())


def is_descendant(node: Optional[Node], ancestor: Optional[Node]) -> bool:
    if not node or not ancestor:
        return False
    current = node
    while current is not None:
        if current is ancestor:
            return True
        current = current.parent
    return False


def nearest_ancestor_with_class(node: Optional[Node], class_name: str) -> Optional[Node]:
    current = node
    while current is not None:
        if class_name in current.classes:
            return current
        current = current.parent
    return None


def direct_children_with_class(node: Node, class_name: str) -> List[Node]:
    return [child for child in node.children if class_name in child.classes]


def template_dom_classes() -> Set[str]:
    template_html = load_text(TEMPLATE_PATH)
    classes: Set[str] = set()
    for value in CLASS_ATTR_RE.findall(template_html):
        classes.update(item for item in value.split() if item)
    return classes | RENDER_FRAGMENT_CLASSES


def validate_required_sections(root: Node, report_path: Path, errors: List[str]) -> None:
    for section_id in REQUIRED_SECTION_IDS:
        if not find_by_id(root, section_id):
            errors.append(f"{report_path}: missing required section id '{section_id}'")


def validate_template_classes(html: str, report_path: Path, errors: List[str]) -> None:
    allowed = template_dom_classes()
    used: Set[str] = set()
    for value in CLASS_ATTR_RE.findall(html):
        used.update(item for item in value.split() if item)
    unexpected = sorted(used - allowed)
    if unexpected:
        errors.append(
            f"{report_path}: uses template-external classes: {', '.join(unexpected)}"
        )


def validate_report_structure(report_path: Path, state: Dict, html: str, root: Node, errors: List[str]) -> None:
    overview = find_by_id(root, "review-overview")
    executive_summary = find_by_id(root, "executive-summary")
    full_review = find_by_id(root, "full-review")
    issue_list = find_by_id(root, "issue-list")
    three_flow = find_by_id(root, "three-flow-consistency")
    resolution_tracks = find_by_id(root, "resolution-tracks")
    open_questions = find_by_id(root, "open-questions")
    next_actions = find_by_id(root, "next-actions")
    project_name = state.get("meta", {}).get("project_name")

    if not project_name:
        errors.append(f"{report_path}: meta.project_name is required for slot validation")
    if overview:
        h1 = find_first(overview, lambda node: node.tag == "h1")
        if not h1:
            errors.append(f"{report_path}: #review-overview must contain an h1")
        elif project_name and normalize_text(text_content(h1)) != normalize_text(str(project_name)):
            errors.append(
                f"{report_path}: #review-overview h1 must equal meta.project_name '{project_name}'"
            )

    if executive_summary:
        if executive_summary.tag != "aside" or "hero-panel" not in executive_summary.classes:
            errors.append(f"{report_path}: #executive-summary must render as aside.hero-panel")
        if not is_descendant(executive_summary, overview):
            errors.append(f"{report_path}: #executive-summary must live inside #review-overview")

    if issue_list and not is_descendant(issue_list, full_review):
        errors.append(f"{report_path}: #issue-list must be nested inside #full-review")

    if three_flow:
        timeline_nodes = find_all(three_flow, lambda node: "timeline-node" in node.classes)
        if len(timeline_nodes) < 4:
            errors.append(f"{report_path}: #three-flow-consistency must contain at least 4 .timeline-node items")
        for index, node in enumerate(timeline_nodes, start=1):
            stage = find_first(node, lambda child: "timeline-stage" in child.classes)
            card = find_first(node, lambda child: "timeline-card" in child.classes)
            if not stage or not card:
                errors.append(
                    f"{report_path}: timeline node {index} must contain both .timeline-stage and .timeline-card"
                )
                continue
            if not find_first(stage, lambda child: "timeline-dot" in child.classes):
                errors.append(f"{report_path}: timeline node {index} is missing .timeline-dot")
            if not find_first(stage, lambda child: "timeline-stage-title" in child.classes):
                errors.append(f"{report_path}: timeline node {index} is missing .timeline-stage-title")
            if not find_first(card, lambda child: "timeline-summary" in child.classes):
                errors.append(f"{report_path}: timeline node {index} is missing .timeline-summary")
            blocks = find_all(card, lambda child: "timeline-block" in child.classes)
            if not blocks:
                errors.append(f"{report_path}: timeline node {index} must contain at least one .timeline-block")
            for block_index, block in enumerate(blocks, start=1):
                text = normalize_text(text_content(block))
                if not any(label in text for label in FLOW_PROBLEM_LABELS):
                    errors.append(
                        f"{report_path}: timeline node {index} block {block_index} must contain a problem label"
                    )
                if not any(label in text for label in FLOW_SOLUTION_LABELS):
                    errors.append(
                        f"{report_path}: timeline node {index} block {block_index} must contain a solution label"
                    )

    if resolution_tracks:
        summary_grid = find_first(resolution_tracks, lambda node: "three-col" in node.classes)
        if not summary_grid:
            errors.append(f"{report_path}: #resolution-tracks must contain .three-col")
        else:
            panel_count = len(direct_children_with_class(summary_grid, "panel"))
            if panel_count != 3:
                errors.append(f"{report_path}: #resolution-tracks .three-col must contain exactly 3 .panel children")

    if open_questions and next_actions:
        open_actions_grid = nearest_ancestor_with_class(open_questions, "actions-grid")
        next_actions_grid = nearest_ancestor_with_class(next_actions, "actions-grid")
        if not open_actions_grid or not next_actions_grid or open_actions_grid is not next_actions_grid:
            errors.append(
                f"{report_path}: #open-questions and #next-actions must be sibling panels inside the same .actions-grid"
            )


def validate_report_html(report_path: Path, state: Dict, errors: List[str], warnings: List[str]) -> None:
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

    dom_root = parse_html(html)
    validate_required_sections(dom_root, report_path, errors)
    validate_template_classes(html, report_path, errors)
    validate_report_structure(report_path, state, html, dom_root, errors)

    issues = state.get("issues", [])
    present_stable_ids = [issue.get("stable_id") for issue in issues if issue.get("stable_id") and issue.get("stable_id") in html]
    if present_stable_ids:
        errors.append(
            f"{report_path}: human report must not expose stable_id values: {', '.join(sorted(present_stable_ids))}"
        )
    for issue in issues:
        display_number = issue.get("display_number")
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

    validate_report_html(report_path, state, errors, warnings)

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

    if not meta.get("project_name"):
        errors.append(f"{state_path}: meta.project_name is required")
    if not meta.get("report_language"):
        errors.append(f"{state_path}: meta.report_language is required")
    if not meta.get("language_source"):
        errors.append(f"{state_path}: meta.language_source is required")
    if not meta.get("template_version"):
        errors.append(f"{state_path}: meta.template_version is required")
    if not meta.get("renderer_version"):
        errors.append(f"{state_path}: meta.renderer_version is required")

    intake = state.get("intake", {})
    precise_intake_node = intake_node_from_url(intake.get("figma_intake_url"))
    requested_node = normalize_node_id(meta.get("requested_input_node"))
    reviewed_node = normalize_node_id(meta.get("reviewed_node"))
    intake_node = normalize_node_id(intake.get("figma_intake_node"))

    if precise_intake_node:
        if requested_node != precise_intake_node:
            errors.append(
                f"{state_path}: meta.requested_input_node must match figma_intake_url node-id '{precise_intake_node}'"
            )
        if intake_node and intake_node != precise_intake_node:
            errors.append(
                f"{state_path}: intake.figma_intake_node must match figma_intake_url node-id '{precise_intake_node}'"
            )

    if requested_node and reviewed_node and requested_node != reviewed_node:
        if not str(meta.get("reviewed_node_reason") or "").strip():
            errors.append(
                f"{state_path}: meta.reviewed_node_reason is required when reviewed_node differs from requested_input_node"
            )

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
