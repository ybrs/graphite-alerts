#!/usr/bin/env python
import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def run_setup():
    setup(
        name='graphitepager',
        version='0.0.1',
        description='',
        keywords = '',
        url='',
        author='',
        author_email='philipcristiano@gmail.com',
        license='BSD',
        packages=[''],
        install_requires=[
        ],
        test_suite='tests',
        long_description=read('README.md'),
        zip_safe=True,
        classifiers=[
        ],
        entry_points="""
        [console_scripts]
        graphite-pager=graphitepager.worker:run
        """,
    )

if __name__ == '__main__':
    run_setup()
