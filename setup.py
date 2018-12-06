from setuptools import setup, find_packages

VERSION = '0.1'

setup(
    name='team_metrics',
    packages=find_packages(),
    version=VERSION,
    description='A library for GDS team-metrics',
    author='Ken Tsang',
    author_email='ken.tsang@digital.cabinet-office.gov.uk',
    url='https://github.com/alphagov/team-metrics',
    keywords=['team-metrics'],
    license='MIT',
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    dependency_links=[
        'git+https://github.com/pycontribs/jira.git@master#egg=jira'
    ],
)
