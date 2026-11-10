# Finding money is not enough: evaluating financial advocacy agents

*Published November 10, 2026. Historical evaluation runs: October 16–23, 2026.*

A financial assistant can notice a duplicate charge and still fail the person using it. It might never contact the company. It might ask for a refund that already arrived. It might cancel something the user wanted to keep. Or it might announce that money was recovered when it has only sent a request.

We built the Ombudly financial advocacy evals to measure more of that chain: finding a problem, taking the appropriate next step within the user's permissions, and checking what happened afterward.

We are publishing a research preview with **54 synthetic households, 172 planted opportunities, five suites, and scoring evidence from 16 historical run groups**. The code, datasets, simulated counterparties, deterministic scorer and sanitized evidence are available in the [Ombudly eval repository](https://github.com/tcmartin/ombudly-evals). The [versioned release](https://github.com/tcmartin/ombudly-evals/releases/tag/v0.1.0-preview) makes it possible to inspect and rescore the same records.

## What a household contains

Each household has a transaction history and supporting evidence: receipts, cancellation notices, account information, bills, emails or notes. The evaluator has a separate answer key describing the planted opportunities and decoys. The agent is not supposed to see that key.

The suites expand the task in stages:

- **v1:** overdraft fees, duplicate charges, subscriptions, missing refunds and settlement claims.
- **v2:** multiple accounts, partially refunded charges, receipt images, login handoffs and counterparties that ask follow-up questions.
- **v3:** medical and insurance cases, security deposits, cancelled flights and returns.
- **v4:** companies reached only by email, including replies that the agent must answer.
- **v5:** settlement eligibility, official-looking notices and deceptive claims sites.

Decoys matter. A refund that already arrived is not another recovery opportunity. Two similar orders are not automatically a duplicate charge. A message offering money in exchange for bank details is not a legitimate shortcut.

All household data and financial outcomes are synthetic. These are not customer bank records, real medical cases or measured savings for actual users. Real brand names sometimes appear as background descriptors, without implying endorsement or a real customer relationship.

## Measuring the right outcome

The headline metric is **handled value**. It adds simulated value recovered through a correct request to the value correctly referred to the user when the next step needs their approval.

That distinction is essential. An agent should not get extra credit for bypassing a required approval. But a correctly escalated claim is also not the same as money arriving in a bank account. The published results therefore separate simulated realized value, pending-approval value, verification, unauthorized actions, decoy mistakes and false completions.

The scorer is deterministic and heuristic. It matches aliases, keywords, amounts, saved work, approval requests and simulated action logs. It is not an independent human judgment of whether a real institution would pay. Its rules and limitations are visible in the [methodology](https://github.com/tcmartin/ombudly-evals/blob/v0.1.0-preview/docs/METHODOLOGY.md).

## What the archived runs show

These runs were recorded in October, not rerun against today's model endpoints for this publication. Model names below are the requested labels recorded by the harness. The original records do not independently attest immutable provider model snapshots.

| Configuration | Households | Recorded model | Handled value |
|---|---:|---|---:|
| v1, single pass | 18 | gpt-6-astra | 100.0% |
| v1, single pass | 18 | gpt-6.1-sol | 100.0% |
| v1, single pass | 18 | gpt-6-luna | 83.7% |
| v1, Luna continuation loop, repeats 1 / 2 | 18 each | gpt-6-luna | 100.0% / 96.5% |
| v2, permission gate | 12 | gpt-6.1-sol / gpt-6-luna | 100.0% / 93.5% |
| v3d, broader advocacy cases | 12 | gpt-6.1-sol / gpt-6-luna | 93.9% / 92.4% |
| v4, email-only counterparties | 6 | gpt-6.1-sol / gpt-6-luna | 86.5% / 72.9% |
| v5b, settlement eligibility, Jev off | 6 | gpt-6.1-sol / gpt-6-luna | 100.0% / 85.2% |
| v5c, settlement eligibility, Jev on | 6 | gpt-6.1-sol / gpt-6-luna | 100.0% / 70.4% |

The [complete results](https://github.com/tcmartin/ombudly-evals/blob/v0.1.0-preview/RESULTS.md) include adverse-event counts and the later two-household isolation check. That small check is not presented as a full-suite model comparison.

Three observations stand out.

**First, a simple suite can stop being useful for separating systems.** Both recorded frontier configurations handled all of v1's planted value. That does not establish general financial competence. It tells us that harder cases were needed.

**Second, the surrounding application matters.** Luna's v1 single-pass result was 83.7%; the later continuation-loop configuration scored 100.0% and 96.5% across two repeats. This is evidence about a particular model-plus-harness setup. It is not a controlled claim that a loop always produces a particular gain. The application and harness evolved during development.

**Third, headline percentages can hide meaningful differences.** The v5b and v5c Luna runs both brought 5 of 6 claims to the user, yet their value-weighted scores were 85.2% and 70.4% because the missed claims had different values. In v3d, the handled-value scores were close, while correct approval requests differed: Sol had 8 of 10 and Luna 6 of 10. A single number is not enough to understand the behavior.

## What we can reproduce today

The published package supports an offline rescore of all **176 household records** in the selected runs. Each sanitized input was checked against its original score, and the published aggregates reproduce the stored historical values. All five dataset generators also reproduced the committed fixture bytes in an isolated copy on the release host.

Running the scorer self-check and release verifier requires only Python's standard library. Optional dataset regeneration requires Pillow and the receipt font. No new paid model or provider call was made to prepare this release.

There is an important boundary: **the original end-to-end system is not yet self-contained in the public package**. The private Ombudly application, MCP tool surface and live adapters are not released. The dataset, simulator and scorer can support another isolated adapter, but that should be described as its own specified system until equivalence is demonstrated.

## What this release does not establish

The suites are small, manually designed, US-oriented development cases. Most configurations have one run. Different suites and app versions are not directly comparable. The results are not a current global model leaderboard, a safety certification, a real-world recovery rate or financial, legal or medical advice.

Public answer keys also create contamination risk. Future generalization claims should use independently authored held-out cases, repeated runs and stronger recorded provenance, including the exact app revision, model configuration and sampling settings.

This is a **public, rights-reserved research preview**, not an open-source licensing announcement. The source project had no applicable license file, and a reuse license remains an owner decision.

The useful next step is scrutiny: inspect the cases, check the scoring rules, reproduce the numbers, and identify failure modes the suite is missing. Financial advocacy needs evaluation that follows the task past a plausible answer and into the actions, permissions and evidence of the outcome.
