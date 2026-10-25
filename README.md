# Antigen Claude Skill

A Codex skill that delegates antigen work to **local Claude Code**, while Codex keeps ownership of the overall project, integration, and verification.

## What it does

- Routes antigen code, feature extraction, model branches, data processing, and Ab–Ag interfaces to Claude.
- Pins **Claude Opus 5** (`claude-opus-5`) for complex design and **Sonnet 5.5** (`claude-sonnet-5-5`) for routine implementation; never silently substitutes a model.
- Requires a refreshed project context file on **every call**, including follow-ups and model switches. Claude runs in the active project folder and reads relevant project entrypoints.
- Records the exact prompt, context snapshot, raw Claude response, errors, and actual model evidence locally.
- Allows read tools in review mode and file-edit tools in implementation mode. Codex runs shell commands, tests, and cluster jobs.

This routes work to a separate process; it does not change the model hosting Codex or automatically synchronize conversation histories. The helper is not a filesystem sandbox. Automatic selection depends on the host loading the skill and remains subject to higher-priority instructions.

## Requirements

- Codex with local skill support.
- Python **3.10+**, available as `python` (or substitute `python3`). The helper and installer use only the standard library; no `pip install` is needed.
- [Claude Code](https://code.claude.com/docs/en/setup) on `PATH`, authenticated with access to the pinned model. Live calls were tested with CLI **2.1.280**; compatible versions must expose the flags used in `scripts/route_claude.py`.
- Git for cloning this repository.

Check the local CLI before running a live task:

```sh
claude --version
claude auth login
claude auth status
```

Claude usage is billed or metered by your Claude account. Offline tests and `--dry-run` make no model requests. Model names being documented does not guarantee your account has access.

## Install — Windows, macOS, Linux

Run these commands in PowerShell or a terminal:

```sh
git clone https://github.com/Mudman14/antigen-claude-skill.git
cd antigen-claude-skill
python scripts/install.py
```

The installer copies only the four skill files into `$CODEX_HOME/skills/antigen-claude`, or `~/.codex/skills/antigen-claude` when `CODEX_HOME` is unset. If your Codex host uses a different skill directory, pass it explicitly:

```sh
python scripts/install.py --skills-dir /path/to/your/skills
```

It **refuses to overwrite an existing installation**. To update, compare the new version with your existing skill, preserve local edits, and copy the intended files manually. Installing does not change global model settings or install Claude Code.

Start a **new Codex chat** in your project folder. Explicitly invoke:

```text
$antigen-claude
Read the project context and extract antigen PLM features. Keep Codex responsible for integration and verification.
```

The installed `agents/openai.yaml` also allows implicit invocation for matching antigen tasks. Explicit invocation is the reliable way to check discovery after installation.

## Offline verification

From this repository:

```sh
python -m unittest discover -s scripts -p "test_*.py" -v
python -m compileall -q scripts
```

Tests cover routing, model substitution rejection, context transmission, artifact preservation, timeouts, dry runs, and installation without overwriting existing files. GitHub Actions runs the same checks on Windows, macOS, and Linux with Python 3.10 and 3.13. CI never uses Claude credentials or makes paid requests.

## Live smoke test

The commands below run from the cloned repository. `examples/context.md` and `examples/assignment.txt` contain synthetic context only. The project folder is deliberately separate from the skill folder.

### PowerShell

```powershell
$project = Join-Path $env:TEMP ("antigen-router-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $project | Out-Null
python scripts/route_claude.py --workspace $project --context-file examples/context.md --prompt-file examples/assignment.txt --model claude-sonnet-5-5 --mode read --dry-run
# Remove --dry-run to make one live Claude request:
python scripts/route_claude.py --workspace $project --context-file examples/context.md --prompt-file examples/assignment.txt --model claude-sonnet-5-5 --mode read
```

### macOS / Linux

```sh
project="$(mktemp -d)"
python scripts/route_claude.py --workspace "$project" --context-file examples/context.md --prompt-file examples/assignment.txt --model claude-sonnet-5-5 --mode read --dry-run
# Remove --dry-run to make one live Claude request:
python scripts/route_claude.py --workspace "$project" --context-file examples/context.md --prompt-file examples/assignment.txt --model claude-sonnet-5-5 --mode read
```

For Opus, change only `--model` to `claude-opus-5`. A successful call reports `"status": "completed"`. Inspect the returned artifact folder: `result.json` must contain the requested model in `modelUsage`, no errors/permission denials, and `ROUTER_OK` in its response. A dry run verifies invocation construction only; it does not prove authentication or inference.

## Real project workflow

Codex follows [SKILL.md](SKILL.md). Before each call, it refreshes a task-specific context file under the active project's `.omx/artifacts/antigen-context/` with:

1. The full task goal, history of relevant decisions and user corrections, progress, and current assignment.
2. Exact project entrypoints and interfaces to read, applicable instructions, existing edits, and write boundaries.
3. Acceptance criteria, recent test evidence, prior Claude feedback, and unresolved questions.

Use a separate context file per Codex task. Claude first reads the relevant project files and reports its understanding; after the call, Codex reviews changes, runs checks, returns feedback to the user, and updates the context for the next handoff. `--mode implement` permits `Read,Glob,Grep,Edit,Write`; it does not grant shell tools. If a command is needed, Codex runs it within the user's authorized scope.

The `.omx/` name is just an artifact convention: **OMX is not a dependency**. CoreWeave access is optional and separately configured. This repository contains no cluster configuration, SSH keys, storage credentials, biological datasets, model weights, or private project logs.

## Feedback and failure handling

Each real call creates a unique artifact folder containing:

| File | Purpose |
|---|---|
| `prompt.txt` | Exact context and assignment sent to Claude |
| `context.md` | Project context snapshot |
| `result.json` | Raw response, feedback, and model usage |
| `stderr.txt` | CLI diagnostic output |
| `handoff.json` | Invocation, workspace, status, and error |

The helper fails if the CLI exits unsuccessfully, reports an error or denied tools, returns no result, or supplies missing/unexpected model evidence. Authentication or unavailable-model errors are reported without model downgrade. After a timeout, inspect partial changes and remaining child processes before retrying. There is no automatic retry or overlapping session launch.

Prompts and raw artifacts can contain project information. Keep them local; review them before sharing. The repository `.gitignore` excludes `.omx/`, but **your working project needs its own ignore rules**. Only pass context/data your project permits you to send to Claude.

## Validation scope

The originating installation completed live calls with both pinned models, a project-file context-reading test, and a three-complex/nine-chain ESM-2 feature-extraction smoke test on a Slurm GPU cluster. Domain code was generated by Claude and independently checked/executed by Codex. Those are historical integration checks, not a guarantee of model availability or biological/downstream accuracy. Raw project data, identifiers, infrastructure details, and outputs are not distributed here.

See [Claude's model configuration documentation](https://support.claude.com/en/articles/11940350-claude-code-model-configuration) for model IDs. The routing policy intentionally pins the requested versions; changing versions is an explicit user decision.

## License

[MIT](LICENSE).
