---
name: design-buff
description: 用 Figma、截图、文档或 Figma MCP 做设计审核；优先从业务与体验角度还原场景，再输出设计师可读的 HTML 报告和机器可追踪的 sidecar。
compatibility: 最适合支持 MCP 和 Figma MCP 的运行时；没有 MCP 时可退化为截图和文档审核。
metadata:
  version: "0.7"
---

# `design-buff`

这个 skill 用来做面向业务与体验的设计审核。它的工作不是给出空泛表扬，也不是停留在审美评论，而是先还原上下文，再判断这份设计到底哪里会让用户停住、犹豫、走错，或干脆放弃。

## 适用场景

- 设计师在正式评审前做自查
- 需要从产品和体验角度诊断方案，而不是只看视觉
- 设计稿没有完整背景，需要先重建场景和目标
- 有 Figma 链接或节点时，借助 MCP 做高精度读取
- 需要按问题逐条给出根因和修正方向
- Agent 工作流里需要结构化的设计审核输出

## 不适用场景

- 纯视觉风格点评
- 没有产品或体验问题，只想追热点风格建议
- 从零生成整套设计系统
- 本应依赖正式用户研究的问题
- 用户没有明确要求时，直接改 Figma 文件

## 工作模型

这个 skill 严格遵循“读证据 -> 做判断 -> 出结果”的模型。

- `design-buff/` 目录只放说明和模板，不承接运行时写入
- 正式输出写到 `design-buff-reviews/<review-slug>/`
- 技术性临时状态可以写到 `.design-buff/<review-slug>/`
- 对话总结、`report.html` 和 `review-state.json` 必须来自同一个 canonical review object

更细的输出、报告和 scratch 规则见 `references/report-contract.md`。

## 输入与证据优先级

支持的输入包括：

- 带 `node-id` 和 `fileKey` 的 Figma board 或 frame URL
- 指向 Figma 文件、frame 或 node 的 URL
- 支持 selection MCP 的运行时里的当前 Figma 选中内容
- 截图
- 长图
- 导出的设计帧
- 局部页面
- 本地设计导出文件路径
- PRD、功能说明、研究资料、业务补充材料

能选时，优先按这个顺序取证：

1. 用户明确确认过的上下文
2. PRD、产品文档或业务材料
3. Figma 结构化数据
4. 截图或导出图
5. 明确标注过的模型推断

无论何时都要区分：

- `confirmed`
- `visible`
- `inferred`
- `unknown`

更具体的 Figma intake 规则见 `references/input-standard.md`。
Figma 链接需要快速规范化时，用 `scripts/parse_figma_url.py`。

## 运行模式

默认报告模式是 `self-check`。

只有在这些情况下才切到 `agent-review`：

- 用户明确要求机器友好输出
- 当前流程明显处于 agent workflow 中
- 被审对象本身就是 agent 生成的设计输出

无论哪种模式，都要同时产出 `report.html` 和 `review-state.json`。

## 运行状态机

### 1. 规范化 intake

先选最窄、但不牺牲判断质量的 intake 通道：

- `figma-board lane`
- `figma-structure lane`
- `draft-first lane`
- `draft + materials lane`

在 intake 阶段要做这些事：

- 规范化输入 URL 和 node ID
- 识别或创建 `review-slug`
- 如果之前评过同一对象，先加载已有的 `report.html` 和 `review-state.json`
- hidden scratch 只用于技术恢复，不要当正式输出

### 2. 采集证据

如果 Figma MCP 可用，按层读取：

1. `get_metadata`
2. `get_screenshot`
3. `get_design_context`
4. 当 token、变量或命名意图重要时再读 `get_variable_defs`
5. 只有在需要精确核对文字、图标、组件或原型时，才用 `use_figma`

读 Figma 时保持这些纪律：

- 用户没有明确要求时，不改 Figma 文件
- 不要一上来就读整个文件
- 用最小、但能回答当前问题的节点
- intake 根节点太大时，先自动拆 review units

大 board 需要拆 screen-like 单元时，用 `scripts/pick_figma_review_units.py`。
board 很大、文案和图标语义很关键、或必须精确记录工具边界时，看 `references/figma-high-precision.md`。

如果只有截图或导出图：

- 从可见证据里推断背景
- 明确写出信心和证据来源
- 只有当缺失背景会实质改变判断时，才要求补材料

### 3. 重建背景

正式批评前，先搞清楚这份设计想帮助谁、完成什么、处在链路哪一步。

- 背景重建、确认问题和证据信号规则见 `references/review-playbook.md`
- 人类报告和结构化 sidecar 必须基于同一份背景理解同步更新

### 4. 做判断并给修正方向

审核重点是产品和体验的合理性，不是表面好不好看。

- 维度、必跑检查、问题结构、严重度、置信度、稳定问题标识、修正路径逻辑，统一看 `references/review-playbook.md`
- 至少对一条关键任务链显式执行 `three-flow continuity review`，检查旅程流、操作流、心智流是否连成一条链
- 用户选中某个问题后，要继续往下给修正方向，不要停在点评
- 需要稳定 mixed-format issue ID 时，用 `scripts/make_issue_id.py`

### 5. 形成 canonical review object

所有正式输出都必须来自同一个 canonical review object。

- sidecar 的合法结构见 `references/review-state-schema.md`
- 核心对象保持精简
- 不要把 HTML 模板当内部 schema

### 6. 渲染输出

从同一个 canonical review object 渲染三份结果：

1. 精炼的对话启动总结
2. `report.html`
3. `review-state.json`

- 报告语言、对话顺序、HTML 标记、分段内容和 hidden scratch 规则见 `references/report-contract.md`
- 语言信号混杂时，用 `scripts/detect_report_language.py`
- 写出 `report.html` 前，先做一遍“说人话”的润色，让它读起来像设计负责人写的审核意见，而不是字段拼接

### 7. 持久化状态

正式写入：

- 更新 `design-buff-reviews/<review-slug>/report.html`
- 更新 `design-buff-reviews/<review-slug>/review-state.json`

hidden scratch 可以保存：

- JSON 状态
- 运行元数据
- review unit 拆分结果
- read coverage
- evidence manifest
- 原始工具缓存

除非用户明确要求，不要把面向人的评审正文写进 hidden scratch。

## 报告风格

### `self-check`

读者：

- 做自查和修稿的设计师

风格：

- 直接
- 锐利
- 简洁
- 像在带人修问题
- 面向决策

### `agent-review`

读者：

- 另一个 agent
- 下游自动化步骤

风格：

- 结构清楚
- 证据先行
- 优先级明确
- 机器可继续处理

两种模式都必须保持对话和 HTML 的结论一致。

## 不可妥协的规则

- 除非审美问题直接影响清晰度、信任或任务完成，不要默认去聊风格。
- 不要给“干净现代”这类空泛表扬。
- 在认可方案前，先确认问题本身有没有判断对。
- 优先给结构修正，不要优先给装饰修正。
- 明确区分什么是看得到的，什么是推断出来的。
- 不确定的结论要当成假设写。
- 有 Figma 结构化证据时，它比截图推断更强。
- 如果最大问题是战略或上下文问题，要先说这个，再说页面细节。
- 尽量引用具体 frame、node 或可见证据。
- 工具边界卡住精度时，记录具体工具、节点和缺失内容，不要硬猜。

## 参考地图

只在任务需要时再读这些文件：

- `references/input-standard.md`：更细的 intake 规则
- `references/figma-high-precision.md`：大 board 或精确核对场景下的读取路径
- `references/review-playbook.md`：背景重建、审核维度、问题结构、修正逻辑
- `references/report-contract.md`：对话、HTML 报告、语言规则、hidden scratch 规则
- `references/review-state-schema.md`：`review-state.json` 的结构边界
- `references/report-style-context.md`：人类报告的视觉方向

内置脚本：

- `scripts/parse_figma_url.py`
- `scripts/pick_figma_review_units.py`
- `scripts/make_issue_id.py`
- `scripts/detect_report_language.py`
