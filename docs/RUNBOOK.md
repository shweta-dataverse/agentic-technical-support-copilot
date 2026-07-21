# Runbook — zero to running

Two ways to run the project: **local** (everything on your machine via Docker
Compose, talking to cloud Azure OpenAI + AI Search) and **cloud** (fully
deployed on Azure Container Apps). Do the prerequisites once, then pick a path.

---

## 0. Prerequisites (once)

Install:
- Docker Desktop
- Python 3.12
- Azure CLI (`az`), then `az login`
- Terraform >= 1.6

Azure resources you create by hand (learning the portal):
- An **Azure OpenAI** resource in an EU region (Sweden Central), with two
  deployments: `gpt-5-mini` (chat) and `text-embedding-3-small` (embeddings).
- Note its **endpoint** and **key** (resource → Keys and Endpoint).

Clone and set up the Python env:
```bash
git clone https://github.com/shweta-dataverse/agentic-technical-support-copilot.git
cd agentic-technical-support-copilot
python3.12 -m venv .venv && source .venv/bin/activate
make install            # installs deps + the en_core_web_md spaCy model
```

Create your local `.env` from the template and fill in the Azure OpenAI values:
```bash
cp .env.example .env
# edit .env:
#   AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY
#   AZURE_OPENAI_DEPLOYMENT=gpt-5-mini
#   AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
#   API_KEY=<pick one>            # the key clients send as X-API-Key
```

Verify the model connection:
```bash
make check-azure        # expects: chat OK, embeddings OK dim=1536
```

---

## A. Run it LOCALLY (Docker Compose)

You still need AI Search in the cloud for retrieval (Free tier, ~€0). Provision
just that, create the indexes, and ingest the manual once:

```bash
# 1. provision AI Search (and its resource group) with Terraform
cd infra
az provider register --namespace Microsoft.Search --wait
export TF_VAR_subscription_id=$(az account show --query id -o tsv)
export TF_VAR_postgres_admin_password='unused-locally-but-required'
terraform init
terraform apply -target=azurerm_search_service.main
cd ..

# 2. point .env at the search service (endpoint from `terraform -chdir=infra output`,
#    key from: az search admin-key show ...). Set:
#   AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY

# 3. create the two indexes and ingest the manual (~1150 chunks, ~€0.005)
make search-indexes
docker compose up -d db          # local Postgres for ingestion registry
make ingest
```

Bring up the full local stack and open the console:
```bash
make up                          # db + migrate + api + ui
# in another shell, seed the demo queue and open the UI:
curl -s -X POST localhost:8000/v1/tickets/seed -H "X-API-Key: <your API_KEY>"
open http://localhost:8501       # the dashboard
```

Stop it:
```bash
make down
```

---

## B. Run it in the CLOUD (Azure Container Apps)

Provision the whole platform, deploy the three apps, and get a public URL.

```bash
# 1. provision the platform (~€19/mo while up; see docs/COST.md)
cd infra
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.OperationalInsights --wait
export TF_VAR_subscription_id=$(az account show --query id -o tsv)
export TF_VAR_postgres_admin_password='<a-strong-password>'
terraform init
terraform apply                  # review the plan, then yes (~8 min)
```

Then follow **docs/DEPLOY.md** end to end:
1. `az acr build` the three images to ACR.
2. `az keyvault secret set` the six secrets.
3. `terraform apply -var deploy_apps=true` to create the apps.
4. `az containerapp job start` the migration job.
5. Grab `terraform output api_url` / `ui_url`.

Seed the demo queue and open the console:
```bash
API_URL=$(terraform -chdir=infra output -raw api_url)
curl -s -X POST "$API_URL/v1/tickets/seed" -H "X-API-Key: <your api-key secret>"
terraform -chdir=infra output -raw ui_url    # open this in a browser
```

Tear it all down when done (stops the meter):
```bash
make infra-down
```

---

## Demo flow (for the video)

1. Open the console — the KPI row and the Jira-style ticket queue.
2. Click a critical ticket (DEMO-3, startup inhibit 0x2521).
3. Click **Resolve with Copilot** — watch triage → retrieval → synthesis →
   guardrails produce a grounded, cited resolution with a confidence score.
4. Show the citations expanding to real manual pages.
5. Show a low-coverage ticket escalating (needs human review) — the system
   knowing when it does not know.
6. (Optional) show the same resolution's trajectory in Langfuse.
7. (Optional) `DELETE /v1/tickets/{id}` — GDPR erase, then a 404.

## Common issues

| Symptom | Fix |
|---|---|
| `MissingSubscriptionRegistration` | `az provider register --namespace <ns> --wait` |
| local Postgres won't connect | a host Postgres may own port 5432; `brew services stop postgresql@14` |
| `make ui` says "up to date" | fixed (targets are `.PHONY`); pull latest |
| cold start on first cloud request | apps take ~1 min to pull images; retry |
