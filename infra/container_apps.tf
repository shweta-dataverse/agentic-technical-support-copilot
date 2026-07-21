# The three container apps (api, ui, worker) plus a one-shot migration job.
# Gated behind var.deploy_apps so the base platform can exist first: images
# must be pushed to ACR and secrets set in Key Vault before these apply.
#
# All apps run as the user-assigned managed identity: they pull from ACR with
# it, read Key Vault secrets with it, and reach Service Bus / Storage with it.
# The only exception is the worker's KEDA queue scaler, which uses a Service
# Bus connection string (KEDA reads the queue depth to scale from zero).

locals {
  acr_login = azurerm_container_registry.main.login_server

  # non-secret config, shared by api and worker
  plain_env = [
    { name = "LLM_PROVIDER", value = "azure" },
    { name = "ENVIRONMENT", value = "production" },
    { name = "AZURE_OPENAI_ENDPOINT", value = var.azure_openai_endpoint },
    { name = "AZURE_OPENAI_API_VERSION", value = var.azure_openai_api_version },
    { name = "AZURE_OPENAI_DEPLOYMENT", value = var.azure_openai_deployment },
    { name = "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", value = var.azure_openai_embedding_deployment },
    { name = "AZURE_SEARCH_ENDPOINT", value = "https://${azurerm_search_service.main.name}.search.windows.net" },
    { name = "SERVICEBUS_NAMESPACE", value = azurerm_servicebus_namespace.main.name },
    { name = "AZURE_CLIENT_ID", value = azurerm_user_assigned_identity.app.client_id },
  ]

  # env vars sourced from Key Vault secrets
  secret_env = [
    { name = "AZURE_OPENAI_API_KEY", secret_name = "azure-openai-key" },
    { name = "AZURE_SEARCH_API_KEY", secret_name = "azure-search-key" },
    { name = "DATABASE_URL", secret_name = "database-url" },
    { name = "API_KEY", secret_name = "api-key" },
    { name = "API_KEY_PEPPER", secret_name = "api-key-pepper" },
    { name = "JIRA_WEBHOOK_SECRET", secret_name = "jira-webhook-secret" },
  ]

  kv_secrets = [
    "azure-openai-key", "azure-search-key", "database-url",
    "api-key", "api-key-pepper", "jira-webhook-secret",
  ]
}

# --- api -------------------------------------------------------------------

resource "azurerm_container_app" "api" {
  count                        = var.deploy_apps ? 1 : 0
  name                         = "${local.prefix}-api"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app.id]
  }

  registry {
    server   = local.acr_login
    identity = azurerm_user_assigned_identity.app.id
  }

  dynamic "secret" {
    for_each = toset(local.kv_secrets)
    content {
      name                = secret.value
      identity            = azurerm_user_assigned_identity.app.id
      key_vault_secret_id = "${azurerm_key_vault.main.vault_uri}secrets/${secret.value}"
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "auto"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 1
    max_replicas = 3

    container {
      name   = "api"
      image  = "${local.acr_login}/copilot-api:${var.image_tag}"
      cpu    = 0.5
      memory = "1Gi"

      dynamic "env" {
        for_each = local.plain_env
        content {
          name  = env.value.name
          value = env.value.value
        }
      }
      dynamic "env" {
        for_each = local.secret_env
        content {
          name        = env.value.name
          secret_name = env.value.secret_name
        }
      }
    }

    http_scale_rule {
      name                = "http-scale"
      concurrent_requests = 10
    }
  }
}

# --- worker (scales from zero on the resolve queue) ------------------------

resource "azurerm_container_app" "worker" {
  count                        = var.deploy_apps ? 1 : 0
  name                         = "${local.prefix}-worker"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app.id]
  }

  registry {
    server   = local.acr_login
    identity = azurerm_user_assigned_identity.app.id
  }

  dynamic "secret" {
    for_each = toset(local.kv_secrets)
    content {
      name                = secret.value
      identity            = azurerm_user_assigned_identity.app.id
      key_vault_secret_id = "${azurerm_key_vault.main.vault_uri}secrets/${secret.value}"
    }
  }

  # KEDA needs the queue depth to scale; a connection string is the simplest
  # trigger auth (the app's own data-plane access still uses managed identity)
  secret {
    name  = "servicebus-connection"
    value = azurerm_servicebus_namespace.main.default_primary_connection_string
  }

  template {
    min_replicas = 0
    max_replicas = 3

    container {
      name   = "worker"
      image  = "${local.acr_login}/copilot-worker:${var.image_tag}"
      cpu    = 0.5
      memory = "1Gi"

      dynamic "env" {
        for_each = local.plain_env
        content {
          name  = env.value.name
          value = env.value.value
        }
      }
      dynamic "env" {
        for_each = local.secret_env
        content {
          name        = env.value.name
          secret_name = env.value.secret_name
        }
      }
    }

    custom_scale_rule {
      name             = "sb-resolve-queue"
      custom_rule_type = "azure-servicebus"
      metadata = {
        queueName    = azurerm_servicebus_queue.ticket_resolve.name
        namespace    = azurerm_servicebus_namespace.main.name
        messageCount = "5"
      }
      authentication {
        secret_name       = "servicebus-connection"
        trigger_parameter = "connection"
      }
    }
  }
}

# --- ui --------------------------------------------------------------------

resource "azurerm_container_app" "ui" {
  count                        = var.deploy_apps ? 1 : 0
  name                         = "${local.prefix}-ui"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app.id]
  }

  registry {
    server   = local.acr_login
    identity = azurerm_user_assigned_identity.app.id
  }

  secret {
    name                = "api-key"
    identity            = azurerm_user_assigned_identity.app.id
    key_vault_secret_id = "${azurerm_key_vault.main.vault_uri}secrets/api-key"
  }

  ingress {
    external_enabled = true
    target_port      = 8501
    transport        = "auto"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 1
    max_replicas = 2

    container {
      name   = "ui"
      image  = "${local.acr_login}/copilot-ui:${var.image_tag}"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "COPILOT_API_URL"
        value = "https://${azurerm_container_app.api[0].ingress[0].fqdn}"
      }
      env {
        name        = "COPILOT_API_KEY"
        secret_name = "api-key"
      }
    }
  }
}

# --- migration job (run once after deploy) ---------------------------------

resource "azurerm_container_app_job" "migrate" {
  count                        = var.deploy_apps ? 1 : 0
  name                         = "${local.prefix}-migrate"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  tags                         = var.tags

  replica_timeout_in_seconds = 300
  manual_trigger_config {
    parallelism              = 1
    replica_completion_count = 1
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app.id]
  }

  registry {
    server   = local.acr_login
    identity = azurerm_user_assigned_identity.app.id
  }

  secret {
    name                = "database-url"
    identity            = azurerm_user_assigned_identity.app.id
    key_vault_secret_id = "${azurerm_key_vault.main.vault_uri}secrets/database-url"
  }

  template {
    container {
      name    = "migrate"
      image   = "${local.acr_login}/copilot-api:${var.image_tag}"
      cpu     = 0.5
      memory  = "1Gi"
      command = ["alembic", "upgrade", "head"]

      env {
        name        = "DATABASE_URL"
        secret_name = "database-url"
      }
    }
  }
}
