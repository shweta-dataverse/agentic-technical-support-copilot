# Deploy to Azure Container Apps

Run these in order from the repo root after the base infra exists
(`terraform apply` with `deploy_apps = false`, the default). All commands use
the resource names from `terraform output`.

Set shell variables once:

```bash
ACR=copilotdevacr4hpjxf
KV=copilot-dev-kv-4hpjxf
RG=copilot-dev-rg
PG_FQDN=copilot-dev-pg-4hpjxf.postgres.database.azure.com
SEARCH=copilot-dev-search-4hpjxf
```

## 1. Build and push the three images to ACR

`az acr build` builds natively as linux/amd64 in the cloud (no local
cross-build). One command per target of the multi-stage Dockerfile:

```bash
az acr build --registry $ACR --image copilot-api:latest    --file docker/Dockerfile --target api    .
az acr build --registry $ACR --image copilot-worker:latest --file docker/Dockerfile --target worker .
az acr build --registry $ACR --image copilot-ui:latest     --file docker/Dockerfile --target ui     .
```

Verify: `az acr repository list --name $ACR -o table` shows the three repos.

## 2. Put the secrets in Key Vault

The container apps read these by reference through the managed identity.

```bash
# Azure OpenAI key (the value from your local .env)
az keyvault secret set --vault-name $KV --name azure-openai-key --value '<AZURE_OPENAI_API_KEY>'

# AI Search admin key (fetched from the service)
az keyvault secret set --vault-name $KV --name azure-search-key \
  --value "$(az search admin-key show --service-name $SEARCH --resource-group $RG --query primaryKey -o tsv)"

# database URL for the cloud Postgres (SSL required); use your PG admin password
az keyvault secret set --vault-name $KV --name database-url \
  --value "postgresql+psycopg://copilotadmin:<PG_PASSWORD>@$PG_FQDN:5432/jira_copilot?sslmode=require"

# app auth: the API key clients present, a pepper for hashing, and the webhook secret
az keyvault secret set --vault-name $KV --name api-key           --value '<choose-an-api-key>'
az keyvault secret set --vault-name $KV --name api-key-pepper    --value '<choose-a-random-pepper>'
az keyvault secret set --vault-name $KV --name jira-webhook-secret --value '<choose-a-webhook-secret>'
```

## 3. Create the container apps

Now flip the gate on and apply. Supply the Azure OpenAI endpoint (not in
Terraform because that resource was created by hand):

```bash
cd infra
export TF_VAR_azure_openai_endpoint='https://<your-openai-resource>.cognitiveservices.azure.com'
terraform apply -var deploy_apps=true
```

## 4. Migrate the cloud database

Run the one-shot migration job (runs inside Azure, reaches Postgres over the
AllowAzureServices rule):

```bash
az containerapp job start --name copilot-dev-migrate --resource-group $RG
# watch it finish:
az containerapp job execution list --name copilot-dev-migrate --resource-group $RG -o table
```

## 5. Smoke test the live system

```bash
terraform output api_url   # https://copilot-dev-api.<region>.azurecontainerapps.io
terraform output ui_url    # the Streamlit console

curl -s <api_url>/health
curl -s <api_url>/ready    # postgres + ai_search should be ok
```

Open `ui_url` in a browser and submit a ticket. That is the live demo.

## Tear down

`make infra-down` (or `terraform destroy`) removes everything. Re-deploy with
steps 1 and 3 (secrets and data persist only if you keep the base infra).
