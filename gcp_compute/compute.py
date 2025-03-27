from pathlib import Path
from logging import Logger

import ansible_runner
from python_terraform import Terraform

from gcp_compute.utils import ComputeUtils


class GCPCompute(ComputeUtils):
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

    def apply_terraform(self):
        try:
            return_code, stdout, stderr = self.tf.apply(var_file=self.env_vars_file, skip_plan=True, auto_approve=True)
            if return_code != 0:
                self.log.debug(f'Output:\n{stdout}')
                self.log.error(f'Failed to apply Terraform: {stderr}')
                return False
            outputs = self.tf.output()
            ip = outputs["instance_ip"]["value"]
            name = outputs["instance_name"]["value"]
            self.display_successful(f'Name: {name}, IP: {ip}')
        except Exception:
            self.log.exception('Failed to apply Terraform')
            return False
        return self.run_ansible_playbook(name, ip)

    def run_ansible_playbook(self, name: str, ip: str):
        inventory_content = f"[all]\n{ip} ansible_user=ansible ansible_ssh_private_key_file={self.ssh_key}\n"
        # Save inventory to a temporary file
        inventory_path = "inventory.ini"
        with open(inventory_path, "w") as f:
            f.write(inventory_content)

        result = ansible_runner.run(
            private_data_dir=".",
            playbook='playbook.yml',
            inventory=inventory_path,
            verbosity=1
        )

        if result.rc != 0:
            raise Exception("Ansible playbook failed")
