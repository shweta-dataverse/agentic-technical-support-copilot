# Infrastructure (Terraform)

Provisions the Azure platform for the Co-Pilot: registry, storage, secrets,
identity, observability, PostgreSQL, and Azure AI Search — everything except the
hand-created Azure OpenAI resource (consumed via config).

## What it creates

| Resource | Purpose | Tier / cost |
|---|---|---|
| Resource group | Container for everything | free |
| Log Analytics + Application Insights | App logs / traces / metrics | free tier |
| Storage account (ADLS Gen2) | Raw PDFs, datasets, MLflow artifacts | ~pennies |
| Container Registry (Basic) | App image built in CI | ~$5/mo |
| User-assigned Managed Identity | Passwordless auth to ACR / Key Vault / Storage | free |
| Key Vault (RBAC) | OpenAI key, PG password, search key | ~free |
| PostgreSQL Flexible Server (B1ms) | Tickets / resolutions / eval results | ~$12/mo |
| Azure AI Search (Free) | Hybrid retrieval (keyword + vector + semantic) | free |

Estimated burn: **< ~$20/mo** — comfortably inside the $200 / 30-day credit.

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/downloads) >= 1.6
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli), then `az login`
- Register the resource providers this stack uses (once per subscription; newer
  ones like Container Apps are not registered by default):

  ```bash
  az provider register --namespace Microsoft.App --wait
  az provider register --namespace Microsoft.OperationalInsights --wait
  ```

  A first apply on a fresh subscription otherwise fails with
  `409 MissingSubscriptionRegistration`.

## Usage

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # fill in subscription_id + a strong PG password
terraform init
terraform plan       # review what will be created
terraform apply      # provision (costs money — review first)
```

Get outputs later with `terraform output` (e.g. `terraform output acr_login_server`).

## Design notes (interview talking points)

- **Passwordless auth:** the app authenticates to ACR, Key Vault, and Storage
  via a user-assigned **Managed Identity** with least-privilege role assignments
  — no keys or connection strings in app config.
- **Secrets in Key Vault:** the deployer gets `Key Vault Secrets Officer`; the
  app identity only gets `Key Vault Secrets User` (read).
- **Dev vs prod:** this uses public network access + a broad firewall rule for
  simplicity. Production would use private endpoints + VNet integration and a
  remote Terraform state backend (see the commented block in `versions.tf`).

## Teardown

```bash
terraform destroy
```
