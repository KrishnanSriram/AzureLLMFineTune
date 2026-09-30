output "resource_group" {
  value = azapi_resource.rg.name
}

output "foundry_name" {
  value = azapi_resource.foundry.name
}

output "project_name" {
  value = azapi_resource.project.name
}

output "endpoint" {
  description = "AZURE_OPENAI_ENDPOINT for the Python scripts."
  value       = "https://${local.subdomain}.openai.azure.com/"
}

output "base_deployment" {
  description = "BASE_DEPLOYMENT for the Python scripts."
  value       = azapi_resource.base_deployment.name
}

output "api_key" {
  description = "AZURE_OPENAI_API_KEY. Read with: terraform output -raw api_key"
  value       = azapi_resource_action.keys.output.key1
  sensitive   = true
}
