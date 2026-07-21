# Azure Service Bus, hot-path queues with native dead-lettering.
# Basic SKU (ADR): queues + DLQ are all this workload needs; idempotency is
# app-level (processed_messages), so Standard's duplicate detection and
# topics/sessions would be paid-for-unused. Upgrade line: Standard when
# topics or scheduled messages arrive.

resource "azurerm_servicebus_namespace" "main" {
  name                = "${local.prefix}-sb-${local.suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  tags                = var.tags
}

resource "azurerm_servicebus_queue" "ticket_ingest" {
  name         = "ticket-ingest"
  namespace_id = azurerm_servicebus_namespace.main.id

  # after 5 failed deliveries the message moves to the dead-letter subqueue
  max_delivery_count = 5
  lock_duration      = "PT1M"
}

resource "azurerm_servicebus_queue" "ticket_resolve" {
  name         = "ticket-resolve"
  namespace_id = azurerm_servicebus_namespace.main.id

  max_delivery_count = 5
  # resolutions run the agent graph (~1 min); hold the lock longer so a
  # working consumer is not competed with mid-flight
  lock_duration = "PT5M"
}

# data-plane access for the developer identity (az login), so make worker and
# the publisher work locally without connection strings
resource "azurerm_role_assignment" "sb_dev_data_owner" {
  scope                = azurerm_servicebus_namespace.main.id
  role_definition_name = "Azure Service Bus Data Owner"
  principal_id         = data.azurerm_client_config.current.object_id
}

# the app identity: api publishes (sender), worker consumes (receiver)
resource "azurerm_role_assignment" "app_sb_sender" {
  scope                = azurerm_servicebus_namespace.main.id
  role_definition_name = "Azure Service Bus Data Sender"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}

resource "azurerm_role_assignment" "app_sb_receiver" {
  scope                = azurerm_servicebus_namespace.main.id
  role_definition_name = "Azure Service Bus Data Receiver"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}
