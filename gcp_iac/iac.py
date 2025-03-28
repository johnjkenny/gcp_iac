import socket
from pathlib import Path
from logging import Logger
from time import sleep

import ansible_runner
from python_terraform import Terraform

from gcp_iac.utils import IaCUtils


class GCPIaC(IaCUtils):
    def __init__(self, logger: Logger = None):
        super().__init__(logger)
        self.__tf: Terraform | None = None

    @property
    def env_vars_file(self):
        return f'{Path(__file__).parent}/gcp_env/env.tfvars'

    @property
    def ssh_key(self):
        return f'{Path(__file__).parent}/gcp_env/keys/.ansible_rsa'

    @property
    def ansible_dir(self):
        return f'{Path(__file__).parent}/ansible'

    @property
    def tf(self):
        if self.__tf is None:
            self.__tf = Terraform(working_dir=f'{Path(__file__).parent}/terraform')
        return self.__tf

    def __create_ansible_client_directory(self, client_dir: Path, name: str, ip: str):
        try:
            Path.mkdir(client_dir, parents=True, exist_ok=True)
            data = f"[all]\n{name} ansible_host={ip}\n"
            with open(f'{client_dir}/inventory.ini', 'w') as f:
                f.write(data)
            return True
        except Exception:
            self.log.exception('Failed to create client directory')
            return False

    def __create_ansible_env_vars(self):
        return {
            'ANSIBLE_CONFIG': f'{self.ansible_dir}/ansible.cfg',
            'ANSIBLE_PYTHON_INTERPRETER': '/usr/bin/python3',
            'ANSIBLE_PRIVATE_KEY_FILE': self.ssh_key,
        }

    def __is_port_open(self, ip: str, port: int = 22, timeout: int = 5, max_attempts: int = 12):
        self.display_successful(f'Waiting for {ip}:{port} to be open')
        while max_attempts > 0:
            try:
                with socket.create_connection((ip, port), timeout=timeout):
                    self.display_successful(f'{ip}:{port} is open, running Ansible playbook')
                    return True
            except (socket.timeout, ConnectionRefusedError, OSError):
                self.display_warning(f'{ip}:{port} is not open. Retrying in {timeout} seconds')
                sleep(timeout)
                max_attempts -= 1
                continue
        self.display_failed('Failed to determine if port is open')
        return False

    def apply_terraform(self):
        self.display_successful('Applying Terraform')
        try:
            return_code, _, stderr = self.tf.apply(var_file=self.env_vars_file, skip_plan=True, auto_approve=True)
            if return_code != 0:
                self.display_failed(f'Failed to apply Terraform: {stderr}')
                return False
            outputs = self.tf.output()
            ip = outputs["instance_ip"]["value"]
            name = outputs["instance_name"]["value"]
            self.display_successful(f'Successfully applied Terraform\nName: {name}, IP: {ip}')
        except Exception:
            self.log.exception('Failed to apply Terraform')
            return False
        if self.__is_port_open(ip):
            return self.run_ansible_playbook(name, ip)
        self.log.error('Failed to configure system')
        return False

    def run_ansible_playbook(self, name: str, ip: str):
        client_dir = Path(f'{self.ansible_dir}/clients/{name}')
        self.__create_ansible_client_directory(client_dir, name, ip)
        result = ansible_runner.run(
            private_data_dir=client_dir.absolute(),
            playbook=f'{self.ansible_dir}/playbooks/install_docker_and_deploy_nginx.yml',
            inventory=f'{client_dir}/inventory.ini',
            artifact_dir=f'{client_dir}/artifacts',
            envvars=self.__create_ansible_env_vars())
        if result.rc == 0:
            self.display_successful('Successfully configured system with ansible')
            return True
        self.log.error(f'Failed to run Ansible playbook: {result.status}')
        return False
