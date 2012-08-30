import distribute_setup
distribute_setup.use_setuptools()

import os
from setuptools import setup, find_packages

version = '1.0.0'
README = os.path.join(os.path.dirname(__file__), 'README')
long_description = open(README).read()

setup(
  name='Hermes',
  version=version,
  description=long_description,
  author='Scott Frazer',
  author_email='scott.d.frazer@gmail.com',
  packages=['hermes'],
  package_dir={'hermes': 'hermes'},
  package_data={'hermes': ['templates/python/*.tpl', 'templates/java/*.tpl', 'templates/c/*.tpl']},
  install_requires=[
    "moody-templates>=0.9",
    "xtermcolor==1.0.1"
  ],
  entry_points={
  'console_scripts': [
      'hermes = hermes.Main:Cli'
    ]
  },
  test_suite='test.HermesTest',
  license = 'MIT',
  keywords = "Parser, Recursive Descent, LL(1), Pratt, Expression, Parser Generator",
  url = "http://github.com/scottfrazer/hermes",
  classifiers=[
    'License :: OSI Approved :: MIT License',
    "Programming Language :: Python",
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Natural Language :: English",
    "Topic :: Software Development :: Code Generators",
    "Topic :: Software Development :: Compilers"
  ]
)
