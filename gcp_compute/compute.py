
from gcp_compute.logger import get_logger


class GCPCompute():
    def __init__(self):
        self.log = get_logger('gcp-compute')
