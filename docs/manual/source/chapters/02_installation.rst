***************************************************************************************************
Installation
***************************************************************************************************

There are two approaches to installing Charlib:

- Install from PyPi using pip
- Install from repository

When installing by either means, we recommend creating a python virtual environment for
the installation:

.. code-block:: SHELL

    python3 -m venv .venv
    source .venv/bin/activate

.. note::
    If you want to contribute to Charlib, you should fork the repository and install your fork by
    following the :ref:`_install_repo` steps.

====================================================================================================
Dependencies
====================================================================================================

CharLib requires the following prerequisite dependencies:

- Python 3.12 or newer
- An analog circuit simulator

CharLib supports the following analog circuit simulators. Consult your PDK to find out which
simulator you need.

- ngspice 44.0 or newer
- Xyce 7.8.0 or newer

.. _install_pip:
====================================================================================================
Install from PyPi using pip
====================================================================================================
To install from Python package manager:

.. code-block:: SHELL

    # Install our customized version of PySpice
    pip install git+https://github.com/infinitymdm/PySpice

    # Install CharLib
    pip install charlib

.. note::
    If you have any trouble installing CharLib, please `open a new issue <https://github.com/stineje/CharLib/issues/new?template=problem-report.md>`_

.. _install_repo:
====================================================================================================
Install from repository
====================================================================================================
To install from repository, first clone CharLib:

.. code-block:: SHELL

    git clone https://github.com/stineje/CharLib
    cd CharLib

and then install the cloned repository:

.. code-block:: SHELL

    # Install our customized version of PySpice
    pip install git+https://github.com/infinitymdm/PySpice

    # Install CharLib
    pip install -e .
