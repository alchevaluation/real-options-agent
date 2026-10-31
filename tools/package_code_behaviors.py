"""Package only reviewed project files; never recurse through the workspace."""

from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


FILES = (
    ".gitignore",
    "README.md",
    "pyproject.toml",
    "src/real_options_agent/__init__.py",
    "src/real_options_agent/__main__.py",
    "src/real_options_agent/dcf.py",
    "src/real_options_agent/scenarios.py",
    "tests/test_dcf.py",
    "tests/test_scenarios.py",
    "tools/package_code_behaviors.py",
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    archive = root.parent / "real-options-agent-code-behaviors.zip"
    sources = []
    for name in FILES:
        source = root / name
        if source.is_symlink() or not source.resolve().is_relative_to(root):
            raise ValueError(f"Package source must stay inside the project: {name}")
        sources.append((name, source.read_bytes()))
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as output:
        for name, content in sources:
            output.writestr(f"real-options-agent/{name}", content)
    with ZipFile(archive) as result:
        expected = {f"real-options-agent/{name}" for name in FILES}
        if set(result.namelist()) != expected or result.testzip() is not None:
            raise RuntimeError("Package verification failed")
    print(f"Created: {archive}")
    print(f"Files: {len(FILES)}")
    print(f"SHA256: {sha256(archive.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
