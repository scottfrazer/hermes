Installation
============

To install Hermes, use `Distribute <http://pypi.python.org/pypi/distribute>`_, a fork of Setuptools.  If you don't have Distribute, you can install it from the distribute_setup.py script in the project root.  Once Distribute is set up, installation is as simple as:

.. code-block:: bash

    $ python setup.py install

To verify installation, simply run from the command line:

.. code-block:: bash

    $ hermes
    usage: hermes [-h] [-s START] [-d DIRECTORY] [-l LANGUAGE] [-t TOKENS]
                  {analyze,generate,parse} GRAMMAR
    hermes: error: too few arguments

Hermes should also be importable as a module:

.. code-block:: bash

    $ python
    >>> import hermes
    >>>

