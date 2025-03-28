# GCP-IaC

Google Cloud Platform Infrastructure as Code (IaC) project using Terraform and Ansible to deploy a Docker
application on a VM instance. The project is designed to be run from a local machine and uses Terraform to create a VM
instance and Ansible to configure the instance.


## Prerequisites
- GCP project access with Compute Engine API enabled
- Firewall tag `ssh` for SSH access (port 22) allowing 0.0.0/0 access (or your public IP address for higher security)
- Firewall tag `web` for HTTP access (port 80) allowing 0.0.0/0 access (or your public IP address for higher security)
- Service account with `Compute Admin` role assigned
- Service account key downloaded in JSON format.
- Python3.12 (only tested with 3.12, but prior versions might work)


## Limitations
This is for demonstration purpose only. It is to showcase how to use Terraform and Ansible together to deploy a Docker
application on GCP. It is not intended for production use. It is designed to deploy a single VM instance then configure
Docker and deploy an application that consists of three containers then run a quick test to verify the application is
working. The application consists of the following containers:
- Nginx
- PHP
- MySQL

The test involves running curl against port 80 of the VM instance. This will then hit the nginx container which will
proxy the request to the PHP container. The PHP container will then connect to the MySQL container to save the
requestors IP address in the database. The returned response will be the IP address of the requestor and a welcome
message with code 200.


## Apply Terraform State (Deploy VM and configure with Ansible)
```bash
giac -a
# Example output
Applying Terraform State
Successfully applied Terraform State
  Name: docker-01, IP: 34.35.75.210
Waiting for 34.35.75.210:22 to be open
34.35.75.210:22 is not open. Retrying in 5 seconds
34.35.75.210:22 is not open. Retrying in 5 seconds
34.35.75.210:22 is open, running Ansible playbook

PLAY [Wait for startup-done.marker on target VM] *******************************

TASK [Wait for startup script marker file] *************************************
ok: [docker-01]

TASK [Success marker found] ****************************************************
ok: [docker-01] => {
    "msg": "Startup completed — marker file detected."
}

PLAY [Install and configure Docker] ********************************************

TASK [Gathering Facts] *********************************************************
ok: [docker-01]

TASK [Install dependencies (YUM/DNF)] ******************************************
changed: [docker-01]

TASK [Set up Docker repo on RedHat-family systems] *****************************
[WARNING]: Module remote_tmp /root/.ansible/tmp did not exist and was created
with a mode of 0700, this may cause issues when running as another user. To
avoid this, create the remote_tmp dir with the correct permissions manually
changed: [docker-01]

TASK [Install Docker CE] *******************************************************
changed: [docker-01]

TASK [Enable and start Docker service] *****************************************
changed: [docker-01]

TASK [Add users to docker group] ***********************************************
changed: [docker-01] => (item=ansible)

PLAY [Deploy Docker Compose App (PHP nginx + mysql)] ***************************

TASK [Create app directory] ****************************************************
changed: [docker-01]

TASK [Write environment variables to file] *************************************
changed: [docker-01]

TASK [Create web data directory] ***********************************************
changed: [docker-01]

TASK [Create db data directory] ************************************************
changed: [docker-01]

TASK [Create db directory] *****************************************************
changed: [docker-01]

TASK [Copy Docker Compose file] ************************************************
changed: [docker-01]

TASK [Copy web nginx.conf file] ************************************************
changed: [docker-01]

TASK [Copy web index.php file] *************************************************
changed: [docker-01]

TASK [Copy web dockerfile] *****************************************************
changed: [docker-01]

TASK [Copy db init.sql file] ***************************************************
changed: [docker-01]

TASK [Copy db dockerfile] ******************************************************
changed: [docker-01]

TASK [Copy db entrypoint file] *************************************************
changed: [docker-01]

TASK [Bring up containers using Docker Compose] ********************************
changed: [docker-01]

PLAY RECAP *********************************************************************
docker-01                  : ok=21   changed=18   unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
```


## Destroy Terraform State (Destroy VM)
```bash
giac -d
# Example output
Destroying Terraform State
Cleaned up ansible client directory: docker-01
Successfully destroyed Terraform State
  Removed Instance: docker-01
```
