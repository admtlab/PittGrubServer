#!/usr/bin/env python

from setuptools import setup


setup(
    name='PittGrub-Server',
    version='0.1.0',
    description='Server for PittGrub app',
    url='https://github.com/admtlab/pittgrubserver',
    author='Mark Silvis',
    author_email='marksilvis@pitt.edu',
    license='TBD',
    packages=['pittgrub/'],
    install_requires=[
        'tornado>=4.5.1',
        'pymysql>=0.7.11',
        'sqlalchemy>=1.1.10',
        'passlib>=1.7.1',
        'bcrypt>=3.1.3',
        'pyjwt>=1.5.2',
        'pillow>=4.2.1',
        'exponent-server-sdk>=0.1.1',
        'sockjs>=0.6.0',
        'inflect>=0.2.5',
        #'flake8>=3.3.0'
    ],
    tests_require=[
        #'flake8>=3.3.0',
        'nose>=1.3.7',
        'mock>=2.0.0',
    ],
)
