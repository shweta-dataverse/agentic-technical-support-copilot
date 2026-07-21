variable "subscription_id" {
  type        = string
  description = "Azure subscription ID (also settable via ARM_SUBSCRIPTION_ID)."
}

variable "project" {
  type        = string
  default     = "copilot"
  description = "Short project prefix used in resource names (lowercase alnum)."
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Deployment environment (dev/staging/prod)."
}

variable "location" {
  type        = string
  default     = "swedencentral"
  description = "Azure region. EU region chosen for GDPR / data residency."
}

variable "postgres_admin_login" {
  type        = string
  default     = "copilotadmin"
  description = "PostgreSQL administrator login."
}

variable "postgres_admin_password" {
  type        = string
  sensitive   = true
  description = "PostgreSQL administrator password (supply via TF_VAR / tfvars, never commit)."
}

variable "tags" {
  type = map(string)
  default = {
    project    = "agentic-technical-support-copilot"
    managed_by = "terraform"
  }
  description = "Tags applied to all resources."
}

# ---------------------------------------------------------------------------
# deployment (container apps)
# ---------------------------------------------------------------------------

variable "image_tag" {
  type        = string
  default     = "latest"
  description = "Container image tag to deploy (CI sets this to the git SHA)."
}

variable "deploy_apps" {
  type        = bool
  default     = false
  description = "Create the container apps. Set true only after images are pushed to ACR and secrets are in Key Vault."
}

variable "azure_openai_endpoint" {
  type        = string
  default     = ""
  description = "Azure OpenAI resource endpoint (the hand-created resource)."
}

variable "azure_openai_deployment" {
  type        = string
  default     = "gpt-5-mini"
  description = "Chat deployment name."
}

variable "azure_openai_embedding_deployment" {
  type        = string
  default     = "text-embedding-3-small"
  description = "Embedding deployment name."
}

variable "azure_openai_api_version" {
  type        = string
  default     = "2024-12-01-preview"
  description = "Azure OpenAI API version."
}
