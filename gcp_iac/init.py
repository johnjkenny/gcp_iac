from pathlib import Path

from gcp_iac.iac import GCPIaC


class Init(GCPIaC):
    def __init__(self, service_account: str, project_id: str, force: bool = False):
        super().__init__()
        self.service_account = service_account
        if not Path(service_account).exists():
            raise FileNotFoundError(f'File not found: {service_account}')
        self.project_id = project_id
        self.__force = force

    def __set_service_account(self):
        path = f'{Path(__file__).parent}/gcp_env/keys/.sa.json'
        if self.__force or not Path(path).exists():
            try:
                with open(self.service_account, 'r') as file:
                    data = file.read()
                with open(path, 'w') as file:
                    file.write(data)
                return True
            except Exception:
                self.log.exception('Failed to set service account')
                return False
        return True

    def __create_project_id_file(self):
        if self.__force or not Path(self.env_vars_file).exists():
            try:
                with open(self.env_vars_file, 'w') as file:
                    file.write(f'project_id="{self.project_id}"')
                return True
            except Exception:
                self.log.exception('Failed to set project id')
            return False
        return True

    def __create_ansible_ssh_keys(self):
        name = f'{Path(__file__).parent}/gcp_env/keys/.ansible_rsa'
        if Path(name).exists():
            if self.__force:
                if not self.run_cmd(f'rm -f {name}*')[1]:
                    return False
            else:
                return True
        return self.run_cmd(f'ssh-keygen -t rsa -b 4096 -C "ansible" -f {name} -N ""')[1]

    def __initialize_terraform(self):
        try:
            self.tf.init()
            self.log.info('Successfully initialized Terraform')
            return True
        except Exception:
            self.log.exception('Failed to initialize Terraform')
            return False

    def _run(self):
        for method in [self.__set_service_account, self.__create_project_id_file, self.__create_ansible_ssh_keys,
                       self.__initialize_terraform]:
            if not method():
                return False
        self.log.info('Successfully initialized GCP-IaC Environment')
        return True
