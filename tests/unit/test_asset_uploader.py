"""Unit tests for AssetUploader and checksum generation."""

from pathlib import Path

from releasecraft.publisher.asset_uploader import AssetUploader


def test_calculate_sha256_and_generate_checksums(tmp_path: Path) -> None:
    f1 = tmp_path / "app-v1.0.tar.gz"
    f1.write_bytes(b"binary payload one")

    f2 = tmp_path / "app-v1.0.whl"
    f2.write_bytes(b"binary payload two")

    digest1 = AssetUploader.calculate_sha256(f1)
    digest2 = AssetUploader.calculate_sha256(f2)
    assert len(digest1) == 64
    assert len(digest2) == 64
    assert digest1 != digest2

    checksum_file = tmp_path / "SHA256SUMS"
    out = AssetUploader.generate_checksums_file([f1, f2], checksum_file)
    assert out.is_file()

    content = out.read_text(encoding="utf-8")
    assert f"{digest1}  app-v1.0.tar.gz" in content
    assert f"{digest2}  app-v1.0.whl" in content


def test_resolve_asset_paths_globs(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "pkg-0.1.0-py3-none-any.whl").write_text("whl", encoding="utf-8")
    (dist / "pkg-0.1.0.tar.gz").write_text("tar", encoding="utf-8")
    (dist / "README.txt").write_text("txt", encoding="utf-8")

    resolved = AssetUploader.resolve_asset_paths(["dist/*.whl", "dist/*.tar.gz"], base_dir=tmp_path)
    assert len(resolved) == 2
    names = [p.name for p in resolved]
    assert "pkg-0.1.0-py3-none-any.whl" in names
    assert "pkg-0.1.0.tar.gz" in names
    assert "README.txt" not in names
