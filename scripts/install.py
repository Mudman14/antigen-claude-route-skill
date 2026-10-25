"""Install this skill without copying Git history, examples, or local artifacts."""
import argparse
import os
from pathlib import Path
import shutil

FILES = ("SKILL.md", "agents/openai.yaml", "scripts/route_claude.py",
         "scripts/test_route_claude.py")


def install(source, skills_dir):
    source, skills_dir = Path(source), Path(skills_dir).expanduser()
    for relative in FILES:
        if not (source / relative).is_file():
            raise FileNotFoundError(source / relative)
    target = skills_dir / "antigen-claude"
    # Never merge with or overwrite a user's existing installation.
    target.mkdir(parents=True, exist_ok=False)
    for relative in FILES:
        dest = target / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, dest)
    return target.resolve()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    default = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "skills"
    parser.add_argument("--skills-dir", type=Path, default=default)
    args = parser.parse_args(argv)
    try:
        target = install(Path(__file__).resolve().parents[1], args.skills_dir)
    except (FileExistsError, FileNotFoundError) as exc:
        parser.error(str(exc) + "; no existing installation was overwritten")
    print("Installed: " + str(target))
    print("Start a new Codex chat and invoke $antigen-claude.")


if __name__ == "__main__":
    main()
