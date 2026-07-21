# Observability

Three concerns, three tools. One correlation id ties a request together
across all of them.

| Question | Tool | Status |
|---|---|---|
| Why did the agent produce THIS answer, at what cost? | Langfuse (EU) | live — full trajectory verified |
| Is the service up / fast / erroring? What happened in this request? | Log Analytics + Application Insights | live — Container Apps ship logs/metrics + our structured JSON logs |
| Infra metrics dashboards | Prometheus + Grafana | designed, not run (see below) |

## Langfuse (AI-native)

The LangGraph callback streams the full agent trajectory to Langfuse Cloud
(EU region): which graph path ran, each node's prompt and retrieved context,
and per-step latency. This is the layer that answers "why this answer",
which neither metrics nor generic traces can. Verified end-to-end in the
agent step.

## Application Insights + Log Analytics

Azure Container Apps ships every container's stdout and platform metrics to
the Log Analytics workspace that backs Application Insights, with no code
required. Our app logs are structured JSON in production (one object per
line) carrying the request `correlation_id`, so a single id retrieves the
whole request story with a KQL query.

## The OpenTelemetry tradeoff (ADR)

Both Langfuse and the Azure Monitor OpenTelemetry exporter build on the
OpenTelemetry SDK, and their supported SDK versions currently conflict
(Langfuse pins ~1.44, the Azure Monitor distro pins ~1.43). A single Python
process can only run one OpenTelemetry SDK version, so you choose one
in-process exporter.

For an AI system the higher-value pipeline is Langfuse: it shows the agent
trajectory and per-step cost, which is exactly what you debug in an LLM app.
Platform telemetry (request rates, latencies, container health) still reaches
Application Insights through the Container Apps integration, so nothing is
lost. If a team needed custom app spans in App Insights too, the clean
answer is a sidecar or collector, not a second SDK in the same process.

## Prometheus + Grafana

The design specifies self-hosted Prometheus + Grafana as two extra Container
Apps. They are deliberately not run: operating a metrics stack for a
single-team demo is unjustified when Log Analytics already stores the metrics
and App Insights renders them. Recognizing when NOT to add a service is the
architectural judgment; the scale-up path is documented, not built.

## Alerts

Azure Monitor alert rules (error rate, p95 latency, `/ready` failing, daily
cost) are the intended alerting surface, defined as Terraform. At demo scale
the cost kill-switch is simply `make infra-down`.
