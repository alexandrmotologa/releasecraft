"""Detects and updates version numbers in project manifest files."""

import json
import re
from pathlib import Path

PYPROJECT_VERSION_REGEX = re.compile(
    r'^(?P<prefix>\s*version\s*=\s*["\'])(?P<ver>[^"\']+)(?P<suffix>["\'])',
    re.MULTILINE,
)

CARGO_VERSION_REGEX = re.compile(
    r'(?P<prefix>\[package\][^\[]*?\bversion\s*=\s*["\'])(?P<ver>[^"\']+)(?P<suffix>["\'])',
    re.DOTALL,
)

PYTHON_INIT_VERSION_REGEX = re.compile(
    r'^(?P<prefix>\s*__version__\s*=\s*["\'])(?P<ver>[^"\']+)(?P<suffix>["\'])',
    re.MULTILINE,
)


class ManifestUpdater:
    """Synchronizes version numbers across common language manifest files."""

    @classmethod
    def detect_manifests(cls, repo_root: Path | str) -> list[Path]:
        """Find supported manifest files in the repository."""
        root = Path(repo_root)
        manifests: list[Path] = []

        # 1. pyproject.toml
        pyproject = root / "pyproject.toml"
        if pyproject.is_file():
            content = pyproject.read_text(encoding="utf-8")
            if PYPROJECT_VERSION_REGEX.search(content):
                manifests.append(pyproject)

        # 2. package.json
        pkg_json = root / "package.json"
        if pkg_json.is_file():
            try:
                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                if "version" in data:
                    manifests.append(pkg_json)
            except Exception:
                pass

        # 3. Cargo.toml
        cargo_toml = root / "Cargo.toml"
        if cargo_toml.is_file():
            content = cargo_toml.read_text(encoding="utf-8")
            if CARGO_VERSION_REGEX.search(content):
                manifests.append(cargo_toml)

        # 4. VERSION file
        version_file = root / "VERSION"
        if version_file.is_file():
            manifests.append(version_file)

        # 5. Python package __init__.py files
        search_dirs = [root / "src", root]
        for s_dir in search_dirs:
            if s_dir.is_dir():
                for init_file in s_dir.rglob("__init__.py"):
                    if ".venv" in init_file.parts or "node_modules" in init_file.parts:
                        continue
                    try:
                        content = init_file.read_text(encoding="utf-8")
                        if PYTHON_INIT_VERSION_REGEX.search(content):
                            manifests.append(init_file)
                    except Exception:
                        pass

        # Remove duplicates while preserving order
        unique_manifests: list[Path] = []
        for m in manifests:
            resolved = m.resolve()
            if resolved not in [u.resolve() for u in unique_manifests]:
                unique_manifests.append(m)

        return unique_manifests

    @classmethod
    def update_manifest(cls, file_path: Path | str, new_version: str) -> bool:
        """Update the version in a single manifest file."""
        path = Path(file_path)
        if not path.is_file():
            return False

        clean_version = new_version.lstrip("v").lstrip("V")
        original_content = path.read_text(encoding="utf-8")
        name = path.name

        if name == "package.json":
            try:
                data = json.loads(original_content)
                if data.get("version") == clean_version:
                    return False
                data["version"] = clean_version
                new_content = json.dumps(data, indent=2) + "\n"
                path.write_text(new_content, encoding="utf-8")
                return True
            except Exception:
                return False

        elif name == "VERSION":
            if original_content.strip() == clean_version:
                return False
            path.write_text(f"{clean_version}\n", encoding="utf-8")
            return True

        elif name == "pyproject.toml":
            match = PYPROJECT_VERSION_REGEX.search(original_content)
            if match:
                if match.group("ver") == clean_version:
                    return False
                new_content = PYPROJECT_VERSION_REGEX.sub(
                    rf"\g<prefix>{clean_version}\g<suffix>",
                    original_content,
                    count=1,
                )
                path.write_text(new_content, encoding="utf-8")
                return True

        elif name == "Cargo.toml":
            match = CARGO_VERSION_REGEX.search(original_content)
            if match:
                if match.group("ver") == clean_version:
                    return False
                new_content = CARGO_VERSION_REGEX.sub(
                    rf"\g<prefix>{clean_version}\g<suffix>",
                    original_content,
                    count=1,
                )
                path.write_text(new_content, encoding="utf-8")
                return True

        elif name == "__init__.py":
            match = PYTHON_INIT_VERSION_REGEX.search(original_content)
            if match:
                if match.group("ver") == clean_version:
                    return False
                new_content = PYTHON_INIT_VERSION_REGEX.sub(
                    rf"\g<prefix>{clean_version}\g<suffix>",
                    original_content,
                    count=1,
                )
                path.write_text(new_content, encoding="utf-8")
                return True

        return False

    @classmethod
    def update_all(cls, repo_root: Path | str, new_version: str) -> list[Path]:
        """Detect and update all manifest files in repository.

        Returns:
            List of successfully modified manifest file paths.
        """
        manifests = cls.detect_manifests(repo_root)
        updated: list[Path] = []
        for m in manifests:
            if cls.update_manifest(m, new_version):
                updated.append(m)
        return updated
