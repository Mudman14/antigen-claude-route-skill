import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import route_claude as router


class RoutingTests(unittest.TestCase):
    def invoke(self, outcome=None, extra=()):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prompt = root / "task.txt"
            prompt.write_text("提取 antigen 特征；保留已有修改", encoding="utf-8")
            context = root / "context.md"
            context.write_text("Overall goal: antigen integration. Prior decision: preserve residue IDs.", encoding="utf-8")
            with patch.object(router.shutil, "which", return_value="claude.exe"), \
                 patch.object(router.subprocess, "run") as run, \
                 contextlib.redirect_stdout(io.StringIO()) as output:
                if isinstance(outcome, Exception):
                    run.side_effect = outcome
                else:
                    run.return_value = outcome
                code = router.main(["--workspace", directory, "--prompt-file", str(prompt),
                                    "--context-file", str(context),
                                    "--model", router.MODELS[0], *extra])
            payload = json.loads(output.getvalue())
            files = {}
            if "artifacts" in payload:
                files = {p.name: p.read_text(encoding="utf-8")
                         for p in Path(payload["artifacts"]).iterdir()}
            return code, payload, files, run

    def test_success_preserves_prompt_and_workspace(self):
        result = {"result": "done", "modelUsage": {router.MODELS[0]: {}}, "is_error": False}
        code, payload, files, run = self.invoke(subprocess.CompletedProcess([], 0, json.dumps(result), ""))
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "completed")
        self.assertIn("提取", run.call_args.kwargs["input"])
        self.assertIn("Prior decision: preserve residue IDs", run.call_args.kwargs["input"])
        self.assertIn(files["context.md"], run.call_args.kwargs["input"])
        self.assertEqual(files["prompt.txt"], run.call_args.kwargs["input"])
        self.assertEqual(json.loads(files["handoff.json"])["cwd"], str(run.call_args.kwargs["cwd"]))
        self.assertFalse(run.call_args.kwargs.get("shell", False))

    def test_error_exit_preserves_evidence(self):
        code, payload, files, _ = self.invoke(subprocess.CompletedProcess([], 1, "not logged in", "auth failure"))
        self.assertEqual(code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(files["stderr.txt"], "auth failure")

    def test_timeout_is_not_success(self):
        code, payload, files, _ = self.invoke(subprocess.TimeoutExpired("claude", 1, output=b"partial"))
        self.assertEqual(code, 1)
        self.assertEqual(payload["status"], "timeout")
        self.assertEqual(files["result.json"], "partial")

    def test_dry_run_does_not_launch_or_write_artifacts(self):
        code, _, files, run = self.invoke(extra=("--dry-run",))
        self.assertEqual(code, 0)
        self.assertEqual(files, {})
        run.assert_not_called()

    def test_model_and_permission_failures(self):
        for result in ({"is_error": True}, {"result": "done"},
                       {"result": "done", "modelUsage": {"claude-opus-5-5": {}}},
                       {"result": "done", "modelUsage": {router.MODELS[0]: {}}, "permission_denials": ["Edit"]}):
            with self.subTest(result=result), self.assertRaises(ValueError):
                router.validate_result(result, router.MODELS[0])

    def test_models_are_pinned_and_tools_match_mode(self):
        for model in router.MODELS:
            read = router.command("claude", model, "read")
            write = router.command("claude", model, "implement")
            self.assertEqual(read[read.index("--model") + 1], model)
            self.assertNotIn("Edit", read[read.index("--tools") + 1])
            self.assertIn("Edit", write[write.index("--tools") + 1])
            self.assertNotIn("Bash", write[write.index("--tools") + 1])
            self.assertNotIn("--dangerously-skip-permissions", write)


if __name__ == "__main__":
    unittest.main()
