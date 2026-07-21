# Compliance (GDPR)

How this system handles personal data under the EU GDPR. Scope: a portfolio
demo, but the controls are the real ones a production system would use.

## Data residency

All Azure resources run in an EU region (Sweden Central; Germany West Central
is the alternative where capacity allows). Azure OpenAI is the EU-region
resource. Langfuse, when enabled, uses its EU data region. No personal data
leaves the EU.

## What personal data can appear

Support tickets are the only source of personal data: a ticket's summary or
description may contain names, emails, phone numbers, or IP addresses entered
by an engineer. Technical manuals contain none.

## Privacy by design (Art. 25)

PII is masked with Microsoft Presidio **before** it can reach any durable or
external store. Masking runs at the pipeline entrance, ahead of embedding,
indexing, logging, and observability capture. A vector is a lossy, irreversible
projection of its text, so once an embedding is written the original PII cannot
be selectively removed; masking must therefore happen first, and it does.

## Data-flow map

| Store | Contains | Personal data? |
|---|---|---|
| PostgreSQL (system of record) | tickets, resolutions, jobs, audit log | yes (masked ticket text) |
| Azure AI Search `tickets` index | ticket text + vectors for retrieval | yes (masked) |
| Azure AI Search `manuals` index | manual chunks + vectors | no |
| Blob storage | raw documents, artifacts | no |
| Application Insights / logs | traces, metrics; PII masked pre-logging | no |

## Right to erasure (Art. 17)

`DELETE /v1/tickets/{id}` runs a verified deletion saga:

1. Delete the ticket document from the AI Search `tickets` index (external
   store first, so a failure leaves Postgres untouched and the call is
   retryable).
2. In one Postgres transaction: delete the ticket (its resolutions
   cascade-delete via the foreign key), and null out any job payloads that
   referenced the ticket.
3. Write an `audit_log` entry recording the erasure (actor, counts, timestamp).

An integration test proves the ticket is removed from the search index, the
ticket and its resolutions are deleted from Postgres, job payloads are
scrubbed, and the audit entry is written. Manual content is not personal data
and is never touched.

## Retention and audit

- Application Insights retention is 30 days.
- The `audit_log` table is append-only and records erasures and other
  security-relevant actions.
- Job records keep their status and error class for operations, but their
  `ticket_id` is nulled and payloads scrubbed on erasure, so no personal data
  survives in job history.

## Honest boundaries

- Backups: point-in-time Postgres backups may retain erased rows until they
  age out; a production runbook would document backup-scoped erasure.
- Access control uses hashed API keys; a production system would move to Entra
  ID / OAuth2 with per-user consent and data-subject request workflows.
