from distutils.core import setup

VERSION = '0.1'

setup(
    name='team_metrics',
    packages=['team_metrics'],
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
)
