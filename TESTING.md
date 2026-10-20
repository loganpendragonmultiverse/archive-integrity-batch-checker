# Testing

Install with python -m pip install -e ".[dev]", then run ruff format --check .,
ruff check ., mypy src, pytest, and python -m build.

CI runs the existing Linux, Windows and macOS matrix on Python 3.10 and 3.14,
with a separate build. The full suite retains 90% branch-aware coverage.

## 1.2.1 regression acceptance

Verify malformed roots, non-array paths, invalid elements, booleans/non-finite
ratios and invalid byte budgets produce actionable errors. Confirm an unreadable
archive does not prevent later archives from verifying. Report tests preserve
existing files, existing/dangling symbolic links (when supported) and a file
created between the existence check and exclusive open.

Retain existing exact-budget, duplicate-entry, CRC, encryption, unsupported
compression and malformed-LZMA cases. Budget exhaustion is incomplete, never valid.
These checks validate ZIP containers; they do not validate EPUB semantics or malware.

## Installed artifacts

Build wheel and source distribution, install each into a separate fresh virtual
environment and run the complete suite outside the checkout against that installed
package. Confirm imported module provenance and run the real console command on
a synthetic valid archive plus missing/corrupt input. Compare installed README,
DEVELOPMENT, TESTING, CHANGELOG and sample bytes to the tagged source.
Verify JSON and Markdown output, exit behavior and no-overwrite protection.
Public release acceptance must repeat against the exact successful tag-workflow assets.
