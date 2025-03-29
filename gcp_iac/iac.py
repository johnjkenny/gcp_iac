import socket
from pathlib import Path
from logging import Logger
from time import sleep
from json import loads
from subprocess import run

import ansible_runner
from python_terraform import Terraform

from gcp_iac.logger import get_logger
from gcp_iac.color import Color


class GCPIaC():
    def __init__(self, logger: Logger = None):
        """GCP IaC class to manage GCP infrastructure as code using Terraform and Ansible.

        Args:
            logger (Logger, optional): logging object to use. Defaults to None.
        """
        self.log = logger or get_logger('gcp-iac')
        self.__tf: Terraform | None = None

    @property
    def env_vars_file(self) -> str:
        """Get the path to the Terraform environment variables file

        Returns:
            str: Path to the environment variables file
        """
        return f'{Path(__file__).parent}/gcp_env/env.tfvars'

    @property
    def ssh_key(self) -> str:
        """Get the path to the SSH key file for Ansible

        Returns:
            str: Path to the SSH key file
        """
        return f'{Path(__file__).parent}/gcp_env/keys/.ansible_rsa'

    @property
    def ansible_dir(self) -> str:
        """Get the path to the Ansible directory

        Returns:
            str: Path to the Ansible directory
        """
        return f'{Path(__file__).parent}/ansible'

    @property
    def tf(self) -> Terraform:
        """Get the Terraform object

        Returns:
            Terraform: Terraform object
        """
        if self.__tf is None:
            self.__tf = Terraform(working_dir=f'{Path(__file__).parent}/terraform')
        return self.__tf

    @property
    def ansible_env_vars(self) -> dict:
        """Get Ansible environment variables

        Returns:
            dict: Ansible environment variables
        """
        return {
            'ANSIBLE_CONFIG': f'{self.ansible_dir}/ansible.cfg',
            'ANSIBLE_PYTHON_INTERPRETER': '/usr/bin/python3',
            'ANSIBLE_PRIVATE_KEY_FILE': self.ssh_key,
        }

    @staticmethod
    def display_successful(msg: str) -> None:
        """Display a successful message to console in green

        Args:
            msg (str): Message to display
        """
        Color().print_message(msg, 'green')

    @staticmethod
    def display_failed(msg: str) -> None:
        """Display a failed message to console in red

        Args:
            msg (str): Message to display
        """
        Color().print_message(msg, 'red')

    @staticmethod
    def display_warning(msg: str) -> None:
        """Display a warning message to console in yellow

        Args:
            msg (str): Message to display
        """
        Color().print_message(msg, 'yellow')

    def run_cmd(self, cmd: str, ignore_error: bool = False, log_output: bool = False) -> tuple:
        """Run a command and return the output

        Args:
            cmd (str): Command to run
            ignore_error (bool, optional): ignore errors. Defaults to False
            log_output (bool, optional): Log command output. Defaults to False.

        Returns:
            tuple: (stdout, True. '') on success or (stdout, False, error) on failure
        """
        state = True
        error = ''
        output = run(cmd, shell=True, capture_output=True, text=True)
        if output.returncode != 0:
            state = False
            error = output.stderr
            if not ignore_error:
                self.log.error(f'Command: {cmd}\nExit Code: {output.returncode}\nError: {error}')
                return '', state, error
        stdout = output.stdout
        if log_output:
            self.log.info(f'Command: {cmd}\nOutput: {stdout}')
        return stdout, state, error

    def __create_ansible_client_directory(self, client_dir: Path, name: str, ip: str) -> bool:
        """Create the Ansible client directory and inventory file

        Args:
            client_dir (Path): Path to the client directory
            name (str): client name
            ip (str): client IP address

        Returns:
            bool: True on success, False otherwise
        """
        try:
            Path.mkdir(client_dir, parents=True, exist_ok=True)
            data = f"[all]\n{name} ansible_host={ip}\n"
            with open(f'{client_dir}/inventory.ini', 'w') as f:
                f.write(data)
            return True
        except Exception:
            self.log.exception('Failed to create client directory')
            return False

    def __is_port_open(self, ip: str, port: int = 22, timeout: int = 5, max_attempts: int = 12) -> bool:
        """Check if a port is open on a given IP address. Will check for 1 minute before giving up with the default
        timeout and max attempts set.

        Args:
            ip (str): ip address to check
            port (int, optional): port to check. Defaults to 22.
            timeout (int, optional): timeout between checks. Defaults to 5.
            max_attempts (int, optional): max attempts before giving up. Defaults to 12

        Returns:
            bool: True if the port is open, False otherwise
        """
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

    def __cleanup_ansible_client_dir(self, client_name: str) -> bool:
        """Clean up the Ansible client directory by removing it when the VM is destroyed.

        Args:
            client_name (str): name of the client to clean up

        Returns:
            bool: True on success, False otherwise
        """
        path = Path(self.ansible_dir + f'/clients/{client_name}')
        if path.exists():
            if self.run_cmd(f'rm -rf {path}')[1]:
                self.display_successful(f'Cleaned up ansible client directory: {client_name}')
            else:
                return False
        return True

    def __plan_tf_destroy(self) -> dict:
        """Plan the Terraform destroy operation and return the plan data. This is needed to get the VM name of the VM
        that will be destroyed so we can clean up the Ansible client directory.

        Returns:
            dict: plan data or empty dict on failure
        """
        try:
            rsp = self.tf.plan(var_file=self.env_vars_file, destroy=True, out='tfplan')
            if rsp[2]:
                self.display_failed(f'Failed to plan Terraform destroy: {rsp[2]}')
                return {}
        except Exception:
            self.log.exception('Failed to plan Terraform destroy')
            return {}
        return self.__get_tf_plan_data()

    def __get_tf_plan_data(self) -> dict:
        """Get the Terraform plan data from the tfplan file and load the json str to dict format

        Returns:
            dict: Terraform plan data or empty dict on failure
        """
        try:
            return_code, plan_json, stderr = self.tf.show('tfplan', json=True)
            if return_code != 0:
                self.display_failed(f'Failed to get Terraform plan data: {stderr}')
                return {}
            return loads(plan_json)
        except Exception:
            self.log.exception('Failed to get Terraform plan data')
            return {}

    def __destroy_tf(self) -> bool:
        """Destroy the Terraform state (Delete the VM in GCP)

        Returns:
            bool: True on success, False otherwise
        """
        try:
            rsp = self.tf.cmd('destroy', f'-var-file={self.env_vars_file}', '-auto-approve')
            if rsp[0] != 0:
                self.display_failed(f'Failed to destroy Terraform: {rsp[2]}')
                return False
            return True
        except Exception:
            self.log.exception('Failed to destroy Terraform')
            return False

    def __display_tf_destroy_changes(self, plan: dict) -> None:
        """Display the changes that will be made by the Terraform destroy operation.

        Args:
            plan (dict): Terraform plan data

        Returns:
            None
        """
        payload = 'Successfully destroyed Terraform State\n'
        for change in plan.get('resource_changes', []):
            change = change.get('change', {})
            if change.get('actions', []) == ['delete']:
                name = change.get('before', {}).get('name', '')
                if name:
                    if not self.__cleanup_ansible_client_dir(name):
                        return False
                    payload += f"  Removed Instance: {name}\n"
        self.display_successful(payload)

    def __run_ansible_playbook(self, name: str, ip: str) -> bool:
        """Run the Ansible playbook to configure the VM. This will configure the VM with Docker and deploy app1

        Args:
            name (str): name of the VM
            ip (str): IP address of the VM

        Returns:
            bool: True on success, False otherwise
        """
        client_dir = Path(f'{self.ansible_dir}/clients/{name}')
        self.__create_ansible_client_directory(client_dir, name, ip)
        result = ansible_runner.run(
            private_data_dir=client_dir.absolute(),
            playbook=f'{self.ansible_dir}/playbooks/configure_host_and_deploy_app.yml',
            inventory=f'{client_dir}/inventory.ini',
            artifact_dir=f'{client_dir}/artifacts',
            envvars=self.ansible_env_vars)
        if result.rc == 0:
            return True
        self.log.error(f'Failed to run Ansible playbook: {result.status}')
        return False

    def destroy_terraform(self) -> bool:
        """Destroy the Terraform state (Delete the VM in GCP) and clean up the Ansible client directory. Display what
        changed have been made to the user on console.

        Returns:
            bool: True on success, False otherwise
        """
        self.display_successful('Destroying Terraform State')
        plan = self.__plan_tf_destroy()
        if not plan:
            return False
        if not self.__destroy_tf():
            return False
        self.__display_tf_destroy_changes(plan)
        return True

    def apply_terraform(self) -> bool:
        """Apply the Terraform state (Create the VM in GCP) and run the Ansible playbook to configure the VM.

        Returns:
            bool: True on success, False otherwise
        """
        self.display_successful('Applying Terraform State')
        try:
            self.tf.destroy()
            return_code, _, stderr = self.tf.apply(var_file=self.env_vars_file, skip_plan=True, auto_approve=True)
            if return_code != 0:
                self.display_failed(f'Failed to apply Terraform: {stderr}')
                return False
            outputs = self.tf.output()
            ip = outputs["instance_ip"]["value"]
            name = outputs["instance_name"]["value"]
            self.display_successful(f'Successfully applied Terraform State\n  Name: {name}, IP: {ip}')
        except Exception:
            self.log.exception('Failed to apply Terraform')
            return False
        if self.__is_port_open(ip):
            return self.__run_ansible_playbook(name, ip)
        self.log.error('Failed to configure system')
        return False


class Init(GCPIaC):
    def __init__(self, service_account: str, project_id: str, force: bool = False):
        """Initialize the GCP IaC environment by setting up the service account and project ID.
        This class also creates the necessary SSH keys for Ansible and initializes Terraform.

        Args:
            service_account (str): Path to the service account JSON file
            project_id (str): GCP project ID
            force (bool, optional): force action. Defaults to False.

        Raises:
            FileNotFoundError: if the service account file does not exist
        """
        super().__init__()
        self.service_account = service_account
        if not Path(service_account).exists():
            raise FileNotFoundError(f'File not found: {service_account}')
        self.project_id = project_id
        self.__force = force

    def __set_service_account(self) -> bool:
        """Set the service account JSON file to the default location for Terraform config var to use

        Returns:
            bool: True on success, False otherwise
        """
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

    def __create_project_id_file(self) -> bool:
        """Create a file with the project ID to be used by Terraform vars

        Returns:
            bool: True on success, False otherwise
        """
        if self.__force or not Path(self.env_vars_file).exists():
            try:
                with open(self.env_vars_file, 'w') as file:
                    file.write(f'project_id="{self.project_id}"')
                return True
            except Exception:
                self.log.exception('Failed to set project id')
            return False
        return True

    def __create_ansible_ssh_keys(self) -> bool:
        """Create SSH keys for Ansible to use to connect to the GCP instance

        Returns:
            bool: True on success, False otherwise
        """
        name = f'{Path(__file__).parent}/gcp_env/keys/.ansible_rsa'
        if Path(name).exists():
            if self.__force:
                if not self.run_cmd(f'rm -f {name}*')[1]:
                    return False
            else:
                return True
        return self.run_cmd(f'ssh-keygen -t rsa -b 4096 -C "ansible" -f {name} -N ""')[1]

    def __initialize_terraform(self) -> bool:
        """Initialize Terraform by running the init command

        Returns:
            bool: True on success, False otherwise
        """
        try:
            self.tf.init()
            self.log.info('Successfully initialized Terraform')
            return True
        except Exception:
            self.log.exception('Failed to initialize Terraform')
            return False

    def _run(self) -> bool:
        """Run the initialization process for GCP IaC

        Returns:
            bool: True on success, False otherwise
        """
        for method in [self.__set_service_account, self.__create_project_id_file, self.__create_ansible_ssh_keys,
                       self.__initialize_terraform]:
            if not method():
                return False
        self.log.info('Successfully initialized GCP-IaC Environment')
        return True
