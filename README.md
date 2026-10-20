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

## Streaming verification budgets

Version 1.2 reads members in chunks with positive integer max_member_bytes
(default 268435456) and max_total_bytes (default 1073741824, per archive).
Limits count decompressed bytes, including directory entries. Reading stops after
at most one extra byte to detect exhaustion. Exact-limit archives can verify.
A status of incomplete, budget_exhausted, and verification_complete: false
identify budget exhaustion; these archives never count as valid.
Encrypted, unsupported, and corrupt members report errors. No member is extracted.
Budgets limit decompressed output reads, not ZIP metadata memory or CPU time.

## Input and report guarantees (1.2.1)

Input must be a JSON object with a non-empty paths array of non-empty strings.
max_compression_ratio must be a finite positive JSON number; byte budgets must
be positive integers, excluding booleans. Relative archive paths are interpreted
against the command's working directory. A missing or inaccessible archive gets
its own error record and later paths still run. Source symbolic links are followed.
Exit 0 means a report was generated; inspect invalid_count, incomplete_count and
each archive status to decide whether the collection passed. Invalid input or
report I/O exits 2.

Reports use exclusive creation and refuse existing files or symbolic links,
including dangling links. A file created after validation is preserved. Keep
source archives stable during verification; this is not a filesystem snapshot.
This guard handles accidental collisions, not a hostile concurrent filesystem.

Both release packages install README, DEVELOPMENT, TESTING, CHANGELOG and the
sample beneath share/doc/archive-integrity-batch-checker in the installation
prefix. See [TESTING.md](TESTING.md) for reproducible acceptance.
