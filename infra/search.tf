# Azure AI Search, managed hybrid retrieval (keyword + vector + semantic
# reranker). Free tier: 50 MB, 3 indexes, enough for the demo corpus.

resource "azurerm_search_service" "main" {
  name                = local.search_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "free"
  tags                = var.tags
}
