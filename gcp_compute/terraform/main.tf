terraform {
  required_version = ">= 1.3"
  required_providers {
    google = {
      source  = "hashicorp/google"
    }
  }
}

locals {
  resolved_sa_file = (
    var.gcp_compute_sa_file != "" ?
    var.gcp_compute_sa_file: "${path.module}/../gcp_env/keys/.sa.json"
  )
}

locals {
  resolved_ansible_pubkey = (
    var.ansible_ssh_pub_key_file != "" ?
    var.ansible_ssh_pub_key_file: "${path.module}/../gcp_env/keys/.ansible_rsa.pub"
  )
}

provider "google" {
  project=var.project_id
  region=var.region
  credentials=file(local.resolved_sa_file)
}

resource "random_id" "instance_suffix" {byte_length=4}

resource "google_compute_instance" "vm_instance" {
  name="docker-01"
  machine_type=var.instance_machine_type
  zone=var.zone
  boot_disk {
    initialize_params {image=var.boot_image}
  }
  network_interface {
    network="default"
    access_config {}
  }
  metadata = {
    ssh-keys="ansible:${file(local.resolved_ansible_pubkey)}"
    startup-script=file("${path.module}/startup.sh")
  }
  tags=var.instance_tags
}

output "instance_name" {value=google_compute_instance.vm_instance.name}

output "instance_ip" {value=google_compute_instance.vm_instance.network_interface[0].access_config[0].nat_ip}
