"""Binary asset resolution, SHA256 checksum generation, and release uploading."""

import glob
import hashlib
from pathlib import Path

import httpx


class AssetUploader:
    """Manages release assets and checksum manifests."""

    @staticmethod
    def resolve_asset_paths(patterns: list[str], base_dir: Path | str | None = None) -> list[Path]:
        """Resolve glob patterns into a sorted list of unique existing file paths."""
        base = Path(base_dir) if base_dir else Path.cwd()
        resolved: list[Path] = []

        for pattern in patterns:
            pattern_path = pattern if Path(pattern).is_absolute() else str(base / pattern)
            matches = glob.glob(pattern_path, recursive=True)
            for m in matches:
                p = Path(m)
                if p.is_file() and p not in resolved:
                    resolved.append(p)

        resolved.sort()
        return resolved

    @staticmethod
    def calculate_sha256(file_path: Path | str) -> str:
        """Compute SHA256 hexadecimal digest for a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def generate_checksums_file(
        cls,
        files: list[Path],
        output_path: Path | str,
    ) -> Path:
        """Create a standard SHA256SUMS file for a collection of assets."""
        out = Path(output_path)
        lines: list[str] = []

        for f in files:
            digest = cls.calculate_sha256(f)
            lines.append(f"{digest}  {f.name}")

        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return out

    @staticmethod
    def upload_github_asset(
        upload_url_template: str,
        token: str,
        asset_path: Path,
        content_type: str = "application/octet-stream",
    ) -> dict:
        """Upload an asset to a GitHub release."""
        # Clean URL template (e.g. https://uploads.github.com/.../assets{?name,label})
        url = upload_url_template.split("{")[0] + f"?name={asset_path.name}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type,
            "User-Agent": "ReleaseCraft",
            "Content-Length": str(asset_path.stat().st_size),
        }

        with open(asset_path, "rb") as data:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(url, headers=headers, content=data)
                if resp.status_code in (200, 201):
                    return resp.json()
                raise RuntimeError(
                    f"Failed to upload asset {asset_path.name} (HTTP {resp.status_code}): {resp.text}"
                )
