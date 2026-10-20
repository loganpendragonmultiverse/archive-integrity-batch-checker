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
