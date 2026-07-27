from __future__ import annotations

import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT = "archive-integrity-batch-checker"


def _require(data: dict[str, Any], key: str) -> Any:
    value = data.get(key)
    if value is None or value == "" or value == []:
        raise ValueError(f"{key} is required")
    return value


def _archive_integrity(data: dict[str, Any]) -> dict[str, Any]:
    results = []
    for raw in _require(data, "paths"):
        path = Path(raw).resolve()
        item = {
            "path": str(path),
            "bytes": path.stat().st_size if path.exists() else 0,
            "valid": False,
            "members": 0,
            "error": None,
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
                    item.update(
                        {
                            "valid": bad is None,
                            "members": len(names),
                            "first_bad_member": bad,
                            "duplicate_names": sorted(
                                (name for name, count in Counter(names).items() if count > 1)
                            ),
                            "encrypted_members": sum(
                                bool(info.flag_bits & 1) for info in archive.infolist()
                            ),
                        }
                    )
            except (OSError, zipfile.BadZipFile) as exc:
                item["error"] = type(exc).__name__
        results.append(item)
    return {
        "archives": results,
        "valid_count": sum(item["valid"] for item in results),
        "invalid_count": sum(not item["valid"] for item in results),
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
