# Review State Schema

当你要写入或更新下面这个文件时，使用这份参考：

```text
design-buff-reviews/<review-slug>/review-state.json
```

这份文件只约束机器 sidecar。人类报告结构和对话规则看 `report-contract.md`。

## 用途

`review-state.json` 用来保存结构化的持久状态，让系统可以：

- 不必重新解析整份 HTML，也能恢复上次评审状态
- 比较不同轮次的结果
- 持续追踪问题身份
- 渲染 `Changes Since Last Review`

它不是第二份人类报告。

## v1 顶层结构

```json
{
  "schema_version": "v1",
  "meta": {},
  "intake": {},
  "coverage": {},
  "background": {},
  "evidence": [],
  "issues": [],
  "priorities": {},
  "history": {}
}
```

## v1 字段说明

### `schema_version`

- required: yes
- type: `string`
- v1 固定值: `"v1"`

### `meta`

运行身份和兼容性元数据。

- `project_name`: `string`, optional
- `review_slug`: `string`, required
- `report_mode`: `string`, required, allowed `self-check | agent-review`
- `review_date`: `string`, required, format `YYYY-MM-DD`
- `reviewer`: `string`, required
- `report_language`: `string`, required
- `language_source`: `string`, required, allowed `explicit_override | intake_inference | default_zh_cn`
- `run_id`: `string`, required
- `input_hash`: `string | null`, optional
- `template_version`: `string`, required
- `renderer_version`: `string`, required
- `created_at`: `string`, required, ISO 8601 timestamp
- `updated_at`: `string`, required, ISO 8601 timestamp

### `intake`

规范化后的 intake 状态和本轮选择的审核范围。

- `source_artifacts`: `array<string>`, required
- `figma_intake_url`: `string | null`, optional
- `figma_file_key`: `string | null`, optional
- `figma_intake_node`: `string | null`, optional
- `figma_intake_node_type`: `string | null`, optional
- `ingest_status`: `string`, required
- `selected_unit_ids`: `array<string>`, required
- `high_precision_unit_ids`: `array<string>`, required
- `structural_only_unit_ids`: `array<string>`, required
- `deferred_unit_ids`: `array<string>`, required
- `tool_limits`: `array<string>`, required

### `coverage`

读取覆盖和验证覆盖。

- `fully_read_unit_ids`: `array<string>`, required
- `partially_read_unit_ids`: `array<string>`, required
- `screenshot_validated_unit_ids`: `array<string>`, required
- `open_tooling_gaps`: `array<string>`, required

### `background`

这里只存结构化背景状态，不写面向人的长 prose。

- `page_type`: `string | null`, optional
- `product_type`: `string | null`, optional
- `industry`: `string | null`, optional
- `target_user`: `string | null`, optional
- `core_scenario`: `string | null`, optional
- `business_goal`: `string | null`, optional
- `workflow_position`: `string | null`, optional
- `summary`: `string | null`, optional，只允许短结构摘要
- `assumptions`: `array<string>`, required
- `unknowns`: `array<string>`, required
- `confidence`: `string | null`, optional

### `evidence`

证据台账。每一项都必须对机器可用。

每项包含：

- `evidence_id`: `string`, required
- `source_type`: `string`, required
- `node_ref`: `string | null`, optional
- `artifact_ref`: `string | null`, optional
- `read_method`: `string`, required
- `confidence`: `string`, required
- `raw_ref`: `string | null`, optional
- `tags`: `array<string>`, required

### `issues`

结构化问题状态。稳定问题身份的行为规则定义在 `review-playbook.md`；这里只定义机器字段。

每项包含：

- `stable_id`: `string`, required
- `display_number`: `string`, required，例如 `ISSUE-001`
- `title`: `string`, required
- `category`: `string`, required
- `severity`: `string`, required
- `confidence`: `string`, required
- `status`: `string`, required，推荐 `active | resolved | changed | deferred`
- `evidence_ids`: `array<string>`, required
- `problem_summary`: `string | null`, optional，只允许短机器摘要
- `impact_summary`: `string | null`, optional，只允许短机器摘要
- `recommendation_summary`: `string | null`, optional，只允许短机器摘要
- `discussion_prompts`: `array<string>`, required

### `priorities`

结构化优先级状态。

- `highest_priority_issue_id`: `string | null`, optional
- `top_issue_ids`: `array<string>`, required
- `open_questions`: `array<object>`, required
- `next_actions`: `array<object>`, required

每个 `open_questions` 项包含：

- `question_id`: `string`
- `title`: `string`
- `status`: `string`
- `related_issue_ids`: `array<string>`

每个 `next_actions` 项包含：

- `action_id`: `string`
- `title`: `string`
- `status`: `string`
- `related_issue_ids`: `array<string>`

### `history`

结构化的评审 diff 状态。

- `previous_run_id`: `string | null`, optional
- `previous_review_date`: `string | null`, optional
- `new_issue_ids`: `array<string>`, required
- `resolved_issue_ids`: `array<string>`, required
- `changed_issue_ids`: `array<string>`, required
- `severity_changed_issue_ids`: `array<string>`, required
- `recommendation_changed_issue_ids`: `array<string>`, required

## 禁止写入的内容

不要存这些东西：

- executive summary 正文
- 完整问题 prose
- `why_it_is_a_problem` 这种长段解释
- 面向人的完整 recommendation 段落
- 任何可能被误认成正式评审报告的长文本

经验法则：

- 如果一个字段是为了让系统恢复、比较或追踪，它应该放这里
- 如果一个字段主要是为了说服或解释给人听，它应该进 `report.html`

## 最小示例

```json
{
  "schema_version": "v1",
  "meta": {
    "project_name": "示例评审",
    "review_slug": "example-review",
    "report_mode": "self-check",
    "review_date": "2026-03-27",
    "reviewer": "Codex design-buff",
    "report_language": "zh-CN",
    "language_source": "intake_inference",
    "run_id": "run_001",
    "input_hash": "abc123",
    "template_version": "human-report-html-v1",
    "renderer_version": "design-buff-v0.7",
    "created_at": "2026-03-27T10:00:00Z",
    "updated_at": "2026-03-27T10:15:00Z"
  },
  "intake": {
    "source_artifacts": ["figma:get_metadata", "figma:get_design_context"],
    "figma_intake_url": "https://www.figma.com/design/FILE123/Test?node-id=1-2",
    "figma_file_key": "FILE123",
    "figma_intake_node": "1:2",
    "figma_intake_node_type": "frame",
    "ingest_status": "success",
    "selected_unit_ids": ["1:2", "1:3"],
    "high_precision_unit_ids": ["1:2"],
    "structural_only_unit_ids": ["1:3"],
    "deferred_unit_ids": [],
    "tool_limits": []
  },
  "coverage": {
    "fully_read_unit_ids": ["1:2"],
    "partially_read_unit_ids": ["1:3"],
    "screenshot_validated_unit_ids": ["1:2"],
    "open_tooling_gaps": []
  },
  "background": {
    "page_type": "移动端弹层流程",
    "product_type": "会员绑定流程",
    "industry": "旅行",
    "target_user": "高意图的权益用户",
    "core_scenario": "选对路径并完成账号互通",
    "business_goal": "提升成功绑定率",
    "workflow_position": "转化后段",
    "summary": "会员开通与绑定流程",
    "assumptions": ["用户可能并不知道自己的账号状态"],
    "unknowns": ["真实回调行为"],
    "confidence": "medium-high"
  },
  "evidence": [
    {
      "evidence_id": "ev_001",
      "source_type": "figma",
      "node_ref": "1:2",
      "artifact_ref": "intake-board",
      "read_method": "get_design_context",
      "confidence": "high",
      "raw_ref": ".design-buff/example-review/tool-cache/context-1-2.json",
      "tags": ["copy", "cta", "hierarchy"]
    }
  ],
  "issues": [
    {
      "stable_id": "routing-self-diagnosis__90f948",
      "display_number": "ISSUE-001",
      "title": "用户还不知道自己是否有万豪账号，却必须先选开通还是绑定",
      "category": "scenario and fit",
      "severity": "high",
      "confidence": "high",
      "status": "active",
      "evidence_ids": ["ev_001"],
      "problem_summary": "入口分流要求用户先推断后台状态",
      "impact_summary": "容易走错路，失败后还会伤害信任",
      "recommendation_summary": "优先系统自动判路，或至少提供明确的不确定路径",
      "discussion_prompts": ["授权后系统能否先检查账号状态？"]
    }
  ],
  "priorities": {
    "highest_priority_issue_id": "routing-self-diagnosis__90f948",
    "top_issue_ids": ["routing-self-diagnosis__90f948"],
    "open_questions": [
      {
        "question_id": "q_001",
        "title": "授权后系统能否先检查账号状态？",
        "status": "open",
        "related_issue_ids": ["routing-self-diagnosis__90f948"]
      }
    ],
    "next_actions": [
      {
        "action_id": "a_001",
        "title": "重写首步判路，不再让用户自己猜账号状态",
        "status": "pending",
        "related_issue_ids": ["routing-self-diagnosis__90f948"]
      }
    ]
  },
  "history": {
    "previous_run_id": null,
    "previous_review_date": null,
    "new_issue_ids": ["routing-self-diagnosis__90f948"],
    "resolved_issue_ids": [],
    "changed_issue_ids": [],
    "severity_changed_issue_ids": [],
    "recommendation_changed_issue_ids": []
  }
}
```
