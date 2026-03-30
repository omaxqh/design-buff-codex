# 报告合同

当你要渲染对话输出、`report.html` 和 hidden scratch 时，使用这份参考。

## Canonical Output Model

所有输出必须来自同一个 canonical review object。

正式输出写到：

```text
design-buff-reviews/<review-slug>/
```

每个 review 根目录至少包含：

- `report.html`：唯一正式的人类评审报告
- `review-state.json`：结构化的持久 sidecar

技术性 scratch 可以写到：

```text
.design-buff/<review-slug>/
```

规则：

- `report.html` 是唯一面向人的正式真相源
- `review-state.json` 不是第二份报告
- 对话可以概括、重排，但不能和报告矛盾
- 同一份草稿或功能再次复审时，要在同一个 `review-slug` 下原地更新

## 对话启动总结

聊天窗口只是启动面，不是长报告正文。

推荐顺序：

1. 一句总诊断
2. 当前最关键的阻塞项或优先级
3. `report.html` 的路径
4. 只有在确实紧急时，才补最重要的待确认问题

保持精炼。不要把整份报告贴回对话里。

## 报告语言规则

按这个顺序决定报告语言：

1. 用户明确指定
2. 当前对话、PRD 和补充材料里的主导语言
3. 回退到 `zh-CN`

要求：

- 把选中的语言写进 `meta.report_language`
- 把语言决策来源写进 `meta.language_source`
- 在 `report.html` 里设置 `<html lang="...">`
- 除非用户明确要求双语，否则标签、标题和叙述都使用选中的报告语言
- 产品名、node ID 和一旦翻译就会丢精度的原文，保持原样

语言信号混杂或互相打架时，用 `scripts/detect_report_language.py`。

## 必备 HTML 标记

`report.html` 必须包含：

- `<html lang="...">`
- `<meta name="design-buff-template" content="human-report-html-v1">`
- `<body data-design-buff-report="v1">`

这些标记让校验器能确认人类报告是否符合包内合同。

## 必备章节

最终页面必须自包含，并且包含这些语义章节：

- `#review-overview`
- `#executive-summary`
- 如果不是首轮评审，再加 `#changes-since-last-review`
- `#highest-priority-issue`
- `#background-and-evidence`
- `#full-review`
- `#issue-list`
- `#three-flow-consistency`
- `#resolution-tracks`
- `#open-questions`
- `#next-actions`

只有在章节确实没有必要时才删除。
如果内容暂时未知，就标成 `unknown`，不要假装确定。

## 章节内容映射

### Review Overview

渲染：

- `project_name`
- `review_slug`
- `report_mode`
- `review_date`
- `reviewer`
- `report_language`
- `source_artifacts`
- `figma_intake_url`
- `figma_file_key`
- `figma_intake_node`
- `figma_intake_node_type`
- `ingest_status`

### Executive Summary

渲染：

- 一句总诊断
- 当前判断
- 立即需要动手的修正重点
- 阻碍继续推进的问题
- 需要 PM、研究或业务补充判断的问题

### Changes Since Last Review

只有在同一个 `review-slug` 被持续复审时才使用。
保持简短，并紧跟在 `Executive Summary` 后面。

渲染：

- 新增问题
- 已解决问题
- 有实质变化的问题
- 严重度上升的问题（如果有）

### Highest-Priority Issue

渲染：

- `display_number`
- `stable_id`
- `title`
- `severity`
- `confidence`
- 一个说人话的诊断段落
- 一个说明“为什么它排第一”的段落
- 一个解释修正路径与推荐方向的段落
- 如果推荐质量受 PM、业务或技术约束影响，再补一个短的 `需要确认` 段落

### Background and Evidence

这一节用简洁 prose 写，不写成过程日志。

只包含人类读者真正需要知道的内容：

- 这次实际看了什么材料
- 最相关的可见证据
- 重建出来的上下文和业务目标
- 会影响建议质量的真实边界或工具限制

除非用户明确要求审计式输出，否则不要暴露 unit 选择过程、coverage 记账或工具调用顺序。

### Full Review

渲染：

- 排名前三的问题
- 面向设计师阅读的问题列表
- 一个总结视图，覆盖问题分布、修正路径分组和关键风险
- 场景压力测试

每张 issue card 至少包含：

- `display_number`
- `stable_id`
- `title`
- `category`
- `severity`
- `confidence`
- 一个诊断段落，把可见事实、问题本质和后果合在一起
- 一个修正段落，说明应该怎么改、为什么这么改
- 只有在未解约束会实质影响建议时，才补一个短的 `需要确认` 段落

### Three-Flow Consistency

这一节必须作为独立大模块，紧跟在 `Full Review` 后面。

目的：

- 让连续性检查显式可见，而不是埋在问题 prose 里
- 判断设计是不是一条能走通的任务链，而不是一堆局部正确的页面

展示形态是沿主旅程排布的一条纵向时间轴，不是三篇抽象长文。

渲染：

- 左侧一条纵向时间轴，包含 4 到 8 个旅程节点
- 每个节点右侧一张卡片
- 当有助于定位时，再加可选的阶段摘要
- 卡片里最多三类问题块：`旅程流`、`操作流`、`心智流`
- 最后补一段短综合判断，说明三条流是在互相支撑，还是彼此打架

每个节点都应：

- 使用对齐真实旅程的阶段标题，不要用抽象 checkpoint 名
- 只展示真正存在明显问题的 flow block
- 没问题时不写 `normal`、`pass` 之类的废话

渲染器可以临时构建一个 `timeline_nodes[]` view model，仅用于 HTML。
这个辅助结构可以包含阶段标题、可选阶段摘要，以及可选的 `journey_issue`、`operation_issue`、`mental_issue`，但绝不能写回 `review-state.json`。

每个问题块只解释三件事：

- 一个简短的人话标题，例如 `旅程流断裂`、`操作流不清`
- 问题是什么
- 解法是什么

### Resolution Tracks

不要把这一节再写成第二份问题列表。

它应该是一个紧凑总结模块，和其他 full-review 摘要面板放在一起。

回答这些问题：

- 哪些问题应该作为一批结构修正一起处理
- 当前建议的结构路径是什么
- 如果继续维持现状，团队会损失什么

它应明显短于 issue cards 和三流一致性模块。

### Open Questions

把待确认问题按优先级清楚列出来。

### Next Actions

渲染：

- 设计师现在就能改什么
- 哪些点要和 PM 或业务对齐
- 实施前还要从 Figma 回读什么

## 视觉系统

这份 HTML 报告是 `design-buff` 内嵌的一套小型设计系统。

设计意图：

- 用编辑式层级，而不是 dashboard 外观
- 用有判断的排版，而不是默认 web 样式
- 用有节奏的留白，而不是一模一样的卡片网格
- 用证据驱动结构，而不是装饰性噪音
- 有明确识别度，但不牺牲可读性

必备组件：

- `hero masthead`：项目、当前判断、语言、intake 状态和顶层元信息
- `diagnosis rail`：一句诊断和最紧急的动作
- `issue spotlight`：最高优先级问题要做成首屏主特征块
- `issue cards`：每个问题一张可复用结构卡
- `evidence chips`：紧凑展示 node、截图、置信度和工具缺口
- `action columns`：宽屏下把待确认问题和下一步动作并排呈现

视觉约束：

- 使用偏暖的浅色底和中性色
- 标题、正文、元信息三套字有明确分工
- 用分隔线和留白建立节奏
- 最高优先级问题必须占住首屏主导位置
- 动效只做轻量 reveal，并尊重 reduced-motion
- 不要做成 metrics dashboard
- 不要依赖通用渐变、玻璃卡、发光
- 不要每一节都堆一模一样的卡片
- 不要让 oversized hero 装饰把诊断压到首屏以下

## 可访问性

- 对比度足够支撑长文阅读
- 行宽保持在舒服范围
- 标题和列表结构保持语义化
- 键盘可导航，不依赖隐藏控件
- 响应式下，笔记本和手机都能顺畅阅读

## 人类写作规则

最终的人类报告要像一份编辑式设计审核，而不是导出的字段表。

必须做到：

- 标题和段落先按人话写
- 优先用一到两个强段落，而不是六个小标签
- 机器身份藏在 `stable_id`，不要写进拗口标题
- `report_language` 是 `zh-CN` 时，中文必须像中文团队真实会写的东西
- 标题、子标题和界面标签都要翻成目标报告语言

明确避免：

- 除非用户明确要求审计口径，否则不要在 HTML 里露出 `what i see`、`likely consequence`、`discussion prompt` 这类 schema 标签
- 不要把英文分析名词直接硬翻成中文
- 不要在面向人的报告里使用 `结构包`、`整改包` 这类 PM 腔
- 不要用压缩短语把角色、动作和后果都藏掉

好的中文标题模式：

- `谁在什么地方不知道什么，却被要求先做什么`
- `页面让用户做关键决定，但没有告诉他会发生什么`
- `成功页宣布结果了，但没有把下一步价值接住`

如果一句话读起来像来自表格、schema 或机器翻译，就在落盘前重写。

## Hidden Scratch Rules

hidden scratch 放在 `.design-buff/<review-slug>/` 下。

允许写入：

- JSON 状态
- 原始工具缓存
- 运行元数据

不允许写入：

- Markdown 评审文档
- 面向人的问题 prose
- executive summary 正文
- recommendation 正文

只要一个 hidden 文件可能被误认成正式评审，它就不该在那里。

## 模板基准

结构和样式以 `templates/report-shell.html` 为基准。
视觉语境以 `references/report-style-context.md` 为基准。
最终结果必须看起来仍然来自同一套设计系统。
