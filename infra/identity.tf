# User-assigned managed identity — the app's passwordless identity.
# It is granted least-privilege access to ACR (pull), Key Vault (read secrets),
# and Storage, so no keys/connection strings live in app config.

resource "azurerm_user_assigned_identity" "app" {
  name                = "${local.prefix}-app-mi"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = var.tags
}
