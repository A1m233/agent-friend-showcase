from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT.parent / "agent-friend-showcase-snapshot"
SENTINEL = ".agent-friend-showcase-snapshot"


EXACT_ROOT_FILES = {
    ".gitignore",
    ".python-version",
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "uv.lock",
}

EXACT_FRONTEND_FILES = {
    "frontend/.nvmrc",
    "frontend/bubble.html",
    "frontend/chat.html",
    "frontend/components.json",
    "frontend/eslint.config.js",
    "frontend/index.html",
    "frontend/memory-inspector.html",
    "frontend/package.json",
    "frontend/pet.html",
    "frontend/pnpm-lock.yaml",
    "frontend/pnpm-workspace.yaml",
    "frontend/settings.html",
    "frontend/tsconfig.app.json",
    "frontend/tsconfig.json",
    "frontend/tsconfig.node.json",
    "frontend/vite.config.ts",
    "frontend/vitest.config.ts",
}

ALLOW_PREFIXES = (
    ".cursor/rules/",
    ".cursor/skills/",
    ".Codex/skills/",
    ".claude/skills/",
    "agent/",
    "agent_bridge/",
    "llm_providers/",
    "memory/",
    "tools/",
    "voice_bridge/",
    "shared/",
    "frontend/src/",
    "frontend/src-tauri/",
    "frontend/public/",
    "frontend/scripts/",
)

MEMORY_EVAL_PREFIXES = (
    "memory_eval/src/",
    "memory_eval/tests/",
)

DOC_EXACT_FILES = {
    "docs/decisions/README.md",
    "docs/requirements/README.md",
}

DOC_SUFFIXES = (
    "/README.md",
    "/requirement.md",
    "/design.md",
    "/test-plan.md",
)

SCRIPT_DIR_ALLOWLIST = {
    "bridge",
    "check",
    "cli",
    "dev",
    "dev-bubble-spotcheck",
    "dev-fire-source",
    "dev-push-subscribe",
    "fix",
    "frontend",
    "im-smoke",
    "lint",
    "setup",
    "showcase-snapshot",
    "test",
    "typecheck",
    "voice",
}

DENY_PATTERNS = (
    ".git/**",
    ".env",
    ".env.*",
    ".claude/settings.local.json",
    ".claude/worktrees/**",
    ".kilo/**",
    ".cache/**",
    ".venv/**",
    "**/__pycache__/**",
    "**/*.pyc",
    "**/.pytest_cache/**",
    "**/.ruff_cache/**",
    "**/.mypy_cache/**",
    "**/node_modules/**",
    "**/.pnpm-store/**",
    "**/target/**",
    "**/dist/**",
    "**/*.tsbuildinfo",
    "client/**",
    "docs/issues/**",
    "docs/explorations/**",
    "docs/**/progress.md",
    "docs/requirements/**/smoke.py",
    "experiments/**",
    "memory_eval/data/**",
    "memory_eval/baselines/**",
    "scripts/codex-adapters/**",
    "scripts/dev-pet-bubble-demo/**",
    "scripts/memory-eval/**",
    "scripts/voice-smoke/**",
    "experiments/voice-poc/rtc-aigc-demo/Server/scenes/Custom.json",
)

TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".lock",
    ".md",
    ".mdc",
    ".mjs",
    ".ps1",
    ".py",
    ".rs",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

PRIVATE_USER = "albert" + "tchen"
PRIVATE_DISPLAY_NAME = "Kha" + "lil"
PRIVATE_MAC_HOME = "/Users/" + PRIVATE_USER
PRIVATE_WIN_HOME = r"C:\Users" + "\\" + "chens"

SOURCE_SAFE_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(re.escape(PRIVATE_DISPLAY_NAME), re.IGNORECASE), "<example-user>"),
    (re.compile(re.escape(PRIVATE_USER), re.IGNORECASE), "example-user"),
    (re.compile(re.escape(PRIVATE_MAC_HOME)), "/Users/example"),
    (re.compile(re.escape(PRIVATE_WIN_HOME), re.IGNORECASE), r"C:\\Users\\example"),
    (
        re.compile(r"AppData\\Roaming\\agent-friend", re.IGNORECASE),
        r"AppData\\Roaming\\agent-friend-example",
    ),
]

DOC_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    *SOURCE_SAFE_REPLACEMENTS,
    (re.compile(r"im:qq:[A-Za-z0-9_-]+"), "im:qq:<example-openid>"),
    (re.compile(r"prod_session/[A-Za-z0-9:_#+ -]+"), "prod_session/<example-session>"),
    (re.compile(r"openid=([A-Fa-f0-9]{8})[A-Fa-f0-9]+"), r"openid=\1..."),
    (re.compile(r"user_openid\s*=\s*[A-Fa-f0-9]{8}[A-Fa-f0-9]+"), "user_openid = <example-openid>"),
    (
        re.compile(r"https://[A-Za-z0-9-]+\.trycloudflare\.com"),
        "https://example-tunnel.trycloudflare.com",
    ),
    (
        re.compile(r"https://[A-Za-z0-9-]+\.ngrok-free\.app"),
        "https://example-tunnel.ngrok-free.app",
    ),
]


@dataclass(frozen=True)
class Finding:
    severity: str
    category: str
    path: str
    line: int
    snippet: str


SCAN_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "error",
        "local absolute path",
        re.compile(
            r"("
            + re.escape(PRIVATE_MAC_HOME)
            + r"|"
            + re.escape(PRIVATE_WIN_HOME)
            + r"|AppData\\(?:Roaming|Local))",
            re.I,
        ),
    ),
    (
        "error",
        "private name",
        re.compile(
            r"\b(" + re.escape(PRIVATE_DISPLAY_NAME) + r"|" + re.escape(PRIVATE_USER) + r")\b", re.I
        ),
    ),
    (
        "error",
        "qq session id",
        re.compile(r"im:qq:(?!<example-openid>|OPENID(?:-|$))[A-Za-z0-9_-]+"),
    ),
    ("error", "prod session trace", re.compile(r"prod_session/(?!<example-session>)[^\s,`'\"]+")),
    (
        "error",
        "qq openid value",
        re.compile(r"(openid|user_openid)\s*[=:]\s*[A-Fa-f0-9]{16,}", re.I),
    ),
    (
        "error",
        "real tunnel url",
        re.compile(
            r"https://(?!example-tunnel\.)(?!xxx\.)[A-Za-z0-9-]+\.(trycloudflare\.com|ngrok-free\.app)",
            re.I,
        ),
    ),
    (
        "error",
        "credential-looking assignment",
        re.compile(
            r"\b[A-Z0-9_]*(?:API_KEY|ACCESS_KEY|SECRET_KEY|CLIENT_SECRET|SECRET|ACCESS_TOKEN|APP_ID|APPID)[A-Z0-9_]*"
            r"\s*[:=]\s*[\"']"
            r"(?!(?:your-|example|fake|test|placeholder|speech-token|speech-app-id|AKLT-test|<|xxx|xxxx|0123456789))"
            r"[A-Za-z0-9_./+=-]{12,}[\"']",
            re.I,
        ),
    ),
    (
        "error",
        "volc access key",
        re.compile(r"\bAKLT(?![-_ ]?(test|fake|example))[-A-Za-z0-9]{8,}", re.I),
    ),
    ("error", "openai key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("error", "tavily key", re.compile(r"\btvly-[A-Za-z0-9]{20,}\b")),
]

URL_PATTERN = re.compile(r"https?://[^\s)\"'<>`]+")
ALLOWED_URL_HOSTS = (
    "127.0.0.1",
    "localhost",
    "example.com",
    "test.example.com",
    "a.example",
    "b.example",
    "github.com",
    "raw.githubusercontent.com",
    "pypi.org",
    "files.pythonhosted.org",
    "astral.sh",
    "rustup.rs",
    "platform.deepseek.com",
    "app.tavily.com",
    "console.volcengine.com",
    "rtc.volcengineapi.com",
    "unpkg.com",
    "q.qq.com",
    "example-tunnel.trycloudflare.com",
    "*.trycloudflare.com",
)


def rel(path: Path) -> str:
    return path.as_posix()


def is_denied(path: str) -> bool:
    if path == ".env.example":
        return False
    return any(fnmatch.fnmatch(path, pattern) for pattern in DENY_PATTERNS)


def is_allowed(path: str) -> bool:
    if path in EXACT_ROOT_FILES or path in EXACT_FRONTEND_FILES:
        return True
    if path in {"pyproject.toml", ".env.example", "scripts/README.md"}:
        return True
    if path in {"memory_eval/README.md", "memory_eval/pyproject.toml"}:
        return True
    if path in DOC_EXACT_FILES:
        return True
    if path.startswith("docs/decisions/") and path.endswith("/README.md"):
        return True
    if path.startswith("docs/requirements/") and path.endswith(DOC_SUFFIXES):
        return True
    if path.startswith(MEMORY_EVAL_PREFIXES):
        return True
    if path.startswith("scripts/"):
        parts = path.split("/")
        return len(parts) >= 3 and parts[1] in SCRIPT_DIR_ALLOWLIST
    return path.startswith(ALLOW_PREFIXES)


def git_ls_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    paths = [p for p in result.stdout.decode("utf-8").split("\0") if p]
    for path in (ROOT / "scripts" / "showcase-snapshot").glob("*"):
        if path.is_file():
            rel_path = path.relative_to(ROOT).as_posix()
            if rel_path not in paths:
                paths.append(rel_path)
    return paths


def prepare_output(output: Path, replace: bool) -> None:
    if output.exists():
        if not replace:
            raise SystemExit(f"output exists: {output}. Pass --replace to regenerate it.")
        if not (output / SENTINEL).exists():
            raise SystemExit(
                f"refusing to replace non-snapshot directory without {SENTINEL}: {output}"
            )
        shutil.rmtree(output)
    output.mkdir(parents=True)
    (output / SENTINEL).write_text("generated by scripts/showcase-snapshot\n", encoding="utf-8")


def public_readme() -> str:
    return """# agent-friend showcase snapshot

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
"""


def public_scripts_readme() -> str:
    return """# scripts/

Project operations are wrapped as scripts so contributors do not need to remember long
`uv`, `pytest`, or frontend commands.

| Script | Purpose | mac / linux | windows |
| --- | --- | --- | --- |
| `setup/` | Initialize the Python workspace, create `.env`, and check optional frontend tools | `./scripts/setup/run.sh` | `.\\scripts\\setup\\run.ps1` |
| `cli/` | Start the CLI debug UI | `./scripts/cli/run.sh` | `.\\scripts\\cli\\run.ps1` |
| `bridge/` | Start the HTTP/SSE bridge | `./scripts/bridge/run.sh` | `.\\scripts\\bridge\\run.ps1` |
| `dev/` | Start bridge plus frontend desktop/web development flow | `./scripts/dev/run.sh [--web]` | `.\\scripts\\dev\\run.ps1 [--web]` |
| `voice/` | Start the voice bridge control plane | `./scripts/voice/run.sh` | `.\\scripts\\voice\\run.ps1` |
| `test/` | Run pytest | `./scripts/test/run.sh` | `.\\scripts\\test\\run.ps1` |
| `lint/` | Run backend lint checks | `./scripts/lint/run.sh` | `.\\scripts\\lint\\run.ps1` |
| `typecheck/` | Run mypy | `./scripts/typecheck/run.sh` | `.\\scripts\\typecheck\\run.ps1` |
| `check/` | Run the combined local quality gate | `./scripts/check/run.sh` | `.\\scripts\\check\\run.ps1` |
| `frontend/*` | Install, lint, test, build, or run frontend tasks | `./scripts/frontend/*.sh` | `.\\scripts\\frontend\\*.ps1` |
| `im-smoke/` | Run the fake-LLM IM smoke test | `./scripts/im-smoke/run.sh` | `.\\scripts\\im-smoke\\run.ps1` |
| `showcase-snapshot/` | Regenerate this sanitized public snapshot from the private source repo | `./scripts/showcase-snapshot/run.sh` | `.\\scripts\\showcase-snapshot\\run.ps1` |

Scripts that intentionally trigger real LLM or vendor smoke calls are omitted from the public
snapshot command index.
"""


def sanitize_text(path: str, text: str) -> str:
    if path == "README.md":
        return public_readme()
    if path == "scripts/README.md":
        return public_scripts_readme()
    if path == "pyproject.toml":
        text = text.replace('    "experiments/agent-contract-eval-spike",\n', "")
    if path == "uv.lock":
        text = sanitize_uv_lock(text)
    if path == ".env.example":
        text = sanitize_env_example(text)

    replacements = DOC_REPLACEMENTS if is_public_doc_path(path) else SOURCE_SAFE_REPLACEMENTS
    for pattern, replacement in replacements:
        text = pattern.sub(replacement, text)
    return text


def sanitize_uv_lock(text: str) -> str:
    text = text.replace('    "agent-contract-eval-spike",\n', "")
    return re.sub(
        r'\n\[\[package\]\]\nname = "agent-contract-eval-spike"\n.*?(?=\n\[\[package\]\])',
        "\n",
        text,
        flags=re.S,
    )


def sanitize_env_example(text: str) -> str:
    public_empty_keys = {
        "DEEPSEEK_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "TAVILY_API_KEY",
        "AGENT_API_TOKEN",
        "VOLC_ACCESS_KEY",
        "VOLC_SECRET_KEY",
        "VOLC_RTC_APP_ID",
        "VOLC_RTC_APP_KEY",
        "VOLC_ARK_API_KEY",
        "VOLC_ARK_ENDPOINT_ID",
        "VOLC_SPEECH_APP_ID",
        "VOLC_SPEECH_ACCESS_TOKEN",
        "VOICE_BRIDGE_PUBLIC_URL",
    }
    lines: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^([A-Z0-9_]+)=(.*)$", line)
        if match and match.group(1) in public_empty_keys:
            lines.append(f"{match.group(1)}=")
        else:
            lines.append(line)
    text = "\n".join(lines) + "\n"

    public_defaults = {
        "AGENT_FRIEND_DATA_DIR": ".agent-friend-data",
        "AGENT_BRIDGE_IM_ENABLED": "false",
    }
    for key, value in public_defaults.items():
        if re.search(rf"^{re.escape(key)}=", text, flags=re.M):
            text = re.sub(rf"^{re.escape(key)}=.*$", f"{key}={value}", text, flags=re.M)
        else:
            text += f"{key}={value}\n"
    return text


def is_public_doc_path(path: str) -> bool:
    return path.endswith((".md", ".mdc")) or path in {"AGENTS.md", "CLAUDE.md", ".env.example"}


def should_treat_as_text(path: Path) -> bool:
    if path.suffix in TEXT_SUFFIXES:
        return True
    return path.name in {
        ".env.example",
        ".gitignore",
        ".npmrc",
        ".prettierrc",
        ".stylelintrc",
        ".eslintrc",
    }


def copy_one(src_rel: str, output: Path) -> None:
    src = ROOT / src_rel
    dst = output / src_rel
    dst.parent.mkdir(parents=True, exist_ok=True)

    if src.is_symlink():
        target = os.readlink(src)
        os.symlink(target, dst)
        return

    if should_treat_as_text(src):
        try:
            text = src.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            shutil.copy2(src, dst)
            return
        dst.write_text(sanitize_text(src_rel, text), encoding="utf-8")
        shutil.copystat(src, dst, follow_symlinks=False)
        return

    shutil.copy2(src, dst)


def write_generated_files(output: Path) -> None:
    scan_dir = output / ".showcase-scan"
    scan_dir.mkdir(exist_ok=True)
    gitignore = output / ".gitignore"
    with gitignore.open("a", encoding="utf-8") as f:
        f.write("\n# showcase snapshot local artifacts\n")
        f.write(".showcase-scan/report.json\n")
        f.write(".agent-friend-data/\n")


def build_snapshot(output: Path) -> list[str]:
    copied: list[str] = []
    for path in git_ls_files():
        if is_denied(path) or not is_allowed(path):
            continue
        copy_one(path, output)
        copied.append(path)
    write_generated_files(output)
    return copied


def redacted(snippet: str) -> str:
    text = snippet.strip()
    text = re.sub(r"(=|:)\s*[A-Za-z0-9_./+=-]{12,}", r"\1 <redacted>", text)
    text = re.sub(r"sk-[A-Za-z0-9]{8,}", "sk-<redacted>", text)
    text = re.sub(r"tvly-[A-Za-z0-9]{8,}", "tvly-<redacted>", text)
    text = re.sub(r"AKLT[-A-Za-z0-9]{8,}", "AKLT-<redacted>", text)
    return text[:220]


def scan_text_file(path: Path, rel_path: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return findings

    for line_no, line in enumerate(text.splitlines(), start=1):
        for severity, category, pattern in SCAN_PATTERNS:
            if pattern.search(line):
                findings.append(Finding(severity, category, rel_path, line_no, redacted(line)))

        for match in URL_PATTERN.finditer(line):
            url = match.group(0).rstrip(".,;")
            host = re.sub(r"^https?://", "", url).split("/", 1)[0].split(":", 1)[0]
            if host not in ALLOWED_URL_HOSTS:
                findings.append(
                    Finding("warning", "url inventory", rel_path, line_no, redacted(url))
                )

    return findings


def scan_snapshot(output: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(output.rglob("*")):
        if path.is_dir():
            continue
        rel_path = path.relative_to(output).as_posix()
        if rel_path == ".showcase-scan/report.json":
            continue
        if rel_path == "scripts/showcase-snapshot/snapshot.py":
            continue
        if rel_path.endswith("experiments/voice-poc/rtc-aigc-demo/Server/scenes/Custom.json"):
            findings.append(
                Finding("error", "forbidden P0 path", rel_path, 0, "Custom.json must not ship")
            )
        if rel_path == ".claude/settings.local.json" or rel_path.startswith(".claude/worktrees/"):
            findings.append(Finding("error", "forbidden local claude state", rel_path, 0, rel_path))
        findings.extend(scan_text_file(path, rel_path))
    return findings


def write_report(output: Path, copied: list[str], findings: list[Finding]) -> None:
    created_at = datetime.now(timezone.utc).isoformat()  # noqa: UP017 - bootstrap supports Python 3.9.
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    report = {
        "created_at": created_at,
        "copied_file_count": len(copied),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "findings": [f.__dict__ for f in findings],
    }
    (output / ".showcase-scan").mkdir(exist_ok=True)
    (output / ".showcase-scan" / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Showcase Snapshot Scan Report",
        "",
        f"- Generated: `{created_at}`",
        f"- Copied files: `{len(copied)}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        "",
    ]
    if not findings:
        lines.append("No findings.")
    else:
        lines.extend(
            ["| Severity | Category | File | Line | Snippet |", "| --- | --- | --- | ---: | --- |"]
        )
        for finding in findings:
            lines.append(
                f"| {finding.severity} | {finding.category} | `{finding.path}` | "
                f"{finding.line} | `{finding.snippet.replace('|', '/')}` |"
            )
    lines.append("")
    (output / "SHOWCASE-SCAN-REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def init_git(output: Path) -> None:
    subprocess.run(["git", "init"], cwd=output, check=True)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a sanitized public showcase snapshot.")
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT, help="snapshot output directory"
    )
    parser.add_argument(
        "--replace", action="store_true", help="replace an existing generated snapshot"
    )
    parser.add_argument(
        "--init-git", action="store_true", help="run git init in the generated snapshot"
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    output = args.output.expanduser().resolve()
    prepare_output(output, args.replace)
    copied = build_snapshot(output)
    findings = scan_snapshot(output)
    write_report(output, copied, findings)
    if args.init_git:
        init_git(output)

    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    print(f"snapshot: {output}")
    print(f"copied files: {len(copied)}")
    print(f"scan errors: {len(errors)}")
    print(f"scan warnings: {len(warnings)}")
    print(f"report: {output / 'SHOWCASE-SCAN-REPORT.md'}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
