resource "random_string" "suffix" {
  length  = 5
  special = false
  upper   = false
}

locals {
  suffix        = random_string.suffix.result
  foundry_name  = "${var.name_prefix}-foundry-${local.suffix}"
  subdomain     = "${var.name_prefix}foundry${local.suffix}"
  budget_start  = formatdate("YYYY-MM-01'T'00:00:00Z", plantimestamp())
}

# 1. Resource group -- delete this one thing to clean up everything.
resource "azapi_resource" "rg" {
  type     = "Microsoft.Resources/resourceGroups@2021-04-01"
  name     = "rg-${var.name_prefix}-${local.suffix}"
  location = var.location
}

# 2. Foundry resource (AIServices account with project management enabled).
resource "azapi_resource" "foundry" {
  type                      = "Microsoft.CognitiveServices/accounts@2025-06-01"
  name                      = local.foundry_name
  parent_id                 = azapi_resource.rg.id
  location                  = var.location
  schema_validation_enabled = false

  body = {
    kind = "AIServices"
    sku  = { name = "S0" }
    identity = { type = "SystemAssigned" }
    properties = {
      allowProjectManagement = true
      customSubDomainName    = local.subdomain
      disableLocalAuth       = false # keep API keys on so test_model.py works
      publicNetworkAccess    = "Enabled"
    }
  }
}

# 3. Foundry project (where fine-tuning jobs show up in the portal).
resource "azapi_resource" "project" {
  type                      = "Microsoft.CognitiveServices/accounts/projects@2025-06-01"
  name                      = "${var.name_prefix}-project"
  parent_id                 = azapi_resource.foundry.id
  location                  = var.location
  schema_validation_enabled = false

  body = {
    identity = { type = "SystemAssigned" }
    properties = {
      displayName = "Fine-tuning demo"
      description = "Northwind Bikes fine-tuning experiment"
    }
  }
}

# 4. Base model deployment. Global Standard = pay per token, no hourly fee.
resource "azapi_resource" "base_deployment" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2024-10-01"
  name      = var.base_deployment_name
  parent_id = azapi_resource.foundry.id

  # The account allows one change at a time; wait for the project to finish.
  depends_on = [azapi_resource.project]

  body = {
    sku = {
      name     = "GlobalStandard"
      capacity = var.deployment_capacity
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = var.base_model_name
        version = var.base_model_version
      }
      versionUpgradeOption = "NoAutoUpgrade"
    }
  }
}

# API key, exposed as a sensitive output for the Python scripts.
resource "azapi_resource_action" "keys" {
  type                   = "Microsoft.CognitiveServices/accounts@2025-06-01"
  resource_id            = azapi_resource.foundry.id
  action                 = "listKeys"
  method                 = "POST"
  response_export_values = ["key1"]
}

# 5. Optional monthly budget alert on the resource group (80% actual, 100% forecast).
resource "azapi_resource" "budget" {
  count     = var.budget_alert_email == "" ? 0 : 1
  type      = "Microsoft.Consumption/budgets@2023-05-01"
  name      = "budget-${var.name_prefix}"
  parent_id = azapi_resource.rg.id

  body = {
    properties = {
      category   = "Cost"
      amount     = var.budget_amount
      timeGrain  = "Monthly"
      timePeriod = { startDate = local.budget_start }
      notifications = {
        actual80 = {
          enabled       = true
          operator      = "GreaterThan"
          threshold     = 80
          thresholdType = "Actual"
          contactEmails = [var.budget_alert_email]
        }
        forecast100 = {
          enabled       = true
          operator      = "GreaterThan"
          threshold     = 100
          thresholdType = "Forecasted"
          contactEmails = [var.budget_alert_email]
        }
      }
    }
  }

  # Start date is computed at plan time; don't churn it on later applies.
  lifecycle {
    ignore_changes = [body]
  }
}
