# Changelog

## 1.2.0 — 2026-10-15

- Keep malformed LZMA member errors within their archive so later archives still verify.
- Stream member verification with per-member and per-archive decompression budgets.
- Report exhausted verification as incomplete, and encrypted/corrupt members as errors.

## 1.1.0 - 2026-07-27

- Added warnings for empty archives, unsafe member paths, and configurable high compression ratios.
- Added warning totals and exact risky-member evidence without extracting content.

## 1.0.0 - 2026-07-26

- Released the first complete Archive Integrity Batch Checker command-line workflow.
- Added deterministic reporting, representative examples, cross-platform tests, and explicit limitations.
