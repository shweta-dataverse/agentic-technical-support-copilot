# CI/CD

Three GitHub Actions workflows:

| Workflow | Trigger | Does |
|---|---|---|
| `ci.yml` | every PR + push to main | ruff, mypy, pytest, docker builds (api/worker/ui), terraform fmt + validate |
| `eval.yml` | PRs touching prompts / agents / retrieval | runs the golden-dataset eval gate; fails on a metric regression |
| `cd.yml` | push to main (src/docker/prompts) + manual | build images tagged by SHA, push to ACR, roll each container app, smoke test, roll back api on failure |

Deploy authenticates to Azure with **OIDC**: GitHub gets a short-lived token
from a federated credential, so no cloud secret is stored in the repo.

## One-time OIDC setup

Create an Entra ID app, trust this repo's main branch, and give it the roles
the deploy needs. Run once:

```bash
RG=copilot-dev-rg
SUB=$(az account show --query id -o tsv)
TENANT=$(az account show --query tenantId -o tsv)
REPO=shweta-dataverse/agentic-technical-support-copilot   # owner/repo

# 1. app registration
APP_ID=$(az ad app create --display-name copilot-gh-deploy --query appId -o tsv)
az ad sp create --id "$APP_ID"

# 2. federated credential trusting pushes to main
az ad app federated-credential create --id "$APP_ID" --parameters "{
  \"name\": \"gh-main\",
  \"issuer\": \"https://token.actions.githubusercontent.com\",
  \"subject\": \"repo:$REPO:ref:refs/heads/main\",
  \"audiences\": [\"api://AzureADTokenExchange\"]
}"

# 3. roles: push images and manage container apps in the resource group
az role assignment create --assignee "$APP_ID" --role "AcrPush" \
  --scope "/subscriptions/$SUB/resourceGroups/$RG"
az role assignment create --assignee "$APP_ID" --role "Contributor" \
  --scope "/subscriptions/$SUB/resourceGroups/$RG"

echo "AZURE_CLIENT_ID=$APP_ID"
echo "AZURE_TENANT_ID=$TENANT"
echo "AZURE_SUBSCRIPTION_ID=$SUB"
```

## GitHub secrets and variables

In the repo: Settings, Secrets and variables, Actions.

Secrets:
- `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` (from above)
- for the eval gate: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`,
  `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_API_KEY`

Variables:
- `AZURE_OPENAI_DEPLOYMENT` = gpt-5-mini
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` = text-embedding-3-small

## Verifying

- Open a PR that weakens a prompt to see `eval.yml` block the merge.
- Merge to main (or run `cd.yml` via "Run workflow") to see the deploy roll
  the apps and smoke-test.
