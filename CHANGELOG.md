# Changelog

## 1.3.0 - 2026-10-23

- Add repeatable optional exit policies for invalid, incomplete and warning reports; retain exit 0 by default and operational-error exit 2.
- Produce unchanged full reports before policy exit 1, with source-read-only and exclusive-output behavior preserved.

## 1.2.1 — 2026-10-20

- Validate JSON roots, path arrays and finite numeric ratio settings explicitly.
- Isolate missing or inaccessible archive metadata errors within a batch.
- Preserve existing, linked and concurrently created report destinations.
- Add the testing contract and install all four authority documents and sample in both packages.

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
