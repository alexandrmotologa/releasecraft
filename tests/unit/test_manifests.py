"""Unit tests for ManifestUpdater."""

import json
from pathlib import Path

from releasecraft.manifests.updater import ManifestUpdater


def test_update_package_json(tmp_path: Path) -> None:
    pkg = tmp_path / "package.json"
    pkg.write_text(json.dumps({"name": "test-pkg", "version": "1.0.0"}), encoding="utf-8")

    updated = ManifestUpdater.update_manifest(pkg, "1.2.0")
    assert updated is True

    data = json.loads(pkg.read_text(encoding="utf-8"))
    assert data["version"] == "1.2.0"

    # Second call with same version should return False
    assert ManifestUpdater.update_manifest(pkg, "1.2.0") is False


def test_update_pyproject_toml(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    content = '[project]\nname = "my-app"\nversion = "0.5.1"\ndescription = "App"\n'
    pyproject.write_text(content, encoding="utf-8")

    updated = ManifestUpdater.update_manifest(pyproject, "0.6.0")
    assert updated is True

    new_content = pyproject.read_text(encoding="utf-8")
    assert 'version = "0.6.0"' in new_content
    assert 'name = "my-app"' in new_content


def test_update_cargo_toml(tmp_path: Path) -> None:
    cargo = tmp_path / "Cargo.toml"
    content = '[package]\nname = "rust_app"\nversion = "0.1.0"\nedition = "2021"\n'
    cargo.write_text(content, encoding="utf-8")

    updated = ManifestUpdater.update_manifest(cargo, "0.2.0")
    assert updated is True

    new_content = cargo.read_text(encoding="utf-8")
    assert 'version = "0.2.0"' in new_content


def test_update_python_init(tmp_path: Path) -> None:
    pkg_dir = tmp_path / "src" / "my_pkg"
    pkg_dir.mkdir(parents=True)
    init_file = pkg_dir / "__init__.py"
    init_file.write_text('"""Docs."""\n\n__version__ = "1.0.0"\n', encoding="utf-8")

    updated = ManifestUpdater.update_manifest(init_file, "1.1.0")
    assert updated is True

    new_content = init_file.read_text(encoding="utf-8")
    assert '__version__ = "1.1.0"' in new_content


def test_detect_and_update_all(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.0.0"\n', encoding="utf-8")
    (tmp_path / "package.json").write_text('{"version": "1.0.0"}', encoding="utf-8")
    (tmp_path / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    (tmp_path / "composer.json").write_text(
        '{"name": "test/app", "version": "1.0.0"}', encoding="utf-8"
    )
    (tmp_path / "pubspec.yaml").write_text("name: demo\nversion: 1.0.0+1\n", encoding="utf-8")
    (tmp_path / "setup.cfg").write_text(
        "[metadata]\nname = demo\nversion = 1.0.0\n", encoding="utf-8"
    )
    (tmp_path / "version.go").write_text(
        'package main\n\nconst Version = "1.0.0"\n', encoding="utf-8"
    )

    manifests = ManifestUpdater.detect_manifests(tmp_path)
    assert len(manifests) == 7

    updated_files = ManifestUpdater.update_all(tmp_path, "1.1.0")
    assert len(updated_files) == 7

    assert (tmp_path / "VERSION").read_text(encoding="utf-8").strip() == "1.1.0"
    assert '"version": "1.1.0"' in (tmp_path / "composer.json").read_text(encoding="utf-8")
    # Verify Flutter build number preserved
    assert "version: 1.1.0+1" in (tmp_path / "pubspec.yaml").read_text(encoding="utf-8")
    assert "version = 1.1.0" in (tmp_path / "setup.cfg").read_text(encoding="utf-8")
    assert 'const Version = "1.1.0"' in (tmp_path / "version.go").read_text(encoding="utf-8")
