#!/usr/bin/env python

from setuptools import setup, find_packages

packages = find_packages()
desc = open("README.md").read(),

setup(
    name='mapzen.whosonfirst.bundles',
    namespace_packages=['mapzen', 'mapzen.whosonfirst', 'mapzen.whosonfirst.bundles'],
    version='0.01',
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
    download_url='https://github.com/mapzen/py-mapzen-whosonfirst-bundle/releases/tag/v0.01',
    license='BSD')
