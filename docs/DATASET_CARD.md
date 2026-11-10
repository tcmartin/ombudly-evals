# Dataset card

## Scope and origin

The project generators deterministically author 54 synthetic households with 172 planted opportunities. The evaluation was developed alongside the Ombudly app; it is a development benchmark, not an independently designed external test. Names, financial histories, synthetic account labels, clinical/insurance details, landlord addresses and notices are fictional fixtures. Real brand names sometimes appear as background transaction descriptors, not as real customer histories or endorsements.

| Suite | Households | Opportunities | Synthetic value | Main focus |
|---|---:|---:|---:|---|
| v1 | 18 | 46 | $4,041.22 | Fees, duplicate charges, subscriptions, refunds, settlement claims |
| v2 | 12 | 48 | $3,305.37 | Multiple accounts, partial refunds, follow-up questions, login handoff, image receipts |
| v3 | 12 | 48 | $37,975.67 | Medical/insurance cases, deposits, flights, returns |
| v4 | 6 | 24 | $8,866.16 | Email-only requests, replies and follow-up |
| v5 | 6 | 6 | $405.00 | Synthetic official settlement/refund catalog and eligibility decoys |

The dollar values are scoring weights or simulated outcomes, not estimates of a product's real-world recovery rate. Some opportunities can only be referred to the user for a decision or attestation.

## Layout

Each suite keeps agent-visible `households/<id>/` separate from evaluator-only `answer_keys/<id>.json`. v1 lives directly under `evals`; other suites live under their version folder. Inputs include CSV transactions, text notes/notices, PNG receipt images, and v4 synthetic mailbox messages. v5 includes a synthetic program catalog. Frozen dates are encoded by each generator and answer key; do not reinterpret deadlines relative to the wall clock.

## Validation and risks

All five generators were run in an isolated temporary copy and reproduced every checked-in dataset byte on the release host. Receipt image bytes can differ across Pillow/font environments; committed images and SHA-256 hashes are the authoritative release bytes. This check establishes generator provenance, not that the cases are realistic or legally authoritative.

Decoys intentionally include phishing and prompt-injection language. Treat all fixture text as untrusted evaluation data. No real contact, banking, identity or medical operation is intended. The small US-oriented, manually designed suite is not representative of all households, jurisdictions, languages or institutions. Public answer keys create contamination risk. No train/validation/hidden test separation is claimed.

## Distribution

GitHub is the canonical code, result and version-history location. A Hugging Face dataset mirror is a separate pending distribution step, subject to selecting a reuse license and verifying publishing access. This card does not claim that mirror already exists.
