output "resource_group" {
  value = azurerm_resource_group.main.name
}

output "acr_login_server" {
  value = azurerm_container_registry.main.login_server
}

output "storage_account" {
  value = azurerm_storage_account.main.name
}

output "search_endpoint" {
  value = "https://${azurerm_search_service.main.name}.search.windows.net"
}

output "postgres_fqdn" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}

output "app_identity_client_id" {
  value       = azurerm_user_assigned_identity.app.client_id
  description = "Client ID the app uses for passwordless auth (AZURE_CLIENT_ID)."
}

output "app_insights_connection_string" {
  value     = azurerm_application_insights.main.connection_string
  sensitive = true
}

output "key_vault_uri" {
  value = azurerm_key_vault.main.vault_uri
}

output "container_app_environment_id" {
  value = azurerm_container_app_environment.main.id
}

output "servicebus_namespace" {
  value = azurerm_servicebus_namespace.main.name
}

output "api_url" {
  value       = var.deploy_apps ? "https://${azurerm_container_app.api[0].ingress[0].fqdn}" : ""
  description = "Public URL of the deployed API (empty until deploy_apps=true)."
}

output "ui_url" {
  value       = var.deploy_apps ? "https://${azurerm_container_app.ui[0].ingress[0].fqdn}" : ""
  description = "Public URL of the deployed Streamlit console."
}
