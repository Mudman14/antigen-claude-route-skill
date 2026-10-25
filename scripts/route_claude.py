"""Bounded local Claude handoff with pinned models and auditable results."""
import argparse
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from uuid import uuid4

MODELS = ("claude-opus-5", "claude-sonnet-5-5")


def command(executable, model, mode):
    toolset = "Read,Glob,Grep" + (",Edit,Write" if mode == "implement" else "")
    return [executable, "--print", "--model", model, "--output-format", "json",
            "--no-session-persistence", "--permission-mode",
            "acceptEdits" if mode == "implement" else "dontAsk",
            "--permission-prompts", "none", "--tools", toolset,
            "--allowedTools", toolset]


def validate_result(result, model):
    if not isinstance(result, dict) or result.get("is_error"):
        raise ValueError("Claude reported an error or invalid result")
    if result.get("permission_denials"):
        raise ValueError("Claude reported permission denials; inspect partial work")
    usage = result.get("modelUsage", {})
    if not usage or any(not re.fullmatch(re.escape(model) + r"(?:-\d{8})?", key) for key in usage):
        raise ValueError("Missing or unexpected modelUsage: " + str(list(usage)))
    if not result.get("result"):
        raise ValueError("Claude returned no result text")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--context-file", required=True, type=Path)
    parser.add_argument("--model", required=True, choices=MODELS)
    parser.add_argument("--mode", choices=("read", "implement"), default="read")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    workspace = args.workspace.resolve(strict=True)
    if not workspace.is_dir() or args.timeout <= 0:
        parser.error("workspace must be a directory and timeout must be positive")
    assignment = args.prompt_file.read_text(encoding="utf-8-sig")
    context = args.context_file.read_text(encoding="utf-8-sig")
    if not assignment.strip() or not context.strip():
        parser.error("prompt and context files must not be empty")
    prompt = (
        "You are the antigen specialist in a Codex-led project. The text below "
        "contains project context and your current assignment. Read the relevant "
        "project entrypoints before acting. Report your understanding of the overall "
        "goal, current phase, assignment, and missing context. Do not invoke the "
        "router or delegate back to Codex. Preserve existing changes and respect "
        "the assignment's write scope.\n\n"
        f"Active project folder: {workspace}\n\n"
        f"## Project context\n{context}\n\n## Current assignment\n{assignment}"
    )
    executable = shutil.which("claude")
    if not executable:
        parser.error("Claude Code executable is not installed/on PATH")
    cmd = command(executable, args.model, args.mode)
    if args.dry_run:
        print(json.dumps({"command": cmd, "cwd": str(workspace),
                          "prompt_chars": len(prompt)}, ensure_ascii=False))
        return 0
    folder = workspace / ".omx" / "artifacts" / (
        "antigen-claude-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-" + uuid4().hex[:8])
    folder.mkdir(parents=True)
    (folder / "prompt.txt").write_text(prompt, encoding="utf-8")
    (folder / "context.md").write_text(context, encoding="utf-8")
    meta = {"command": cmd, "cwd": str(workspace), "model": args.model,
            "mode": args.mode, "status": "started"}
    stdout, stderr = "", ""
    code = 1
    try:
        run = subprocess.run(cmd, input=prompt, cwd=workspace, encoding="utf-8",
                             errors="replace", capture_output=True, timeout=args.timeout)
        stdout, stderr = run.stdout, run.stderr
        meta["exit_code"] = run.returncode
        if run.returncode:
            try:
                detail = json.loads(stdout).get("result", "")
            except (ValueError, AttributeError):
                detail = ""
            raise RuntimeError("Claude exited with code " + str(run.returncode)
                               + (": " + str(detail) if detail else ""))
        validate_result(json.loads(stdout), args.model)
        meta["status"] = "completed"
        code = 0
    except subprocess.TimeoutExpired as exc:
        def decode(value):
            return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""
        stdout, stderr = decode(exc.stdout), decode(exc.stderr)
        meta.update(status="timeout", error="Timed out; inspect partial changes before retrying")
    except (OSError, ValueError, RuntimeError) as exc:
        meta.update(status="failed", error=str(exc))
    finally:
        (folder / "result.json").write_text(stdout, encoding="utf-8")
        (folder / "stderr.txt").write_text(stderr, encoding="utf-8")
        (folder / "handoff.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps({"status": meta["status"], "artifacts": str(folder),
                      "error": meta.get("error")}, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
