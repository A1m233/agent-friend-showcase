# agent-friend 公开展示快照

这是 `agent-friend` 私有开发仓库的公开展示快照，用于简历、作品集和技术交流场景。

它不是原始开发仓库，也不承诺持续维护。公开版本经过脚本化处理：

- 不包含原始 git history
- 不包含本地凭据、私有数据、生成缓存和真实厂商 demo 配置
- 保留必要的 Coding Agent 工作流配置，用于展示工程协作和 harness 设计
- 通过 allowlist-first 的 snapshot pipeline 生成，并附带扫描报告

## 项目内容

`agent-friend` 是一个桌面陪伴型 AI 原型，包含 Python 对话引擎、长期记忆、
HTTP/SSE bridge、语音控制面，以及 Tauri + React 桌面前端。

主要模块：

| 路径 | 说明 |
| --- | --- |
| `agent/` | 对话引擎、persona、系统提示词组装、上下文管理和工具调用 |
| `memory/` | 基于 SQLite 的长期记忆抽取、存储与召回 |
| `agent_bridge/` | HTTP/SSE bridge，提供 OpenAI-compatible 与 AG-UI 风格出口 |
| `voice_bridge/` | 语音通话控制面与 RTC 集成边界 |
| `frontend/` | Tauri 2 + React 桌面壳、桌宠界面、聊天 UI、设置和记忆查看器 |
| `.cursor/`, `.Codex/`, `.claude/` | Coding Agent 规则、skills 与协作 harness |

## 本地运行

先安装 Python 3.12 和 `uv`。如果要运行桌面前端，还需要 Node 22+、pnpm 和 Rust。

```bash
./scripts/setup/run.sh
cp .env.example .env
# 在 .env 中填入必要的模型服务 key
./scripts/cli/run.sh
```

运行 web 调试版桌面界面：

```bash
./scripts/dev/run.sh --web
```

然后打开 `http://localhost:1420/chat.html`。

公开版 `.env.example` 默认关闭 IM 和厂商集成，并把本地运行数据放在
`.agent-friend-data/` 下。填入 LLM provider key 后即可试用对话；可选厂商集成
请在换成你自己的凭据后再启用。

运行质量检查：

```bash
./scripts/check/run.sh
```

部分语音链路需要真实厂商凭据，不会在公开 snapshot pipeline 中执行。

## 快照来源

真实开发仓库保持 private。这个公开副本由 `scripts/showcase-snapshot/` 生成：
先按 allowlist 复制必要文件，再做规则化替换和隐私/凭据扫描，扫描通过后输出报告。
