#!/usr/bin/env python
import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def run_setup():
    setup(
        name='graphitepager',
        version='0.0.6',
        description='',
        keywords = '',
        url='http://github.com/philipcristiano/graphite-pager',
        author='Philip Cristiano',
        author_email='philipcristiano@gmail.com',
        license='BSD',
        packages=['graphitepager'],
        install_requires=[
            'Jinja2==2.6',
            'PyYAML==3.10',
            'distribute==0.6.28',
            'pagerduty==0.2.1',
            'redis==2.6.2',
            'requests==0.14.0',
            'python-simple-hipchat==0.1',
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
