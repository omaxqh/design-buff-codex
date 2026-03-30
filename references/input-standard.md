# 输入标准

这份文件只负责 intake 精度和升级策略。报告、HTML 与 sidecar 的输出规则在别的文件里定义。

## 推荐的 Figma 输入

做 Figma 审核时，最理想的输入是已经带上 `fileKey` 和 `node-id` 的 board 或 frame URL。

可接受的输入示例：

- 一个明确指向某条旅程图或某块 review board 的 board URL
- 一个明确指向单个页面、弹窗或状态的 frame URL
- 一个 frame URL，再加 PRD 或补充说明

设计师不需要一开始就给每个页面都贴一个链接。一个 board 或 frame URL 就足够开始 intake。

## 尽量避免

- 没有 `node-id` 的文件首页 URL
- 明明只想审一个 board，却给整页或整文件
- 已经有可用 Figma 链接时，还用截图替代

如果用户只给了很宽泛的文件 URL，先定位目标 board 或 frame，再开始审核。

## 精度要求

`design-buff` 应该：

- 以 intake board 或 frame 作为根节点
- 自动把大 board 拆成 screen-level review units
- 对每个 review unit 用 `get_design_context` 精读，再用 `get_screenshot` 交叉确认
- 只有当该 unit 已经被完整读过，才宣称高精度

`design-buff` 不应该：

- 把一张巨大的 board 截图假装成精确的 screen read
- board 太大时悄悄退化成模糊点评
- 在自己尝试自动拆分前，就让设计师先补十几个 URL

## 升级与兜底

如果 Figma MCP 不可用，或重复出现工具边界导致精度受阻：

- 继续使用当前能拿到的最佳可见证据
- 明确写出被卡住的细节
- 微观细节问题下调置信度
- 只有在自动拆分路径彻底走不通时，才要求补更窄的材料
