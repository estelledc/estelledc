# Jason Xun

**AI Application Engineer · Reliable agents, RAG/evals · Web/iOS delivery**

我做可运行、可评测、可恢复的 AI 应用。不只把模型接进产品，也把工具边界、失败语义、证据回放和人工责任写进系统：它做了什么、为什么失败、怎样重放、何时交还给人，都应该说得清。

> **English summary:** I build reliable AI applications with bounded tools, replayable evaluation, explicit failure semantics, and human ownership across Web and iOS delivery.

[Work](https://estelledc.github.io/work/) · [Résumé](https://estelledc.github.io/resume/) · [About](https://estelledc.github.io/about/)

## Selected evidence

- **[TraceFetch](https://github.com/estelledc/tracefetch)** — `v1.0 · Public source` 把搜索候选与可信证据分开，产出带原文、锚点、收据和 SHA-256 的可验证 evidence bundle；不判断来源真假，也不绕过访问控制。
- **[BJ-Pal](https://github.com/estelledc/bj-pal)** — `v6.29 · Public source` 用 durable jobs、有界模型执行和可复算评测承载短途规划；公开证据不外推生产容量或用户效果。
- **[Tencent/WeKnora PR #1785](https://github.com/Tencent/WeKnora/pull/1785)** — `Merged OSS contribution` 过滤 Excel 中的 DISPIMG / IMAGE 图像函数串，并补齐 4 条回归用例。
- **[web-plan-execute](https://github.com/estelledc/web-plan-execute/releases/tag/v0.9.0-rc.1)** — `0.9.0-rc.1 · Public RC` 把规划、独立复审、执行、交接和验证收敛为一份可恢复的 living ExecPlan；当前仍是 RC。

产品案例、私有项目与 iOS 经历统一由 Work 页面承载。

## How I work

- **失败关闭** — 权限、证据或边界不满足就停止并暴露原因，不静默降级成“成功”。
- **可重放评测** — 保存输入、来源、版本、决策和收据，让结果能复算、对比和回归。
- **诚实边界** — Release、RC 与测试收据只证明对应版本和范围，不等于生产 SLA、规模化运行或真实用户效果；AI 的越界点和人的最终责任必须明确。
