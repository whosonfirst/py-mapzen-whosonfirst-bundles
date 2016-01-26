#!/usr/bin/env python

# Remove .egg-info directory if it exists, to avoid dependency problems with
# partially-installed packages (20160119/dphiffer)

import os, sys
from shutil import rmtree

cwd = os.path.dirname(os.path.realpath(sys.argv[0]))
egg_info = cwd + "/mapzen.whosonfirst.bundles.egg-info"
if os.path.exists(egg_info):
    rmtree(egg_info)

from setuptools import setup, find_packages

packages = find_packages()
version = open("VERSION").read()
desc = open("README.md").read()

setup(
    name='mapzen.whosonfirst.bundles',
    namespace_packages=['mapzen', 'mapzen.whosonfirst', 'mapzen.whosonfirst.bundles'],
    version=version,
    description='A package to generate Who\'s On First data bundles',
    author='Mapzen',
    url='https://github.com/mapzen/py-mapzen-whosonfirst-bundles',
    install_requires=[
        'boto',
        'mapzen.whosonfirst.placetypes>=0.11',
        ],
    dependency_links=[
        'https://github.com/whosonfirst/py-mapzen-whosonfirst-placetypes/tarball/master#egg=mapzen.whosonfirst.placetypes-0.11',
        ],
    packages=packages,
    scripts=[
        'scripts/wof-bundle-placetypes',
        ],
    download_url='https://github.com/mapzen/py-mapzen-whosonfirst-bundle/releases/tag/' + version,
    license='BSD')
