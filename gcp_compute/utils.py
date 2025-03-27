from logging import Logger
from subprocess import run

from gcp_compute.logger import get_logger
from gcp_compute.color import Color


class ComputeUtils():
    def __init__(self, logger: Logger = None):
        self.log = logger or get_logger('gcp-compute')

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
