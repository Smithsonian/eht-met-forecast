#!/usr/bin/env python

from setuptools import setup

packages = [
    'eht_met_forecast',
]

requires = []

test_requirements = []

scripts = ['scripts/stations-to-geodetic.py']

package_data = {'': ['data/*.json']}

try:
    import pypandoc
    description = pypandoc.convert_file('README.md', 'rst')
except (IOError, ImportError):
    description = open('README.md').read()

setup(
    name='eht-met-forecast',
    use_scm_version=True,
    description='Tools to generate EHT station forecasts',
    long_description=description,
    author='Greg Lindahl and others',
    author_email='glindahl@cfa.harvard.edu',
    url='https://github.com/wumpus/eht-met-forecast',
    packages=packages,
    python_requires=">=3.4.*",
    include_package_data=True,
    package_data=package_data,
    setup_requires=['setuptools_scm'],
    install_requires=requires,
    entry_points='''
        [console_scripts]
        eht-met-forecast = eht_met_forecast.cli:main
    ''',
    scripts=scripts,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
    ],
)
