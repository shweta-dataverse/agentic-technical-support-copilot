# Resource group + shared naming.

data "azurerm_client_config" "current" {}

# short random suffix to make globally-unique names (storage, acr, search, kv)
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

locals {
  prefix = "${var.project}-${var.environment}"
  # names for resources that require globally-unique, alnum-only identifiers
  suffix      = random_string.suffix.result
  acr_name    = "${var.project}${var.environment}acr${local.suffix}"
  sa_name     = "${var.project}${var.environment}sa${local.suffix}"
  kv_name     = "${var.project}-${var.environment}-kv-${local.suffix}"
  search_name = "${var.project}-${var.environment}-search-${local.suffix}"
  pg_name     = "${var.project}-${var.environment}-pg-${local.suffix}"
}

resource "azurerm_resource_group" "main" {
  name     = "${local.prefix}-rg"
  location = var.location
  tags     = var.tags
}
