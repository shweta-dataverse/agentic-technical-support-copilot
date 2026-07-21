# Azure Database for PostgreSQL Flexible Server, system-of-record for
# tickets, resolutions, and eval-run results. Burstable B1ms (cheapest tier).

resource "azurerm_postgresql_flexible_server" "main" {
  name                          = local.pg_name
  resource_group_name           = azurerm_resource_group.main.name
  location                      = azurerm_resource_group.main.location
  version                       = "16"
  administrator_login           = var.postgres_admin_login
  administrator_password        = var.postgres_admin_password
  storage_mb                    = 32768
  sku_name                      = "B_Standard_B1ms"
  auto_grow_enabled             = true
  geo_redundant_backup_enabled  = false
  public_network_access_enabled = true
  zone                          = "1"
  tags                          = var.tags
}

resource "azurerm_postgresql_flexible_server_database" "app" {
  name      = "jira_copilot"
  server_id = azurerm_postgresql_flexible_server.main.id
  collation = "en_US.utf8"
  charset   = "UTF8"
}

# dev-only: allow other Azure services (e.g. Container Apps) to reach the server.
# Production would use a private endpoint + VNet integration instead.
resource "azurerm_postgresql_flexible_server_firewall_rule" "azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}
