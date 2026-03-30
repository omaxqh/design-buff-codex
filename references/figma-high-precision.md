# Figma 高精度读取

当手上有 board 或 frame URL，且这次审核需要精确判断文案、图标语义或状态差异时，使用这份流程。

## 目标

把一个 board 或 frame URL，拆成既足够小、能读准细节，又足够完整、能支持产品判断的一组 review units。

## Intake 流程

1. 先规范化 intake URL。
2. 对 intake 根节点调用 `get_metadata`。
3. 对 intake 根节点调用 `get_screenshot`。
4. 尝试对 intake 根节点调用 `get_design_context`。
5. 如果节点过大，或只返回稀疏 metadata，就继续拆成 review units。

## Review Unit 选择启发

优先选择这些子节点：

- 尺寸像真实页面的 `frame`
- 代表单一状态、单一步骤或单一分支
- 包含丰富可见文案、CTA、表单字段或状态提示

通常不应优先当主阅读单元的有：

- 装饰性矢量
- 连线箭头
- slices
- 巨大的拼贴外壳
- 只是给别的页面做标题的独立标签

## 递归拆分规则

如果某个 unit 继续只返回稀疏信息，或依旧过大：

- 再往下一层
- 选最小、但仍然保留一个完整任务或状态语义的子 frame
- 只有当这个 unit 能产出有用的 contextual read，或已经没有更有意义的 UI 分组时才停

## 微观细节的证据梯度

- `high`：拿到了精确文案、命名实例、命名组件，或直接 contextual read 与截图一致
- `medium`：截图可见、结构上也说得通，但没有精确 node 命名支撑
- `low`：只能从密集视觉里推断，或被工具边界挡住

## 工具不一致规则

如果 `get_metadata` 和 `get_design_context` 都能读到某个节点，但 `use_figma` 找不到：

- 以 `get_metadata + get_design_context + get_screenshot` 作为主证据集
- `use_figma` 只用于它能真实解析到的节点
- 在报告里记下这个 mismatch，不要靠猜补齐

## Code Connect 阻塞

如果 `get_design_context` 因 Code Connect 提示被打断：

- 按工具提示继续处理
- 不要把它误判成“设计无法读取”
- 提示处理完后，继续主读取路径
