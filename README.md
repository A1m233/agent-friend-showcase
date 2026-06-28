# agent-friend 公开展示快照

这是 `agent-friend` 私有开发仓库的公开展示快照，用于简历、作品集和技术交流场景。

它不是原始开发仓库，也不承诺持续维护。公开版本经过脚本化处理：

- 不包含原始 git history
- 不包含本地凭据、私有数据、生成缓存和真实厂商 demo 配置
- 保留必要的 Coding Agent 工作流配置，用于展示工程协作和 harness 设计
- 通过 allowlist-first 的 snapshot pipeline 生成，并附带扫描报告

## 这个项目在做什么

`agent-friend` 是一个桌面陪伴型 AI 原型。目标不是做一个普通聊天工具，而是把
LLM、长期记忆、桌面形态、语音通道和多入口接入组合成一个“常驻桌面的 AI 朋友”。

当前公开快照能展示的重点包括：

- **对话引擎**：纯 Python 的多轮对话编排，包含 session、persona、system prompt 组装、
  tool calling、上下文裁剪 / 摘要压缩，以及用户消息编辑重发等交互能力。
- **长期记忆**：基于 SQLite 的记忆抽取、reconcile、持久化和检索召回，目标是跨会话保留
  用户事实、偏好和重要事件。
- **桌面前端**：Tauri 2 + React 的多窗口桌面应用，包含传统聊天页、Live2D 桌宠窗口、
  气泡窗口、设置页和记忆查看器。
- **服务边界**：`agent_bridge` 通过 HTTP/SSE 暴露 OpenAI-compatible 与 AG-UI 风格接口；
  `voice_bridge` 承载语音通话控制面、RTC 集成边界和 LLM proxy。
- **工程工作流**：需求 / 决策文档、脚本化开发入口、单元测试、记忆评测 harness，以及
  面向 Coding Agent 协作的 rules / skills。

## 仓库内容

主要模块：

| 路径 | 说明 |
| --- | --- |
| `agent/` | 对话引擎核心：conversation loop、session、persona、prompt、context、tools |
| `memory/` | 长期记忆系统：SQLite store、LLM 抽取、reconcile、检索召回 |
| `memory_eval/` | 记忆召回质量评测：benchmark adapter、LLM judge、baseline report |
| `llm_providers/` | LLM provider 适配层，当前通过 LiteLLM 收敛不同模型服务 |
| `agent_bridge/` | HTTP/SSE bridge，提供 OpenAI-compatible、AG-UI、IM 与内部 push 边界 |
| `voice_bridge/` | 语音通话控制面与 RTC / ASR / TTS 集成边界 |
| `frontend/` | Tauri 2 + React 桌面端：聊天、桌宠、气泡、设置、记忆查看器 |
| `docs/` | 产品愿景、技术决策、需求文档和配套设计 |
| `scripts/` | 跨平台开发脚本：setup、dev、check、test、lint、frontend 等 |
| `.cursor/`, `.Codex/`, `.claude/` | Coding Agent 规则、skills 与协作 harness |

可以优先看的入口：

- [`docs/decisions/0001-product-vision-and-roadmap/README.md`](docs/decisions/0001-product-vision-and-roadmap/README.md)：产品愿景和路线图
- [`docs/decisions/0002-incubation-tech-stack/README.md`](docs/decisions/0002-incubation-tech-stack/README.md)：孵化期技术栈与架构边界
- [`agent/README.md`](agent/README.md)、[`memory/README.md`](memory/README.md)：核心引擎和记忆模块说明
- [`frontend/src/pages/chat/`](frontend/src/pages/chat/) 与 [`frontend/src/pages/pet/`](frontend/src/pages/pet/)：桌面聊天页和桌宠窗口
- [`scripts/README.md`](scripts/README.md)：本地开发脚本清单

## 公开快照范围

这个仓库保留了能说明工程结构和核心实现的代码与文档，但不是完整私有开发环境：

- 没有原始 git history、issue 讨论、私有探索记录和本地调试缓存
- `.env.example` 只保留示例配置，不包含真实凭据
- IM、语音和厂商集成默认关闭或需要你自己的服务凭据
- `SHOWCASE-SCAN-REPORT.md` 是生成快照时的扫描报告，用于说明公开版本的脱敏结果

## 本地运行

先安装 Python 3.12 和 `uv`。如果要运行桌面前端，还需要 Node 22+、pnpm 和 Rust。

macOS / Linux：

```bash
./scripts/setup/run.sh
cp .env.example .env
# 在 .env 中填入必要的模型服务 key
```

Windows PowerShell：

```powershell
.\scripts\setup\run.ps1
Copy-Item .env.example .env
# 在 .env 中填入必要的模型服务 key
```

启动桌面端：

```bash
./scripts/dev/run.sh
```

```powershell
.\scripts\dev\run.ps1
```

这会同时启动本地 bridge 和 Tauri 桌面前端。首次运行会编译 Rust，时间会稍长。

如果只想快速验证聊天窗口，也可以使用浏览器调试模式：

```bash
./scripts/dev/run.sh --web
```

然后打开 `http://localhost:1420/chat.html`。

命令行调试入口是可选的：

```bash
./scripts/cli/run.sh
```

```powershell
.\scripts\cli\run.ps1
```

公开版 `.env.example` 默认关闭 IM 和厂商集成，并把本地运行数据放在
`.agent-friend-data/` 下。填入 LLM provider key 后即可试用对话；可选厂商集成
请在换成你自己的凭据后再启用。

运行质量检查：

```bash
./scripts/check/run.sh
```

```powershell
.\scripts\check\run.ps1
```

部分语音链路需要真实厂商凭据，不会在公开 snapshot pipeline 中执行。

## 快照来源

真实开发仓库保持 private。这个公开副本由 `scripts/showcase-snapshot/` 生成：
先按 allowlist 复制必要文件，再做规则化替换和隐私/凭据扫描，扫描通过后输出报告。
