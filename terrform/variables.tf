variable "subscription_id" {
  description = "Azure subscription ID to deploy into."
  type        = string
}

variable "location" {
  description = "Region. North Central US and Sweden Central support gpt-4.1-nano fine-tuning."
  type        = string
  default     = "northcentralus"
}

variable "name_prefix" {
  description = "Short prefix for resource names (lowercase letters/numbers)."
  type        = string
  default     = "ftdemo"
}

variable "base_model_name" {
  description = "Base model to deploy (must be fine-tunable)."
  type        = string
  default     = "gpt-4.1-nano"
}

variable "base_model_version" {
  type    = string
  default = "2025-04-14"
}

variable "base_deployment_name" {
  description = "Deployment name your scripts will call (BASE_DEPLOYMENT)."
  type        = string
  default     = "gpt-4.1-nano-base"
}

variable "deployment_capacity" {
  description = "Rate limit in thousands of tokens per minute. Pay-per-token, so this doesn't add cost."
  type        = number
  default     = 10
}

variable "budget_amount" {
  description = "Monthly budget (USD) for the resource group. Alerts only; it does not stop spending."
  type        = number
  default     = 10
}

variable "budget_alert_email" {
  description = "Email for budget alerts. Leave empty to skip creating the budget."
  type        = string
  default     = ""
}
