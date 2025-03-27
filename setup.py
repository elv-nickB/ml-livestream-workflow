from setuptools import setup, find_packages

setup(
    name='my_package',  
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'tqdm',
        'loguru',
        'elv-client-py @ git+https://github.com/eluv-io/elv-client-py.git#egg=elv-client-py',
    ],
)