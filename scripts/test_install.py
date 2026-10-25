from pathlib import Path
import tempfile
import unittest

import install


class InstallTests(unittest.TestCase):
    def test_installs_only_allowlisted_skill_files(self):
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            target = install.install(source, Path(tmp) / "skills")
            actual = {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()}
            self.assertEqual(actual, set(install.FILES))
            for name in install.FILES:
                self.assertEqual((target / name).read_bytes(), (source / name).read_bytes())

    def test_existing_installation_is_preserved(self):
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "antigen-claude"
            target.mkdir()
            marker = target / "SKILL.md"
            marker.write_text("user changes", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                install.install(source, Path(tmp))
            self.assertEqual(marker.read_text(encoding="utf-8"), "user changes")


if __name__ == "__main__":
    unittest.main()
