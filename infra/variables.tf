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
