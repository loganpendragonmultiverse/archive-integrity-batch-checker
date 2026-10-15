from __future__ import annotations

import json
import math
import re
import zipfile
import zlib
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
    if not math.isfinite(max_ratio) or max_ratio <= 0:
        raise ValueError("max_compression_ratio must be positive")
    budgets = {}
    for key, default in (
        ("max_member_bytes", 256 * 1024 * 1024),
        ("max_total_bytes", 1024 * 1024 * 1024),
    ):
        value = data.get(key, default)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{key} must be a positive integer")
        budgets[key] = value
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
            "verification_complete": False,
            "status": "error",
            "decompressed_bytes": 0,
            "budget_exhausted": None,
        }
        if not path.is_file():
            item["error"] = "file not found"
        elif path.suffix.lower() not in {".zip", ".cbz", ".epub"}:
            item["error"] = "unsupported archive family"
        else:
            try:
                with zipfile.ZipFile(path) as archive:
                    bad = None
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
                    total = 0
                    complete = True
                    for info in infos:
                        member_bytes = 0
                        if info.flag_bits & 1:
                            item["error"] = "encrypted member"
                            bad = info.filename
                            complete = False
                            break
                        try:
                            with archive.open(info) as member:
                                while True:
                                    remaining = min(
                                        budgets["max_member_bytes"] - member_bytes,
                                        budgets["max_total_bytes"] - total,
                                    )
                                    chunk = member.read(min(65536, remaining + 1))
                                    if not chunk:
                                        break
                                    member_bytes += len(chunk)
                                    total += len(chunk)
                                    if (
                                        member_bytes > budgets["max_member_bytes"]
                                        or total > budgets["max_total_bytes"]
                                    ):
                                        item["budget_exhausted"] = (
                                            "max_member_bytes"
                                            if member_bytes > budgets["max_member_bytes"]
                                            else "max_total_bytes"
                                        )
                                        complete = False
                                        break
                            if not complete:
                                break
                            if member_bytes != info.file_size:
                                raise zipfile.BadZipFile("member size mismatch")
                        except (
                            OSError,
                            EOFError,
                            RuntimeError,
                            NotImplementedError,
                            zipfile.BadZipFile,
                            zlib.error,
                        ) as exc:
                            item["error"] = type(exc).__name__
                            bad = info.filename
                            complete = False
                            break
                    item.update(
                        {
                            "valid": complete and bad is None,
                            "verification_complete": complete,
                            "status": "verified"
                            if complete
                            else ("incomplete" if item["budget_exhausted"] else "error"),
                            "decompressed_bytes": total,
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
        **budgets,
        "incomplete_count": sum(item["status"] == "incomplete" for item in results),
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
