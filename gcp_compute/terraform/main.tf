provider "google" {
  project=var.project
  region=var.region
  credentials=file(var.credentials_file)
}

resource "random_id" "instance_suffix" {byte_length=4}

resource "random_id" "instance_username" {byte_length=4}


locals {final_ssh_user = var.ssh_user != "" ? var.ssh_user : "user-${random_id.instance_username.hex}"}

resource "google_compute_instance" "vm_instance" {
  name="${var.web_instance_prefix}-${random_id.instance_suffix.hex}"
  machine_type=var.machine_type
  zone=var.zone
  boot_disk {
    initialize_params {
      image=var.boot_image
      size=var.boot_disk_size_gb
    }
  }
  network_interface {
    network="default"
    access_config {}
  }
  metadata = {
    ssh-keys="${local.final_ssh_user}:${file(var.public_key_path)}"
    startup-script=file("${path.module}/startup.sh")
  }
  tags=var.web_tags
}
output "instance_username" {value=local.final_ssh_user}
output "instance_name" {value=google_compute_instance.vm_instance.name}
output "instance_ip" {value=google_compute_instance.vm_instance.network_interface[0].access_config[0].nat_ip}
