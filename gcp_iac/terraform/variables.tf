variable "project_id" {
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

variable "instance_tags" {
  type=list(string)
  default=["web", "ssh"]
}

variable "instance_machine_type" {
  type=string
  default="e2-highcpu-2"
}

variable "boot_image" {
  type=string
  default="rocky-linux-cloud/rocky-linux-9"
}

variable "ansible_ssh_pub_key_file" {
  type=string
  description="Path to the Ansible SSH public key"
  default=""
}

variable "gcp_iac_sa_file" {
  type=string
  description="Path to the GCP service account file"
  default=""
}
