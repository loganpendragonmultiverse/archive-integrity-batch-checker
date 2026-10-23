# Development contract

Validate ZIP, CBZ, and EPUB archives in bulk without permanently extracting them.

Version 1.1 adds review warnings for empty archives, unsafe paths, and extreme compression ratios without presenting them as malware verdicts.

Preserve deterministic, source-safe behavior and the interpretation boundary documented in the README. Every feature release must update tests, version metadata, changelog, README claims, repository metadata, release assets, and the Forge catalog together.

## 1.2.1 completion contract

Keep input-shape errors actionable, isolate missing/inaccessible archive results,
and create reports exclusively. Retain streaming decompression budgets and their
incomplete-verification semantics. Run the full 90% branch-coverage gate, native
OS/Python matrix and installed wheel/source-package acceptance before release.
Both packages must contain the four authority documents and sample input.

## Optional exit policies (1.3.0)

By default, exit 0 still means the report was generated, even when archives need attention. For scripts and scheduled checks, select the conditions that should return exit 1 after the full report is successfully written:

```bash
archive-integrity input.json --format json --fail-on invalid
archive-integrity input.json --fail-on invalid --fail-on warning --output report.md
```

Repeat `--fail-on` to combine policies. `invalid` matches any unverified archive, including corrupt, missing, unsupported or budget-incomplete inputs (`invalid_count > 0`). `incomplete` matches budget-exhausted verification specifically (`incomplete_count > 0`). `warning` matches any reported review warning (`warning_count > 0`), including warnings on otherwise verified archives. Repeating a policy has no additional effect. These choices do not change archive interpretation, budgets, report schema or report contents. Warnings remain review evidence, not malware findings.

Input/argument and report-I/O failures still return exit 2 and take precedence. A policy failure returns 1 only after output succeeds; review the report to see the affected archives. Existing report files and symbolic links remain refused, and source files remain read-only. No new runtime dependencies or extraction are introduced.
