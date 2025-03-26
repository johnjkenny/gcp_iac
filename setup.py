from setuptools import setup


try:
    setup(
        name='gcp_compute',
        version='1.0.0',
        entry_points={'console_scripts': [
            'gcompute = gcp_compute.cli:compute_parent',
        ]},
    )
    exit(0)
except Exception as error:
    print(f'Failed to setup package: {error}')
    exit(1)
