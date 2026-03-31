#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE_PATH = REPO_ROOT / "templates" / "report-shell.html"
PLACEHOLDER_RE = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")

LABELS = {
    "zh": {
        "report_mode_self": "自查模式 · 设计评审报告",
        "report_mode_agent": "机器交接模式 · 设计评审报告",
        "review_slug_chip_label": "评审标识",
        "review_date_chip_label": "日期",
        "report_language_chip_label": "语言",
        "ingest_status_chip_label": "读取状态",
        "reviewer_label": "评审器",
        "figma_file_label": "Figma 文件",
        "figma_node_label": "评审节点",
        "verdict_label": "当前评估",
        "changes_title": "本次更新",
        "new_issues_label": "新增问题",
        "resolved_issues_label": "已解决问题",
        "changed_issues_label": "本次变化",
        "highest_priority_section_title": "最高优先级问题",
        "issue_label": "核心问题",
        "diagnosis_label": "诊断",
        "why_first_label": "为何优先",
        "recommended_direction_label": "修改建议",
        "need_to_confirm_label": "需确认",
        "background_title": "评审依据与边界",
        "full_review_title": "完整评审",
        "three_flow_title": "三流一致性",
        "three_flow_synthesis_label": "整体判断",
        "resolution_tracks_title": "结构摘要",
        "issue_distribution_label": "问题分布",
        "resolution_paths_label": "分三批推进",
        "key_risk_label": "关键风险",
        "actions_title": "待确认与下一步",
        "open_questions_title": "待确认",
        "next_actions_title": "下一步",
        "background_basis_title": "评审依据",
        "background_boundaries_title": "评审边界",
        "unknown": "unknown",
        "none": "暂无。",
        "no_prior_review": "这是首轮评审，本节只记录本次基线，不比较上一轮变化。",
        "no_changes": "当前问题集与上一版保持一致。",
        "problem_label": "问题：",
        "solution_label": "解法：",
    },
    "en": {
        "report_mode_self": "Self-check · Design Review Report",
        "report_mode_agent": "Agent Handoff · Design Review Report",
        "review_slug_chip_label": "Review Slug",
        "review_date_chip_label": "Review Date",
        "report_language_chip_label": "Language",
        "ingest_status_chip_label": "Ingest Status",
        "reviewer_label": "Reviewer",
        "figma_file_label": "Figma File",
        "figma_node_label": "Review Node",
        "verdict_label": "Current Verdict",
        "changes_title": "Changes Since Last Review",
        "new_issues_label": "New Issues",
        "resolved_issues_label": "Resolved Issues",
        "changed_issues_label": "Current Change",
        "highest_priority_section_title": "Highest-Priority Issue",
        "issue_label": "Core Issue",
        "diagnosis_label": "Diagnosis",
        "why_first_label": "Why This Comes First",
        "recommended_direction_label": "Recommended Direction",
        "need_to_confirm_label": "Need To Confirm",
        "background_title": "Background and Evidence",
        "full_review_title": "Full Review",
        "three_flow_title": "Three-Flow Consistency",
        "three_flow_synthesis_label": "Overall Reading",
        "resolution_tracks_title": "Structural Summary",
        "issue_distribution_label": "Issue Distribution",
        "resolution_paths_label": "Resolution Sequence",
        "key_risk_label": "Key Risk",
        "actions_title": "Open Questions and Next Actions",
        "open_questions_title": "Open Questions",
        "next_actions_title": "Next Actions",
        "background_basis_title": "Review Basis",
        "background_boundaries_title": "Review Boundaries",
        "unknown": "unknown",
        "none": "None for now.",
        "no_prior_review": "This is the baseline review for this slug, so no previous version is being compared yet.",
        "no_changes": "The current issue set is unchanged from the last pass.",
        "problem_label": "Problem:",
        "solution_label": "Solution:",
    },
}

SEVERITY_LABELS = {
    "zh": {
        "high": "高优先级",
        "medium": "中优先级",
        "low": "低优先级",
        "critical": "关键优先级",
    },
    "en": {
        "high": "High Priority",
        "medium": "Medium Priority",
        "low": "Low Priority",
        "critical": "Critical Priority",
    },
}

CONFIDENCE_LABELS = {
    "zh": {
        "high": "高置信",
        "medium": "中置信",
        "low": "低置信",
        "medium-high": "中高置信",
    },
    "en": {
        "high": "High Confidence",
        "medium": "Medium Confidence",
        "low": "Low Confidence",
        "medium-high": "Medium-High Confidence",
    },
}

INGEST_STATUS_LABELS = {
    "zh": {
        "success": "成功",
        "partial": "部分成功",
        "failed": "失败",
        "unknown": "unknown",
    },
    "en": {
        "success": "Success",
        "partial": "Partial",
        "failed": "Failed",
        "unknown": "unknown",
    },
}


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def pick_language(report_language: str) -> str:
    return "zh" if report_language.lower().startswith("zh") else "en"


def labels_for(report_language: str) -> Dict[str, str]:
    return LABELS[pick_language(report_language)]


def escape_text(value: Any) -> str:
    return html.escape(str(value), quote=True)


def compact_text(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def localize_value(kind: str, value: Any, report_language: str) -> str:
    normalized = str(value or "").strip().lower() or "unknown"
    locale = pick_language(report_language)
    table = {
        "severity": SEVERITY_LABELS,
        "confidence": CONFIDENCE_LABELS,
        "ingest_status": INGEST_STATUS_LABELS,
    }.get(kind)
    if not table:
        return compact_text(value, LABELS[locale]["unknown"])
    return table.get(locale, {}).get(normalized, compact_text(value, LABELS[locale]["unknown"]))


def panel_body_html(body: Any, fallback: str) -> str:
    paragraphs: List[str] = []
    if isinstance(body, dict):
        if isinstance(body.get("paragraphs"), list):
            paragraphs = [str(item).strip() for item in body["paragraphs"] if str(item).strip()]
        elif body.get("body") is not None:
            paragraphs = [segment.strip() for segment in str(body["body"]).split("\n\n") if segment.strip()]
    elif isinstance(body, list):
        paragraphs = [str(item).strip() for item in body if str(item).strip()]
    elif body is not None:
        paragraphs = [segment.strip() for segment in str(body).split("\n\n") if segment.strip()]

    if not paragraphs:
        paragraphs = [fallback]
    return "".join(f"<p>{escape_text(paragraph)}</p>" for paragraph in paragraphs)


def render_panel(panel: Any, title: str, fallback: str) -> str:
    if isinstance(panel, dict):
        heading = compact_text(panel.get("title"), title)
        body_source = panel
    else:
        heading = title
        body_source = panel
    return f"<h3>{escape_text(heading)}</h3>{panel_body_html(body_source, fallback)}"


def render_list_items(items: Sequence[str], fallback: str) -> str:
    values = [compact_text(item, "").strip() for item in items if compact_text(item, "").strip()]
    if not values:
        values = [fallback]
    return "".join(f"<li>{escape_text(item)}</li>" for item in values)


def normalize_issue_slots(raw: Any) -> Dict[str, Dict[str, Any]]:
    if isinstance(raw, dict):
        if all(isinstance(value, dict) for value in raw.values()):
            return {str(key): value for key, value in raw.items()}
        if "stable_id" in raw:
            return {str(raw["stable_id"]): raw}
    if isinstance(raw, list):
        normalized = {}
        for item in raw:
            if isinstance(item, dict) and item.get("stable_id"):
                normalized[str(item["stable_id"])] = item
        return normalized
    return {}


def first_non_empty(values: Iterable[Any], fallback: str) -> str:
    for value in values:
        text = compact_text(value, "").strip()
        if text:
            return text
    return fallback


def issue_lookup(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(issue.get("stable_id")): issue for issue in state.get("issues", []) if issue.get("stable_id")}


def summarize_history_ids(ids: Sequence[str], fallback: str) -> str:
    values = [str(item).strip() for item in ids if str(item).strip()]
    return "、".join(values) if values else fallback


def slot_list(values: Any) -> List[str]:
    if isinstance(values, list):
        return [str(item).strip() for item in values if str(item).strip()]
    return []


def normalize_priority_titles(entries: Any) -> List[str]:
    if not isinstance(entries, list):
        return []
    titles: List[str] = []
    for entry in entries:
        if isinstance(entry, dict):
            value = entry.get("title") or entry.get("question") or entry.get("action")
            if value:
                titles.append(str(value).strip())
        elif entry:
            titles.append(str(entry).strip())
    return [item for item in titles if item]


def build_top_priority_chips(state: Dict[str, Any], slots: Dict[str, Any], labels: Dict[str, str]) -> List[str]:
    slot_values = slot_list(slots.get("overview", {}).get("top_priority_chips"))
    if slot_values:
        values = slot_values
    else:
        lookup = issue_lookup(state)
        values = []
        for stable_id in state.get("priorities", {}).get("top_issue_ids", []):
            issue = lookup.get(str(stable_id))
            if issue and issue.get("title"):
                values.append(str(issue["title"]).strip())
        if not values and state.get("issues"):
            values = [str(issue.get("title", "")).strip() for issue in state["issues"][:3] if issue.get("title")]
    while len(values) < 3:
        values.append(labels["none"])
    return values[:3]


def render_issue_cards(state: Dict[str, Any], slots: Dict[str, Any], labels: Dict[str, str], report_language: str) -> str:
    slot_map = normalize_issue_slots(slots.get("issues"))
    cards: List[str] = []
    for issue in state.get("issues", []):
        stable_id = str(issue.get("stable_id", ""))
        slot = slot_map.get(stable_id, {})
        display_number = compact_text(issue.get("display_number"), labels["unknown"])
        title = compact_text(issue.get("title"), labels["unknown"])
        category = compact_text(issue.get("category"), labels["unknown"])
        severity = localize_value("severity", issue.get("severity"), report_language)
        confidence = localize_value("confidence", issue.get("confidence"), report_language)
        diagnosis = first_non_empty(
            [slot.get("diagnosis_paragraph"), slot.get("problem_paragraph"), issue.get("problem_summary")],
            labels["none"],
        )
        direction = first_non_empty(
            [slot.get("recommended_direction_paragraph"), slot.get("solution_paragraph"), issue.get("recommendation_summary")],
            labels["none"],
        )
        need_to_confirm = first_non_empty(
            [slot.get("need_to_confirm"), issue.get("discussion_prompts", [None])[0] if issue.get("discussion_prompts") else None],
            labels["none"],
        )
        cards.append(
            "\n".join(
                [
                    '<article class="issue-card">',
                    "  <header>",
                    f"    <h3>{escape_text(display_number)} · {escape_text(title)}</h3>",
                    f"    <div class=\"issue-meta\">{escape_text(category)} · {escape_text(severity)} · {escape_text(confidence)}</div>",
                    "  </header>",
                    '  <div class="split-list">',
                    '    <div class="panel">',
                    f"      <h3>{escape_text(labels['diagnosis_label'])}</h3>",
                    f"      <p>{escape_text(diagnosis)}</p>",
                    "    </div>",
                    '    <div class="panel">',
                    f"      <h3>{escape_text(labels['recommended_direction_label'])}</h3>",
                    f"      <p>{escape_text(direction)}</p>",
                    "    </div>",
                    '    <div class="panel">',
                    f"      <h3>{escape_text(labels['need_to_confirm_label'])}</h3>",
                    f"      <p>{escape_text(need_to_confirm)}</p>",
                    "    </div>",
                    "  </div>",
                    "</article>",
                ]
            )
        )
    return "\n".join(cards)


def render_timeline_nodes(slots: Dict[str, Any], labels: Dict[str, str]) -> str:
    three_flow = slots.get("three_flow", {})
    nodes = three_flow.get("nodes", [])
    rendered_nodes: List[str] = []
    for index, node in enumerate(nodes, start=1):
        stage_number = compact_text(node.get("stage_number"), f"{index:02d}")
        stage_title = compact_text(node.get("stage_title"), labels["unknown"])
        stage_summary = compact_text(node.get("stage_summary"), "")
        timeline_summary = compact_text(node.get("timeline_summary"), labels["none"])
        blocks = node.get("blocks") or []
        rendered_blocks: List[str] = []
        for block in blocks:
            heading = compact_text(block.get("heading"), labels["none"])
            problem = compact_text(block.get("problem"), labels["none"])
            solution = compact_text(block.get("solution"), labels["none"])
            rendered_blocks.append(
                "\n".join(
                    [
                        '    <div class="timeline-block">',
                        f"      <h3>{escape_text(heading)}</h3>",
                        f"      <p><span class=\"inline-label\">{escape_text(labels['problem_label'])}</span> {escape_text(problem)}</p>",
                        f"      <p><span class=\"inline-label\">{escape_text(labels['solution_label'])}</span> {escape_text(solution)}</p>",
                        "    </div>",
                    ]
                )
            )
        if not rendered_blocks:
            rendered_blocks.append(
                "\n".join(
                    [
                        '    <div class="timeline-block">',
                        f"      <h3>{escape_text(labels['none'])}</h3>",
                        f"      <p><span class=\"inline-label\">{escape_text(labels['problem_label'])}</span> {escape_text(labels['none'])}</p>",
                        f"      <p><span class=\"inline-label\">{escape_text(labels['solution_label'])}</span> {escape_text(labels['none'])}</p>",
                        "    </div>",
                    ]
                )
            )
        summary_html = (
            f"              <div class=\"timeline-stage-summary\">{escape_text(stage_summary)}</div>"
            if stage_summary
            else ""
        )
        rendered_nodes.append(
            "\n".join(
                [
                    '<article class="timeline-node">',
                    '  <div class="timeline-stage">',
                    f"    <div class=\"timeline-dot\">{escape_text(stage_number)}</div>",
                    '    <div class="timeline-stage-text">',
                    f"      <div class=\"timeline-stage-title\">{escape_text(stage_title)}</div>",
                    summary_html,
                    "    </div>",
                    "  </div>",
                    '  <div class="timeline-card">',
                    f"    <p class=\"timeline-summary\">{escape_text(timeline_summary)}</p>",
                    *rendered_blocks,
                    "  </div>",
                    "</article>",
                ]
            )
        )
    return "\n".join(rendered_nodes)


def build_footer_note(state: Dict[str, Any]) -> str:
    meta = state.get("meta", {})
    intake = state.get("intake", {})
    slug = compact_text(meta.get("review_slug"), "unknown")
    note = f"产物路径：design-buff-reviews/{slug}/report.html · run_id: {compact_text(meta.get('run_id'), 'unknown')}"
    requested = compact_text(meta.get("requested_input_node"), "").strip()
    reviewed = compact_text(meta.get("reviewed_node"), "").strip()
    if requested and reviewed and requested != reviewed:
        note += f" · 输入节点: {requested} · 实际评审节点: {reviewed}"
    elif intake.get("figma_intake_node"):
        note += f" · 评审节点: {compact_text(intake.get('figma_intake_node'), 'unknown')}"
    return note


def build_context(state: Dict[str, Any], slots: Dict[str, Any]) -> Dict[str, str]:
    meta = state.get("meta", {})
    intake = state.get("intake", {})
    history = state.get("history", {})
    priorities = state.get("priorities", {})
    report_language = compact_text(meta.get("report_language"), "zh-CN")
    labels = labels_for(report_language)
    issues_by_id = issue_lookup(state)
    highest_priority_id = compact_text(priorities.get("highest_priority_issue_id"), "")
    highest_issue = issues_by_id.get(highest_priority_id) if highest_priority_id else None
    if not highest_issue and state.get("issues"):
        highest_issue = state["issues"][0]
    highest_slot_map = slots.get("highest_priority_issue", {})
    if isinstance(highest_slot_map, dict) and highest_issue and highest_issue.get("stable_id") in highest_slot_map:
        highest_slot = highest_slot_map[str(highest_issue["stable_id"])]
    elif isinstance(highest_slot_map, dict):
        highest_slot = highest_slot_map
    else:
        highest_slot = {}

    overview_slots = slots.get("overview", {})
    background_slots = slots.get("background_and_evidence", {})
    resolution_slots = slots.get("resolution_tracks", {})

    context = {
        "report_mode_label": labels["report_mode_self"]
        if compact_text(meta.get("report_mode"), "self-check") == "self-check"
        else labels["report_mode_agent"],
        "project_name": compact_text(meta.get("project_name"), labels["unknown"]),
        "overall_diagnosis": compact_text(overview_slots.get("overall_diagnosis"), labels["none"]),
        "review_slug_chip_label": labels["review_slug_chip_label"],
        "review_date_chip_label": labels["review_date_chip_label"],
        "report_language_chip_label": labels["report_language_chip_label"],
        "ingest_status_chip_label": labels["ingest_status_chip_label"],
        "review_slug": compact_text(meta.get("review_slug"), labels["unknown"]),
        "review_date": compact_text(meta.get("review_date"), labels["unknown"]),
        "report_language": report_language,
        "ingest_status": localize_value("ingest_status", intake.get("ingest_status"), report_language),
        "reviewer_label": labels["reviewer_label"],
        "figma_file_label": labels["figma_file_label"],
        "figma_node_label": labels["figma_node_label"],
        "reviewer": compact_text(meta.get("reviewer"), labels["unknown"]),
        "figma_file_key": compact_text(intake.get("figma_file_key"), labels["unknown"]),
        "figma_intake_node": compact_text(meta.get("reviewed_node") or intake.get("figma_intake_node"), labels["unknown"]),
        "verdict_label": labels["verdict_label"],
        "current_verdict": compact_text(overview_slots.get("current_verdict"), labels["none"]),
        "top_priority_1": build_top_priority_chips(state, slots, labels)[0],
        "top_priority_2": build_top_priority_chips(state, slots, labels)[1],
        "top_priority_3": build_top_priority_chips(state, slots, labels)[2],
        "changes_title": labels["changes_title"],
        "new_issues_label": labels["new_issues_label"],
        "resolved_issues_label": labels["resolved_issues_label"],
        "changed_issues_label": labels["changed_issues_label"],
        "new_issues": compact_text(
            slots.get("changes", {}).get("new_issues"),
            summarize_history_ids(history.get("new_issue_ids", []), labels["no_prior_review"]),
        ),
        "resolved_issues": compact_text(
            slots.get("changes", {}).get("resolved_issues"),
            summarize_history_ids(history.get("resolved_issue_ids", []), labels["no_changes"]),
        ),
        "changed_issues": compact_text(
            slots.get("changes", {}).get("changed_issues"),
            summarize_history_ids(history.get("changed_issue_ids", []), labels["no_changes"]),
        ),
        "highest_priority_section_title": labels["highest_priority_section_title"],
        "issue_label": labels["issue_label"],
        "highest_priority_display_number": compact_text(
            highest_issue.get("display_number") if highest_issue else None,
            labels["unknown"],
        ),
        "highest_priority_issue_title": compact_text(highest_issue.get("title") if highest_issue else None, labels["unknown"]),
        "highest_priority_category": compact_text(highest_issue.get("category") if highest_issue else None, labels["unknown"]),
        "highest_priority_severity": localize_value(
            "severity",
            highest_issue.get("severity") if highest_issue else None,
            report_language,
        ),
        "highest_priority_confidence": localize_value(
            "confidence",
            highest_issue.get("confidence") if highest_issue else None,
            report_language,
        ),
        "diagnosis_label": labels["diagnosis_label"],
        "why_first_label": labels["why_first_label"],
        "recommended_direction_label": labels["recommended_direction_label"],
        "need_to_confirm_label": labels["need_to_confirm_label"],
        "highest_priority_diagnosis_paragraph": first_non_empty(
            [highest_slot.get("diagnosis_paragraph"), highest_issue.get("problem_summary") if highest_issue else None],
            labels["none"],
        ),
        "highest_priority_why_first_paragraph": compact_text(highest_slot.get("why_first_paragraph"), labels["none"]),
        "highest_priority_recommended_direction_paragraph": first_non_empty(
            [highest_slot.get("recommended_direction_paragraph"), highest_issue.get("recommendation_summary") if highest_issue else None],
            labels["none"],
        ),
        "highest_priority_need_to_confirm": first_non_empty(
            [
                highest_slot.get("need_to_confirm"),
                highest_issue.get("discussion_prompts", [None])[0] if highest_issue and highest_issue.get("discussion_prompts") else None,
            ],
            labels["none"],
        ),
        "background_title": labels["background_title"],
        "background_and_evidence_html": render_panel(
            background_slots.get("review_basis"),
            labels["background_basis_title"],
            labels["none"],
        ),
        "review_boundaries_html": render_panel(
            background_slots.get("review_boundaries"),
            labels["background_boundaries_title"],
            labels["none"],
        ),
        "full_review_title": labels["full_review_title"],
        "issue_cards_html": render_issue_cards(state, slots, labels, report_language),
        "three_flow_title": labels["three_flow_title"],
        "timeline_nodes_html": render_timeline_nodes(slots, labels),
        "three_flow_synthesis_label": labels["three_flow_synthesis_label"],
        "three_flow_synthesis_paragraph": compact_text(
            slots.get("three_flow", {}).get("synthesis_paragraph"),
            labels["none"],
        ),
        "resolution_tracks_title": labels["resolution_tracks_title"],
        "issue_distribution_label": labels["issue_distribution_label"],
        "issue_distribution_paragraph": compact_text(
            resolution_slots.get("issue_distribution_paragraph"),
            labels["none"],
        ),
        "resolution_paths_label": labels["resolution_paths_label"],
        "resolution_paths_paragraph": compact_text(
            resolution_slots.get("resolution_paths_paragraph"),
            labels["none"],
        ),
        "key_risk_label": labels["key_risk_label"],
        "key_risk_paragraph": compact_text(
            resolution_slots.get("key_risk_paragraph"),
            labels["none"],
        ),
        "actions_title": labels["actions_title"],
        "open_questions_title": labels["open_questions_title"],
        "next_actions_title": labels["next_actions_title"],
        "open_questions_items_html": render_list_items(
            slot_list(slots.get("open_questions")) or normalize_priority_titles(priorities.get("open_questions")),
            labels["none"],
        ),
        "next_actions_items_html": render_list_items(
            slot_list(slots.get("next_actions")) or normalize_priority_titles(priorities.get("next_actions")),
            labels["none"],
        ),
        "footer_note": compact_text(slots.get("footer_note"), build_footer_note(state)),
    }
    return context


def render_template(template: str, context: Dict[str, str]) -> str:
    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in context:
            raise KeyError(f"missing render context for placeholder '{key}'")
        return context[key]

    rendered = PLACEHOLDER_RE.sub(replacer, template)
    leftovers = sorted(set(PLACEHOLDER_RE.findall(rendered)))
    if leftovers:
        raise KeyError(f"unresolved placeholders remain: {', '.join(leftovers)}")
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a design-buff HTML report from review-state and constrained report slots.")
    parser.add_argument("state", help="Path to design-buff review-state.json")
    parser.add_argument(
        "--slots",
        required=True,
        help="Path to constrained report-slots.json stored in hidden scratch or another technical location",
    )
    parser.add_argument("--output", help="Output report.html path; defaults to the sibling of review-state.json")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE_PATH), help="Template path to use")
    args = parser.parse_args()

    state_path = Path(args.state).resolve()
    slots_path = Path(args.slots).resolve()
    output_path = Path(args.output).resolve() if args.output else state_path.with_name("report.html")
    template_path = Path(args.template).resolve()

    state = load_json(state_path)
    slots = load_json(slots_path)
    template = template_path.read_text(encoding="utf-8")

    context = build_context(state, slots)
    rendered = render_template(template, context)
    write_text(output_path, rendered)
    print(f"Rendered {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
