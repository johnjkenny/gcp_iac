variable "project" {
  type=string
  default=""
}

variable "region" {
  type=string
  default="us-central1"
}

variable "zone" {
  type=string
  default="us-central1-a"
}

variable "credentials_file" {
  type=string
  default="service_account.json"
}

variable "web_instance_prefix" {
  type=string
  default="web-"
}

variable "web_tags" {
  type=list(string)
  default=["web", "ssh"]
}

variable "machine_type" {
  type=string
  default="e2-medium"
}

variable "boot_image" {
  type=string
  default="debian-cloud/debian-12"
}

variable "boot_disk_size_gb" {
  type=number
  default=20
}

variable "ssh_user" {
  type=string
  default=""
}

variable "public_key_path" {
  type=string
  default="~/.ssh/id_rsa.pub"
}
