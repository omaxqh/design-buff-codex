# Design Buff

这是给 `Codex` 直接安装使用的最小运行仓库，不是维护源码仓库。

`Design Buff` 是一个面向业务与体验的设计审核 skill，不是审美打分器。它会根据 Figma、截图、页面结构和补充材料，还原这条设计到底服务谁、要完成什么任务、处在链路的哪一步，再判断真正的问题是不是出在结构、认知成本、信任建立或连续性上。

## 这个 Skill 用来做什么

- 设计师自查和方案复盘
- 关键转化流程的体验诊断
- Figma、截图、PRD 混合输入下的设计审核
- 发现页面局部没错、但整条链路不顺的结构问题

## 在 Codex 里怎么触发

- 如果你是让 AI 直接按 GitHub URL 安装，这个仓库本身就可以直接安装
- 直接在对话里写明你的设计审核需求，并附上 Figma、截图或相关材料
- 想明确点名时，直接写 `$design-buff`
- 如果已经有同一条方案的旧评审，继续沿用同一个 `review-slug`

## 会生成什么

- 人看的报告：`design-buff-reviews/<review-slug>/report.html`
- 机器状态：`design-buff-reviews/<review-slug>/review-state.json`
- 临时技术状态：`.design-buff/<review-slug>/`

`report.html` 是正式的人类评审报告；`review-state.json` 只用于结构化追踪、复跑和对比，不是第二份报告。
