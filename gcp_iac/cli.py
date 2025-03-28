from argparse import REMAINDER

from gcp_iac.arg_parser import ArgParser
from gcp_iac.iac import GCPIaC


def parse_parent_args(args: dict):
    if args.get('init'):
        return iac_init(args['init'])
    if args.get('apply'):
        return GCPIaC().apply_terraform()
    if args.get('destroy'):
        return GCPIaC().destroy_terraform()
    return True


def iac_parent():
    args = ArgParser('GCP IaC Commands', None, {
        'init': {
            'short': 'I',
            'help': 'Initialize GCP IaC Environment',
            'nargs': REMAINDER
        },
        'apply': {
            'short': 'a',
            'help': 'Apply GCP IaC Configuration',
            'action': 'store_true',
        },
        'destroy': {
            'short': 'd',
            'help': 'Destroy GCP IaC Configuration',
            'action': 'store_true',
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
