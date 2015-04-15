#!/usr/bin/env python
import os

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


install_requires = [
]

setup(
    name='demotime',
    version='0.1',
    author='Mark Rogers',
    author_email='f4nt@f4ntasmic.com',
    url='https://github.com/f4nt/demotime/',
    description='A service for facilitating demos between dev and product',
    packages=find_packages(),
    zip_safe=False,
    install_requires=install_requires,
    include_package_data=True,
    entry_points={},
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)

