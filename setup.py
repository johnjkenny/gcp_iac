from setuptools import setup


try:
    setup(
        name='gcp_iac',
        version='1.0.0',
        entry_points={'console_scripts': [
            'giac = gcp_iac.cli:iac_parent',
            'giac-init = gcp_iac.cli:iac_init',
        ]},
    )
    exit(0)
except Exception as error:
    print(f'Failed to setup package: {error}')
    exit(1)
