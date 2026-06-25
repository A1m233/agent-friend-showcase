# scripts/

Project operations are wrapped as scripts so contributors do not need to remember long
`uv`, `pytest`, or frontend commands.

| Script | Purpose | mac / linux | windows |
| --- | --- | --- | --- |
| `setup/` | Initialize the Python workspace, create `.env`, and check optional frontend tools | `./scripts/setup/run.sh` | `.\scripts\setup\run.ps1` |
| `cli/` | Start the CLI debug UI | `./scripts/cli/run.sh` | `.\scripts\cli\run.ps1` |
| `bridge/` | Start the HTTP/SSE bridge | `./scripts/bridge/run.sh` | `.\scripts\bridge\run.ps1` |
| `dev/` | Start bridge plus frontend desktop/web development flow | `./scripts/dev/run.sh [--web]` | `.\scripts\dev\run.ps1 [--web]` |
| `voice/` | Start the voice bridge control plane | `./scripts/voice/run.sh` | `.\scripts\voice\run.ps1` |
| `test/` | Run pytest | `./scripts/test/run.sh` | `.\scripts\test\run.ps1` |
| `lint/` | Run backend lint checks | `./scripts/lint/run.sh` | `.\scripts\lint\run.ps1` |
| `typecheck/` | Run mypy | `./scripts/typecheck/run.sh` | `.\scripts\typecheck\run.ps1` |
| `check/` | Run the combined local quality gate | `./scripts/check/run.sh` | `.\scripts\check\run.ps1` |
| `frontend/*` | Install, lint, test, build, or run frontend tasks | `./scripts/frontend/*.sh` | `.\scripts\frontend\*.ps1` |
| `im-smoke/` | Run the fake-LLM IM smoke test | `./scripts/im-smoke/run.sh` | `.\scripts\im-smoke\run.ps1` |
| `showcase-snapshot/` | Regenerate this sanitized public snapshot from the private source repo | `./scripts/showcase-snapshot/run.sh` | `.\scripts\showcase-snapshot\run.ps1` |

Scripts that intentionally trigger real LLM or vendor smoke calls are omitted from the public
snapshot command index.
