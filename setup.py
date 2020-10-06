# -*- coding: utf-8 -*-

# DO NOT EDIT THIS FILE!
# This file has been autogenerated by dephell <3
# https://github.com/dephell/dephell

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os.path

readme = ''
here = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(here, 'README.rst')
if os.path.exists(readme_path):
    with open(readme_path, 'rb') as stream:
        readme = stream.read().decode('utf8')

setup(
    long_description=readme,
    name='diot',
    version='0.1.0',
    description='Python dictionary with dot notation.',
    python_requires='==3.*,>=3.6.0',
    project_urls={
        "homepage": "https://github.com/pwwang/diot",
        "repository": "https://github.com/pwwang/diot"
    },
    author='pwwang',
    author_email='pwwang@pwwang.com',
    license='MIT',
    packages=['diot'],
    package_dir={"": "."},
    package_data={},
    install_requires=['inflection==0.*'],
    extras_require={"dev": ["pytest", "pytest-cov", "pyyaml", "toml"]},
)
