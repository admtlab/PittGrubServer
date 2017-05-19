#!/usr/bin/env python

from distutils.core import setup

setup(name='PittGrub-Server',
      version='0.1.0',
      description='Server for PittGrub app',
      author='Mark Silvis, David Tsui',
      author_email='marksilvis@pitt.edu, dat83@pitt.edu',
      url='https://github.com/admtlab/pittgrubserver',
      requires=[
            'tornado',
            'sockjs',
            'sqlalchemy',
            'pymysql',
            'inflect',
      ]
     )
