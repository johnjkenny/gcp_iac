from argparse import REMAINDER

from gcp_iac.arg_parser import ArgParser
from gcp_iac.iac import GCPIaC


def parse_parent_args(args: dict):
    if args.get('init'):
        return iac_init(args['init'])
    if args.get('run'):
        return iac_run(args['run'])
    return True


def iac_parent():
    args = ArgParser('GCP IaC Commands', None, {
        'init': {
            'short': 'I',
            'help': 'Initialize GCP IaC Environment (giac-init)',
            'nargs': REMAINDER
        },
        'configs': {
            'short': 'c',
            'help': 'Manage GCP IaC Deploy Configurations (giac-configs)',
            'nargs': REMAINDER
        },
        'run': {
            'short': 'r',
            'help': 'Run GCP IaC Deploy Configurations (giac-run)',
            'nargs': REMAINDER
        },
        'destroy': {
            'short': 'd',
            'help': 'Destroy GCP IaC Systems (giac-destroy)',
            'nargs': REMAINDER
        },
    }).set_arguments()
    if not parse_parent_args(args):
        exit(1)
    exit(0)


def parse_init_args(args: dict):
    if args.get('serviceAccount') and args.get('project'):
        from gcp_iac.init import Init
        return Init(args['serviceAccount'], args['project'], args['force'])._run()
    return True


def iac_init(parent_args: list = None):
    args = ArgParser('GCP IaC Initialization', parent_args, {
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
        return GCPIaC().apply_terraform()
    return True


def iac_run(parent_args: list = None):
    args = ArgParser('GCP IaC Run', parent_args, {
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
