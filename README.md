# Archive Integrity Batch Checker

[![CI](https://github.com/loganpendragonmultiverse/archive-integrity-batch-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/loganpendragonmultiverse/archive-integrity-batch-checker/actions/workflows/ci.yml)

Validate ZIP, CBZ, and EPUB archives in bulk without permanently extracting them. The command uses explicit UTF-8 JSON input and produces reviewable JSON or Markdown output.

## Three-minute start

```bash
python -m pip install .
archive-integrity examples/sample.json
archive-integrity examples/sample.json --format json --output report.json
```

The example documents the input shape. Version 1.1 warns about empty containers, unsafe member paths, and members above a configurable `max_compression_ratio`, while retaining the exact member evidence. Existing report files are never overwritten. Source inputs are read-only except where the documented purpose explicitly creates a new output artifact.

## Privacy and platforms

The tool runs locally and does not upload input or include telemetry. Python 3.10 or newer is supported on Windows, macOS, and Linux.

## Interpretation boundary

The tool validates ZIP-family containers only. Warnings are review evidence rather than malware findings; a structurally valid archive can still contain unsafe, misleading, or semantically invalid content.

## Development

```bash
python -m pip install -e ".[dev]"
ruff format --check .
ruff check .
mypy src
pytest
python -m build
```

The project is feature-complete for its documented v1 scope. Maintenance focuses on correctness, security, compatibility, and well-supported input improvements.

Part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Licensed under the [MIT License](LICENSE).
