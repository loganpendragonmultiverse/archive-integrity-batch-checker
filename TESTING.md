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

## Optional exit policies (1.3.0)

By default, exit 0 still means the report was generated, even when archives need attention. For scripts and scheduled checks, select the conditions that should return exit 1 after the full report is successfully written:

```bash
archive-integrity input.json --format json --fail-on invalid
archive-integrity input.json --fail-on invalid --fail-on warning --output report.md
```

Repeat `--fail-on` to combine policies. `invalid` matches any unverified archive, including corrupt, missing, unsupported or budget-incomplete inputs (`invalid_count > 0`). `incomplete` matches budget-exhausted verification specifically (`incomplete_count > 0`). `warning` matches any reported review warning (`warning_count > 0`), including warnings on otherwise verified archives. Repeating a policy has no additional effect. These choices do not change archive interpretation, budgets, report schema or report contents. Warnings remain review evidence, not malware findings.

Input/argument and report-I/O failures still return exit 2 and take precedence. A policy failure returns 1 only after output succeeds; review the report to see the affected archives. Existing report files and symbolic links remain refused, and source files remain read-only. No new runtime dependencies or extraction are introduced.
