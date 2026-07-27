from __future__ import annotations

import json
import re
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

PROJECT = "archive-integrity-batch-checker"


def _require(data: dict[str, Any], key: str) -> Any:
    value = data.get(key)
    if value is None or value == "" or value == []:
        raise ValueError(f"{key} is required")
    return value


def _archive_integrity(data: dict[str, Any]) -> dict[str, Any]:
    max_ratio = float(data.get("max_compression_ratio", 1000))
    if max_ratio <= 0:
        raise ValueError("max_compression_ratio must be positive")
    results: list[dict[str, Any]] = []
    for raw in _require(data, "paths"):
        path = Path(raw).resolve()
        item = {
            "path": str(path),
            "bytes": path.stat().st_size if path.exists() else 0,
            "valid": False,
            "members": 0,
            "error": None,
            "warnings": [],
        }
        if not path.is_file():
            item["error"] = "file not found"
        elif path.suffix.lower() not in {".zip", ".cbz", ".epub"}:
            item["error"] = "unsupported archive family"
        else:
            try:
                with zipfile.ZipFile(path) as archive:
                    bad = archive.testzip()
                    names = archive.namelist()
                    infos = archive.infolist()
                    unsafe_names = [
                        name
                        for name in names
                        if PurePosixPath(name.replace("\\", "/")).is_absolute()
                        or ".." in PurePosixPath(name.replace("\\", "/")).parts
                        or bool(re.match(r"^[A-Za-z]:", name))
                    ]
                    high_ratio = [
                        info.filename
                        for info in infos
                        if info.file_size
                        and info.file_size / max(info.compress_size, 1) > max_ratio
                    ]
                    warnings = []
                    if not names:
                        warnings.append("empty archive")
                    if unsafe_names:
                        warnings.append("unsafe member paths")
                    if high_ratio:
                        warnings.append("high compression ratio")
                    item.update(
                        {
                            "valid": bad is None,
                            "members": len(names),
                            "first_bad_member": bad,
                            "duplicate_names": sorted(
                                (name for name, count in Counter(names).items() if count > 1)
                            ),
                            "encrypted_members": sum(bool(info.flag_bits & 1) for info in infos),
                            "unsafe_members": sorted(unsafe_names),
                            "high_compression_members": sorted(high_ratio),
                            "warnings": warnings,
                        }
                    )
            except (OSError, zipfile.BadZipFile) as exc:
                item["error"] = type(exc).__name__
        results.append(item)
    return {
        "archives": results,
        "max_compression_ratio": max_ratio,
        "valid_count": sum(item["valid"] for item in results),
        "invalid_count": sum(not item["valid"] for item in results),
        "warning_count": sum(len(item["warnings"]) for item in results),
    }


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    return {"version": 1, "project": PROJECT, **_archive_integrity(data)}


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [f"# {report['project'].replace('-', ' ').title()} report", ""]
    for key, value in report.items():
        if key not in {"version", "project"}:
            lines.extend(
                [
                    f"## {key.replace('_', ' ').title()}",
                    "",
                    f"```json\n{json.dumps(value, indent=2, ensure_ascii=False, default=str)}\n```",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"
