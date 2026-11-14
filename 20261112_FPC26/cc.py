"""Isolated headless Claude Code calls shared by the FPC26 scripts.

Each call runs in an empty working directory with its own CLAUDE_CONFIG_DIR, so that no CLAUDE.md, memory, MCP
server or user setting reaches the model. (Run from inside this repository, the repository's CLAUDE.md asks for
Japanese, which skewed the answers towards Japanese and Japan in a test run.)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time

LIMIT_MARK = "hit your"  # "You've hit your 5-hour limit"
_SCRUB = re.compile(r"^(CLAUDE|ANTHROPIC)", re.I)
MODELS = {"opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5", "haiku": "claude-haiku-5-5",
          "fable": "claude-fable-5-1"}


def clean_env(cfg):
    env = {k: v for k, v in os.environ.items() if not _SCRUB.match(k)}
    env.update({"CLAUDE_CONFIG_DIR": cfg, "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1", "DISABLE_AUTOUPDATER": "1",
                "PYTHONIOENCODING": "utf-8"})
    # keep the session's own credentials reachable: CLAUDE_CONFIG_DIR only moves settings and history
    for k in ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL"):
        if k in os.environ:
            env[k] = os.environ[k]
    return env


def call(prompt, model, system_prompt=None, schema=None, timeout=300, attempts=4):
    """One tool-less `claude -p` call. Returns (data, error); data is the parsed --output-format json result."""
    last = None
    for attempt in range(1, attempts + 1):
        tmp = tempfile.mkdtemp(prefix="fpc26_")
        cwd, cfg = os.path.join(tmp, "cwd"), os.path.join(tmp, "cfg")
        os.makedirs(cwd)
        os.makedirs(cfg)
        cmd = ["claude", "-p", "--model", MODELS.get(model, model), "--tools", "", "--strict-mcp-config",
               "--no-session-persistence", "--output-format", "json"]
        if system_prompt is not None:
            cmd += ["--system-prompt", system_prompt]
        if schema is not None:
            cmd += ["--json-schema", json.dumps(schema)]
        try:
            r = subprocess.run(cmd, cwd=cwd, env=clean_env(cfg), input=prompt, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=timeout)
            data = json.loads(r.stdout)
            if data.get("is_error"):
                last = f"is_error: {str(data.get('result'))[:300]}"
                if LIMIT_MARK in last:  # retrying cannot help until the usage limit resets
                    return None, last
            elif schema is not None and not data.get("structured_output"):
                last = f"no structured_output: {r.stdout[-300:]}"
            else:
                return data, None
        except subprocess.TimeoutExpired:
            last = "timeout"
        except json.JSONDecodeError:
            last = f"bad json: {r.stdout[-200:]} {r.stderr[-200:]}"
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        time.sleep(3 * attempt)
    return None, last
