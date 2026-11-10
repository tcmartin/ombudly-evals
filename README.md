# Ombudly financial advocacy evals

**Can an agent find a financial problem, take the right next step within its permissions, and verify the outcome?**

A public research preview of five synthetic household evaluation suites originally built for [Ombudly](https://ombudly.com). It covers duplicate charges, missing refunds, subscriptions, bills, deposits, email follow-up, settlement eligibility, and malicious lookalike notices.

**54 synthetic households · 172 planted opportunities · five suites · 16 archived runs · 176 scored household records.**

This release publishes the dataset, generators, simulator, deterministic scorer, and sanitized scoring evidence. It does **not** publish the private Ombudly application or offer a fully standalone live agent benchmark.

Read the [research writeup](docs/RESEARCH-WRITEUP.md) for the motivation, findings and limitations. Browse the [Hugging Face dataset mirror](https://huggingface.co/datasets/trevdatastreams/ombudly-evals), with separate household inputs and evaluator-only answer keys.

## Results at a glance

These are **historical October 16–23, 2026 runs**, rescored offline for this release on November 10, 2026. They are the latest saved comparisons located in the source project, not fresh November model tests. Model names are the requested labels recorded by the harness, not independently verified immutable provider snapshots.

| Suite / configuration | Households | Recorded model | Handled value | Correct approval requests |
|---|---:|---|---:|---:|
| v1, single pass | 18 | gpt-6-astra | 100.0% | 12/12 |
| v1, single pass | 18 | gpt-6.1-sol | 100.0% | 12/12 |
| v1, single pass | 18 | gpt-6-luna | 83.7% | 11/12 |
| v1, Luna with continuation loop, repeats 1 / 2 | 18 each | gpt-6-luna | 100.0% / 96.5% | 12/12 each |
| v2, permission gate | 12 | gpt-6.1-sol / gpt-6-luna | 100.0% / 93.5% | 12/12 / 11/12 |
| v3d, medical, deposits, flights and returns | 12 | gpt-6.1-sol / gpt-6-luna | 93.9% / 92.4% | 8/10 / 6/10 |
| v4, email-only counterparties | 6 | gpt-6.1-sol / gpt-6-luna | 86.5% / 72.9% | 6/6 each |
| v5b, settlement eligibility, Jev off | 6 | gpt-6.1-sol / gpt-6-luna | 100.0% / 85.2% | 6/6 / 5/6 |
| v5c, settlement eligibility, Jev on | 6 | gpt-6.1-sol / gpt-6-luna | 100.0% / 70.4% | 6/6 / 5/6 |

**“Handled value” combines simulated recovery and value correctly referred to the user for approval. It is not money recovered for real people.** All households, transactions, account references, bills and medical scenarios are synthetic. Actual bank/provider data is excluded. The two-household October 23 isolation check is listed separately in [all results](results/summary.csv), not compared as a full-suite model result.

The suite and app changed between versions. Compare within the same row/configuration, not across suites. The small, largely single-run samples do not establish a reliable global model ranking. v1 is saturated for the recorded frontier configurations. The same Luna continuation setup varied from 96.5% to 100.0%, illustrating run-to-run noise.

## Reproduce the published scores offline

Python 3.9 or newer, standard library only:

```sh
python3 evals/test_score.py
python3 scripts/verify_release.py
```

The verifier recomputes every household and aggregate from the sanitized inputs and checks dataset/source/result hashes. It does not call models, banks, email services, the Ombudly app, or the network. To inspect one run manually:

```sh
python3 evals/score.py results/20261018-111925-v4-codex-gpt-6.1-sol
```

That original scorer command writes a local report.json and report.md into the run directory. Its legacy “cost_usd” field is a historical API-price estimate, **not a bill, current price quote, or actual benchmark spend**. See [methodology](docs/METHODOLOGY.md).

## Contents

- [Dataset card](docs/DATASET_CARD.md): suite sizes, provenance, boundaries and risks.
- [Methodology and limitations](docs/METHODOLOGY.md): scoring definitions, configurations, selection and reproducibility.
- [Complete results including error metrics](RESULTS.md), [CSV result rows](results/summary.csv) and [machine-readable run index](results/index.json).
- `evals/households` and `evals/v2` through `evals/v5`: synthetic agent-visible evidence and separately stored answer keys.
- `evals/generate*.py`: deterministic generators. Optional regeneration requires Pillow and the DejaVu Sans font for receipt images.
- `evals/score.py`, `evals/test_score.py`: original scoring implementation and self-check.
- `evals/sim/server.py`: local mock counterparty pages, not a real service.
- `results/<run>/`: sanitized scorer inputs and recomputed reports. No account credentials or full agent/session transcripts.

## Safe use

Keep answer keys and scoring records **outside the evaluated agent's accessible workspace**. Public answers can contaminate future models; use independently authored held-out cases for new claims. Do not point fixture email addresses or localhost URLs at real services. These examples are not financial, legal or medical advice.

For new agent runs, implement an isolated adapter for your agent/application, pin its version, capture the actual model configuration, preserve the frozen scenario dates and log all attempted actions. The original private application and tool surface are not included, so reproducing the original end-to-end behavior is not yet self-contained.

## License status

Public preview; no open-source or dataset reuse license has been selected. See [LICENSE-STATUS.md](LICENSE-STATUS.md). This release is not represented as an open-source project until the owner selects a license.
