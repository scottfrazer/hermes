import distribute_setup
distribute_setup.use_setuptools()

import os
from setuptools import setup, find_packages

version = '1.0.0b'
README = os.path.join(os.path.dirname(__file__), 'README')
long_description = open(README).read()

setup(
    name='Hermes',
    version=version,
    description=long_description,
    author='Scott Frazer',
    author_email='scott.d.frazer@gmail.com',
    packages=['hermes'],
    package_dir={
        'hermes': 'hermes',
    },
    install_requires=[
        "moody-templates>=0.9"
    ],
    entry_points={
      'console_scripts': [
            'hermes = hermes.Main:Cli'
        ]
      },
    license = "GPL",
    keywords = "Parser, Recursive Descent, LL(1), Pratt, Expression, Parser Generator",
    url = "http://zeus-lang.org/hermes",
    classifiers=[
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Programming Language :: Python",
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "Natural Language :: English",
          "Topic :: Software Development :: Code Generators",
          "Topic :: Software Development :: Compilers"
      ]
    )
