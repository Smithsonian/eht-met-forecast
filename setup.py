#!/usr/bin/env python

from setuptools import setup
from os import path

packages = [
    'eht_met_forecast',
]

requires = ['hdrhistogram', 'requests', 'pygrib']  # download
requires += ['matplotlib', 'pycairo', 'skyfield', 'pandas', 'scipy', 'astropy', 'ply']  # plots
requires += ['jinja2']  # webpages
requires += ['slack-sdk']
# pycairo needs os packages installed:
#  redhat: cairo cairo-dev (tested)
#  debian: libcairo2-dev ?

test_requires = ['pytest!=7.1.0', 'pytest-cov', 'requests_mock']

requires += ['setuptools_scm', 'cython']

extras_require = {
    'test': test_requires,  # setup no longer tests, so make them an extra that .travis.yml uses
}

scripts = ['scripts/stations-to-geodetic.py']

package_data = {'': ['data/*.json']}

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    description = f.read()

setup(
    name='eht-met-forecast',
    use_scm_version=True,
    description='Tools to generate EHT station forecasts',
    long_description=description,
    long_description_content_type='text/markdown',
    author='Greg Lindahl, Scott Paine, Lindy Blackburn, and others',
    author_email='glindahl@cfa.harvard.edu',
    url='https://github.com/wumpus/eht-met-forecast',
    packages=packages,
    python_requires=">=3.6.*",
    extras_require=extras_require,
    include_package_data=True,
    package_data=package_data,
    install_requires=requires,
    entry_points='''
        [console_scripts]
        eht-met-forecast = eht_met_forecast.cli:main
    ''',
    scripts=scripts,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Operating System :: POSIX :: Linux',
        'Natural Language :: English',
        'Programming Language :: Python',
        #'Programming Language :: Python :: 3.5',  # setuptools_scm now has f-strings
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3 :: Only',
    ],
)
