terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # NOTE: production uses remote state in an Azure Storage backend so the team
  # shares one state file. Kept local here for a solo project; to switch, create
  # a state storage account and uncomment:
  #
  # backend "azurerm" {
  #   resource_group_name  = "tfstate-rg"
  #   storage_account_name = "copilottfstate"
  #   container_name       = "tfstate"
  #   key                  = "copilot.tfstate"
  # }
}

provider "azurerm" {
  subscription_id = var.subscription_id
  features {}
}
