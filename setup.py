from setuptools import setup

version = '2.0rc5'
long_description = 'LL(1) parser generator with expression parsing support'

setup(
  name='hermes-parser',
  version=version,
  description=long_description,
  author='Scott Frazer',
  author_email='scott.d.frazer@gmail.com',
  packages=['hermes'],
  package_data={
      'hermes': [
          'templates/python/*.tpl',
          'templates/java/*.tpl',
          'templates/javascript/*.tpl',
          'templates/c/*.tpl'
      ]
  },
  install_requires=[
      "moody-templates",
      "xtermcolor",
      "nose",
      "pygments",
      "pygments_hermes"
  ],
  scripts={
      'scripts/hermes',
  },
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
