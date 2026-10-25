---
name: antigen-claude
description: Route antigen (抗原) work to local Claude Code, including antigen code, feature extraction, model branches/architecture, datasets, preprocessing, and antigen-antibody interfaces. Applies to follow-ups whose established context is antigen work even when the word is omitted.
---

# Antigen Claude routing

Use local Claude Code as the primary domain executor. Codex coordinates scope, passes context, reviews changes, runs verification, and reports evidence. Do not silently implement domain work in Codex when Claude is unavailable.

## Shared project context and specialist role

Claude is the antigen specialist inside the overall Codex-led project. Launch it with the same active project folder as Codex (`--workspace`), not a nested antigen folder, global skill directory, or artifact folder. If Codex changes the active project folder, update the handoff accordingly. Read scope may include the project structure and integration dependencies; write scope stays limited to the assigned antigen task and explicitly identified dependencies. Shared directory access does not transmit the Codex conversation.

Maintain a task-specific UTF-8 context file under the active project's `.omx/artifacts/antigen-context/`. Give each Codex task its own file so parallel chats do not overwrite context. Before every invocation, refresh it with:

- The overall user objective, current request, project root, and how the antigen assignment contributes to the full workflow.
- Progress from task start to now: completed work, relevant decisions and reasons, rejected approaches, user corrections, current phase, open questions, and next steps. Distinguish confirmed facts from assumptions.
- A project map and exact entrypoints to read: applicable AGENTS.md/CLAUDE.md, relevant README or mission documents, antigen code/data/configuration, upstream/downstream interfaces, and tests. Include applicable instruction text or direct Claude to read the exact files before acting.
- Existing user/other-agent changes, assigned write scope, data and environment constraints, acceptance criteria, recent test outputs, and prior Claude feedback with Codex's disposition of it.

Pass this context with `--context-file` on every call, including follow-ups and model switches. The helper starts fresh Claude calls with no session persistence; continuity comes from this updated context plus shared project files, not automatic chat synchronization. Keep relevant history from the beginning without dumping unrelated chats, credentials, or entire datasets.

Before domain work, Claude must read the supplied project entrypoints and relevant files, then state its understanding of the overall goal, current phase, specialist assignment, and missing context. Acknowledge uncertainty rather than inventing missing history. If a material dependency is unclear, return a targeted question to Codex. Codex resolves what it can from the project and user history, updates the context, and re-dispatches. Reading everything byte-for-byte is unnecessary; understanding the full task and its integration boundaries is required.

After each call, incorporate Claude's findings, changed files, tests, blockers, and unresolved questions into the context before the next handoff. Codex retains ownership of overall architecture/integration and presents Claude's feedback to the user with independently verified results distinguished from specialist judgments.

## Scope and models

- Route antigen analysis, coding, features/embeddings, model architecture or experimental branches, data processing, and antigen-antibody interfaces. Infer scope from the task and ongoing context, not merely the workspace name. Unrelated work stays with Codex. Explicit user overrides take precedence.
- Use `claude-opus-5` for architecture, new model branches, complex reasoning/debugging, and cross-module design.
- Use `claude-sonnet-5-5` for routine feature extraction, preprocessing, dataset tasks, and localized implementation. Honor explicit choice between these two models.
- Pin the full model ID; never use changing aliases or silently substitute another version. Model unavailability or authentication failure is a blocker to report, not permission to downgrade.

## Handoff

1. Prepare or refresh the shared project context above. Write a separate UTF-8 prompt file with the current specialist assignment, exact workspace, read/write scope, and acceptance criteria. The helper requires both files. Exclude unrelated secrets/data.
2. Tell Claude it owns the scoped domain work, must preserve existing changes, and must not invoke this router or delegate back to Codex. Include applicable instructions explicitly: Claude does not automatically read Codex's AGENTS.md. Request changed files, verification performed, and limitations. Analysis tasks remain read-only.
3. Invoke the bundled helper from the actual target project. Artifacts go in a unique directory under its `.omx/artifacts/`:

   Resolve `SKILL_DIR` to the directory containing this loaded SKILL.md, and `PROJECT_DIR` to Codex's active project root. Use absolute paths for the context and assignment files. Keep the current directory at `PROJECT_DIR`, not `SKILL_DIR`. For example in a POSIX shell (on Windows, use the equivalent quoted PowerShell paths):

   ```sh
   python "$SKILL_DIR/scripts/route_claude.py" --workspace "$PROJECT_DIR" --context-file "$PROJECT_DIR/.omx/artifacts/antigen-context/task-context.md" --prompt-file "$PROJECT_DIR/task.txt" --model claude-sonnet-5-5 --mode implement
   ```

   Use `--mode read` for analysis/review. `--dry-run` validates arguments without contacting Claude or creating artifacts. Increase `--timeout` for deliberately long tasks. After timeout, inspect partial changes and process state before retrying; do not run overlapping retries.
4. Inspect `result.json`, `stderr.txt`, and actual changes. Check `is_error`, permission denials, and `modelUsage`; exit zero alone is insufficient. The helper rejects unexpected/missing model evidence. If Claude is absent, unauthenticated, unavailable, or denied required actions, report the specific blocker and preserve artifacts; do not claim completion.
5. Review changes and run relevant checks. The helper permits file edits in implementation mode but grants no shell tools: Codex runs requested verification/data commands within authorized scope. Hand further domain changes back to Claude. Report actual model, changed files, verification, and unresolved limitations.

The helper uses normal permissions, never bypass flags. Routing preserves existing authorization; it does not authorize deployment, messages, unrelated edits, or destructive operations. It does not change the model hosting this Codex conversation. Discovery depends on the host loading this skill; a new chat may be needed after installation. Explicit invocation: `$antigen-claude`.

The helper limits the available tool types; it is not a filesystem sandbox. Respect the read/write scope stated in the handoff. Prompt, context and raw feedback artifacts may contain project information; keep them local unless the user explicitly authorizes sharing them. `.omx/` is an artifact-directory convention only; the OMX runtime is not required. CoreWeave is optional and uses a separate deployment-specific skill/configuration.

Model IDs checked against [Claude Code model configuration](https://support.claude.com/en/articles/11940350-claude-code-model-configuration) on 2026-10-24. Account access must still be tested locally.
