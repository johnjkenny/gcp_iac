# GCP-IaC

Google Cloud Platform Infrastructure as Code (IaC) project using Terraform and Ansible to deploy a Docker
application on a VM instance. The project is designed to be run from a local machine and uses Terraform to create a VM
instance and Ansible to configure the instance.


## Prerequisites
- GCP project access with Compute Engine API enabled
- Firewall tag `ssh` for SSH access (port 22) allowing 0.0.0/0 access (or your public IP address)
- Firewall tag `web` for HTTP access (port 80) allowing 0.0.0/0 access (or your public IP address)
- Service account with `Compute Admin` role assigned
- Service account key downloaded in JSON format.
- Python3.12 (only tested with 3.12, but prior versions might work)
- Test used `rocky9.5` for host and client OS


## Limitations
This is for demonstration purpose only. It is to showcase how to use Terraform and Ansible together to deploy a Docker
application on GCP. It is not intended for production use. It is designed to deploy a single VM instance then configure
Docker and deploy an application that consists of three containers then run a quick test to verify the application is
working. The application consists of the following containers:
- Nginx
- PHP
- MySQL


## Usage

Command Options:
```bash
giac -h             
usage: giac [-h] [-I ...] [-a] [-d]

GCP IaC Commands

options:
  -h, --help          show this help message and exit

  -I ..., --init ...  Initialize GCP IaC Environment

  -a, --apply         Apply GCP IaC Configuration

  -d, --destroy       Destroy GCP IaC Configuration
```

### Initialization

The following will walk you through the initialization process. The initialization process will create a
virtual environment, install the required packages, and create the necessary directories and files. It will also
generate a private key for SSH access to the VM instance. The private key will be stored in `gcp_env/keys`. It will
stash the service account key in the `gcp_env/keys` directory as well. It will also create a `terraform.tfvars` file in
the `gcp_env` directory. The `terraform.tfvars` file will contain the project ID to be used for the terraform deploy
state.


```bash
# Command options:
giac -I -h
usage: giac [-h] -sa SERVICEACCOUNT -p PROJECT [-F]

GCP IaC Initialization

options:
  -h, --help            show this help message and exit

  -sa SERVICEACCOUNT, --serviceAccount SERVICEACCOUNT
                        Service account path (full path to json file)

  -p PROJECT, --project PROJECT
                        GCP project ID to set as the default project

  -F, --force           Force action
```

1. Create virtual environment and install requirements:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

2. Run the init command:
```bash
giac -I -sa /home/myUser/sa.json -p my-projectID
[2025-03-29 17:01:52,911][INFO][init,53]: Successfully initialized Terraform
[2025-03-29 17:01:52,912][INFO][init,64]: Successfully initialized GCP-IaC Environment
```

### Apply Terraform State (Deploy VM and configure with Ansible)

The following command, `giac -a`, will create a VM instance in GCP using Terraform named `docker-01`. It will assign the
`ssh` and `web` firewall tags to ensure SSH and HTTP access on the public IP address of the VM instance. It will add
the user `ansible` to the meta data of the VM instance and include the public SSH key that was generated during the 
initialization step performed earlier. It will also assign a bash script to the metadata startup-script. The script
will install python3.12 on the host system to ensure no issues with Ansible. The script will then set a marker file
`startup-done.marker` to indicate that the startup script has completed. The Ansible playbook will then wait for this
marker file to be created before proceeding. Finally, it will install docker and deploy three application containers.
A unique username and password will be generated for the MySQL database and stored in the environment variables.

You can ssh to the VM instance using the `ansible` user and the private key that was generated during the
initialization step: `ssh -i gcp_env/keys/.ansible_rsa ansible@<VM_PUBLIC_IP>`

```bash
giac -a
# Example output
Applying Terraform State
Successfully applied Terraform State
  Name: docker-01, IP: 104.198.167.64
Waiting for 104.198.167.64:22 to be open
104.198.167.64:22 is not open. Retrying in 5 seconds
104.198.167.64:22 is not open. Retrying in 5 seconds
104.198.167.64:22 is open, running Ansible playbook

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
changed: [docker-01]

TASK [Install Docker CE] *******************************************************
changed: [docker-01]

TASK [Enable and start Docker service] *****************************************
changed: [docker-01]

TASK [Add users to docker group] ***********************************************
changed: [docker-01] => (item=ansible)

PLAY [Deploy Docker Compose App1 (nginx + php + mysql)] ************************

TASK [Create app directory structure] ******************************************
changed: [docker-01] => (item=web)
changed: [docker-01] => (item=php)
changed: [docker-01] => (item=mysql/db)

TASK [Copy Docker Compose file] ************************************************
changed: [docker-01]

TASK [Copy web container files] ************************************************
changed: [docker-01]

TASK [Copy php container files] ************************************************
changed: [docker-01]

TASK [Copy db container files] *************************************************
changed: [docker-01]

TASK [Copy web index file] *****************************************************
changed: [docker-01]

TASK [Write environment variables to file] *************************************
changed: [docker-01]

TASK [Set ownership of copied files] *******************************************
changed: [docker-01]

TASK [Deploy containers] *******************************************************
changed: [docker-01]

PLAY RECAP *********************************************************************
docker-01                  : ok=17   changed=14   unreachable=0    failed=0    skipped=4    rescued=0    ignored=0 
```


### Test Application
Demonstrate the application is working by running curl against the public IP address of the VM instance. The nginx
server will receive the request on port 80 and proxy the request to the PHP container. The PHP container will handle
the request and connect to the MySQL container to save the requestors IP address in the database. The returned
response will be the IP address of the requestor and a welcome message with code 200.

1. Run curl to the public IP address of the VM instance
```bash
curl 104.198.167.64
<h1>Welcome!</h1><p>Your IP 46.82.212.17 has been recorded.</p>#
```

2. Curl response received with 200 OK. Your IP should now be logged in the MySQL database on the vm instance. Verify:
```bash
# SSH to the VM instance
ssh -i gcp_env/keys/.ansible_rsa ansible@104.198.167.64
# connect to the MySQL container
docker exec -it app1-app1_db-1 mysql
select * from app1.visitors;
+----+---------------+---------------------+
| id | ip            | visited_at          |
+----+---------------+---------------------+
|  1 | 46.82.212.17 | 2025-03-29 16:49:24 |
+----+---------------+---------------------+
1 row in set (0.00 sec)
```


### Destroy Terraform State (Destroy VM)
```bash
giac -d
# Example output
Destroying Terraform State
Cleaned up ansible client directory: docker-01
Successfully destroyed Terraform State
  Removed Instance: docker-01
# Verify in GCP VM is deleted for sanity
```
