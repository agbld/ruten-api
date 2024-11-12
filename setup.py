from setuptools import setup, find_packages

setup(
    name='ruten_api',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests',
        'pandas',
        'tqdm',
        'ipython'
    ],
    description='Helper functions for interacting with the Ruten API',
    author='agbld',
    author_email='agiblida#gmail.com',
    url='https://github.com/agbld/ruten-api',
)
