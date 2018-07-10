#!/usr/bin/python

import sys
from setuptools import setup
from setuptools import find_packages

__module__ = 'async-nftables'
__url__ = 'https://github.com/ccxtechnologies'

__version__ = None
exec(open(f'{__module__}/__version__.py').read())

if "--nosystemd" in sys.argv:
    sys.argv.remove("--nosystemd")

setup(
        name=__module__,
        version=__version__,
        author='CCX Technologies',
        author_email='charles@ccxtechnologies.com',
        description='asyncio wrapper around nft',
        license='MIT',
        url=f'{__url__}/{__module__}',
        download_url=f'{__url__}/archive/v{__version__}.tar.gz',
        python_requires='>=3.6',
        packages=find_packages(),
        install_requires=[
                'async_timeout>=2.0.1',
        ]
)
