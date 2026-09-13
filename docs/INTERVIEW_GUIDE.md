# How TintinHR Reaches the LLM Decision

## Short interview answer

“I did not select the LLM from a leaderboard alone. I first created a representative HR golden dataset containing policy lookup, multi-turn, comparison, personalized SQL-plus-policy, access-control and unanswerable questions. I used the same retrieval pipeline and prompt for every candidate model, measured answer correctness, faithfulness, citation validity, refusal accuracy, latency, token usage and cost, then applied hard security/quality gates. Among the passing models, I selected the lowest-cost model meeting the latency target, while keeping providers configurable. I continuously run this suite because changing chunks, embeddings or prompts can change the best model.”

## Step-by-step model and pipeline evaluation

1. **Define business tasks**: policy Q&A, policy comparison, follow-up questions, personal leave balance, hybrid answers and access denials.
2. **Build a golden dataset**: HR-approved questions, expected facts, required source pages, allowed roles and whether the system must abstain.
3. **Separate retrieval from generation**: first measure whether the correct chunks reach top-k. A generator cannot recover evidence the retriever missed.
4. **Tune ingestion**: compare chunk size/overlap, page preservation, tables and document metadata.
5. **Evaluate retrieval**: hit-rate@k, MRR, context recall and context precision. Compare vector-only, keyword-only, hybrid RRF and reranked hybrid.
6. **Evaluate generators**: run identical retrieved context through candidate LLMs at temperature 0. Measure correctness, faithfulness, answer relevance, citation validity, refusal accuracy, p50/p95 latency, tokens and cost.
7. **Use hard gates**: reject a model if access-control leakage occurs, citation validity is below the target, or unsupported-answer refusal falls below the target—even if its average quality is high.
8. **Choose on the Pareto frontier**: among passing models, choose the least expensive/fastest one that meets quality targets. Keep a stronger fallback for difficult cases only if evaluation proves routing helps.
9. **Human review**: HR reviews sensitive and ambiguous examples; automated LLM-as-judge scores are signals, not unquestionable truth.
10. **Regression and production monitoring**: run the suite in CI for prompt/retrieval changes, trace latency/tokens/errors, sample feedback, and add failures back into the golden set.

## Suggested acceptance gates

| Metric | Initial target |
|---|---:|
| Retrieval hit-rate@6 | ≥ 0.90 |
| Citation validity | ≥ 0.98 |
| Faithfulness | ≥ 0.90 |
| Answer relevance | ≥ 0.85 |
| Abstention accuracy | ≥ 0.95 |
| Access-control leakage | 0 |
| p95 latency | ≤ 5 s (cloud) |

Targets are adjusted using real usage and risk appetite; they are not universal constants.

## Metadata-filtered, authorization-aware RAG

Each document stores access metadata: `visibility`, optional `department_id`, status, version and validity dates. After authentication the API derives an immutable access scope from trusted database claims. It converts the user's role to permitted visibility levels and includes the user's department. Both vector and keyword SQL queries contain these predicates before candidates are returned. Therefore a restricted chunk never enters the reranker, prompt, cache entry or citation list.

Cache keys include a hash of the access scope. This prevents an HR user's cached response being replayed to an employee. If a user's role/department changes, the versioned scope invalidates old cache keys.

This is stronger than retrieving everything and asking the LLM to ignore confidential text: prompts are not authorization controls.

## What Redis is doing (question 21)

- **Caching**: avoids recomputing safe, repeated answers; keys include user access scope and corpus version.
- **Rate limiting**: controls expensive/abusive chat and upload requests.
- **Background job broker**: Celery uses Redis to queue parsing and embedding work so uploads return quickly.
- **Transient coordination**: job status and short-lived locks.

PostgreSQL remains the durable source of truth. Redis loss may reduce performance or interrupt queued work, but it must not corrupt HR records.

## How to describe agentic RAG honestly

The agent is a controlled state graph, not an unconstrained autonomous bot. Its router chooses among `policy_search`, `employee_data`, `hybrid`, `holiday` and `out_of_scope`. Each tool has typed inputs and enforced authorization. Conditional edges decide whether to retrieve, combine evidence, generate, validate or safely refuse. This is predictable, testable and easier to audit than an open-ended loop.

