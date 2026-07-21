# Build Progress

Tracks completion of the build order in the architecture design (Section 15).

| Step | Scope | Status |
|---|---|---|
| 1 | Foundations: repo restructure, pinned deps, ruff + mypy strict, settings, Alembic baseline, exceptions taxonomy, pickle removal | done |
| 2 | Hot-path data layer: Postgres schema, AI Search indexes, single-document ingestion | done — 1142 chunks indexed, re-run idempotent, registry verified |
| 3 | Retrieval layer: hybrid query client, FAISS/BM25 removal with eval comparison | done — comparison recorded with bias analysis, legacy stores removed |
| 4 | Agent layer: LLM wrapper, LangGraph graph, versioned prompts, Langfuse | done — live e2e resolution grounded+cited at €0.006; Langfuse keys pending |
| 5 | API + hot-path async: Service Bus, worker, DLQ, auth, Streamlit console | done — live async e2e verified (webhook→queue→worker→job done); DLQ poison test pending |
| 6 | Evaluation plane: golden dataset, RAGAS, MLflow, thresholds | pending |
| 7 | Containerization: four images + compose stack | pending |
| 8 | Cold path: ADLS zones, dual-entry ingestion job, ADF pipelines | pending |
| 9 | Infrastructure: Terraform modules, remote state, RBAC, Key Vault | pending |
| 10 | Deployment: ACR, Container Apps, KEDA, smoke tests | pending |
| 11 | CI/CD: three workflows, OIDC, rollback | pending |
| 12 | Observability completion: three layers, alerts | pending |
| 13 | Security & GDPR hardening: RTBF saga, audit log, COMPLIANCE.md | pending |
| 14 | Docs & demo readiness | pending |
