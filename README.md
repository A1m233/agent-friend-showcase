# agent-friend showcase snapshot

This repository is a sanitized public showcase snapshot of a private development repository.

It is intended for portfolio and resume review:

- no original git history is included
- local credentials, private data, generated caches, and vendor demo secrets are excluded
- coding-agent workflow harness files are intentionally kept where they are useful context
- this snapshot is not guaranteed to be continuously maintained

## What is included

`agent-friend` is a desktop companion-AI prototype with a Python engine, memory system,
HTTP/SSE bridge, voice control plane, and a Tauri + React desktop frontend.

Main areas:

| Path | Purpose |
| --- | --- |
| `agent/` | Conversation engine, personas, prompt composition, context management, tools |
| `memory/` | SQLite-backed long-term memory extraction and retrieval |
| `agent_bridge/` | HTTP/SSE bridge with OpenAI-compatible and AG-UI style routes |
| `voice_bridge/` | Voice-call control plane and RTC integration boundary |
| `frontend/` | Tauri 2 + React desktop shell, pet surface, chat UI, settings, memory inspector |
| `.cursor/`, `.Codex/`, `.claude/` | Coding-agent workflow rules and skill harness |

## Running locally

Install Python 3.12 and `uv` first. Desktop frontend work also needs Node 22+, pnpm, and Rust.

```bash
./scripts/setup/run.sh
cp .env.example .env
# Fill the required provider keys in .env.
./scripts/cli/run.sh
```

For the desktop surface:

```bash
./scripts/dev/run.sh --web
```

Then open `http://localhost:1420/chat.html`.

The public `.env.example` keeps IM/vendor integrations disabled by default and stores local
runtime data under `.agent-friend-data/`. Fill the LLM provider key to try chat; enable optional
vendor integrations only after adding your own credentials.

Use `./scripts/check/run.sh` to run the local quality gate. Some optional voice flows require
real provider credentials and are not executed by the showcase snapshot pipeline.

## Snapshot provenance

The private source repository remains private. This public copy is produced by
`scripts/showcase-snapshot/`, which uses an allowlist-first copy strategy and then runs a
privacy/secret scan before reporting success.
