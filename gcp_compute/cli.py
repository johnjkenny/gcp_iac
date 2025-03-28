from argparse import REMAINDER

from gcp_compute.arg_parser import ArgParser
from gcp_compute.compute import GCPCompute


def parse_parent_args(args: dict):
    if args.get('init'):
        return compute_init(args['init'])
    if args.get('run'):
        return compute_run(args['run'])
    return True


def compute_parent():
    args = ArgParser('GCP Compute Commands', None, {
        'init': {
            'short': 'I',
            'help': 'Initialize GCP Compute Environment (gcompute-init)',
            'nargs': REMAINDER
        },
        'configs': {
            'short': 'c',
            'help': 'Manage GCP Compute Deploy Configurations (gcompute-configs)',
            'nargs': REMAINDER
        },
        'run': {
            'short': 'r',
            'help': 'Run GCP Compute Deploy Configurations (gcompute-run)',
            'nargs': REMAINDER
        },
        'destroy': {
            'short': 'd',
            'help': 'Destroy GCP Compute Systems (gcompute-destroy)',
            'nargs': REMAINDER
        },
    }).set_arguments()
    if not parse_parent_args(args):
        exit(1)
    exit(0)


def parse_init_args(args: dict):
    if args.get('serviceAccount') and args.get('project'):
        from gcp_compute.init import Init
        return Init(args['serviceAccount'], args['project'], args['force'])._run()
    return True


def compute_init(parent_args: list = None):
    args = ArgParser('GCP Compute Initialization', parent_args, {
        'serviceAccount': {
            'short': 'sa',
            'help': 'Service account path (full path to json file)',
            'required': True,
        },
        'project': {
            'short': 'p',
            'help': 'GCP project ID to set as the default project',
            'required': True,
        },
        'force': {
            'short': 'F',
            'help': 'Force action',
            'action': 'store_true',
        }
    }).set_arguments()
    if not parse_init_args(args):
        exit(1)
    exit(0)


def parse_run_args(args: dict):
    if args.get('test'):
        # GCPCompute().destroy_terraform()
        return GCPCompute().apply_terraform()
    return True


def compute_run(parent_args: list = None):
    args = ArgParser('GCP Compute Run', parent_args, {
        'force': {
            'short': 'F',
            'help': 'Force action',
            'action': 'store_true',
        },
        'test': {
            'short': 't',
            'help': 'Test run',
            'action': 'store_true'
        }
    }).set_arguments()
    if not parse_run_args(args):
        exit(1)
    exit(0)
