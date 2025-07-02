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

.. note:: If you want to contribute to Charlib, you should install from repository.

====================================================================================================
Install from PyPi using pip
====================================================================================================
To install from Python package manager:

.. code-block:: SHELL

    # Install our customized version of PySpice
    pip install git+https://github.com/infinitymdm/PySpice

    # Install CharLib
    pip install charlib

====================================================================================================
Install from repository
====================================================================================================
To install from repository, first clone Charlib:

.. code-block:: SHELL

    git clone https://github.com/stineje/CharLib
    cd CharLib

and then do:

.. code-block:: SHELL

    # Install our customized version of PySpice
    pip install git+https://github.com/infinitymdm/PySpice

    # Install your forked version of CharLib
    pip install -e .

====================================================================================================
Dependencies
====================================================================================================

For CharLib to work correctly, you need following dependencies:

- Python 3.12 or newer
- Analog simulator

As analog simulator, CharLib requires one of:

- NGSPICE 44.0 or newer
- Xyce 7.8.0 or newer

NGSPICE
----------------------------------------------------------------------------------------------------
For CharLib to use NGSPICE correctly, one of conditions following must be satisfied:

    * NGSPICE must be configured with ``--with-ngshared`` option during the build to build the shared
      object library (.so) / dynamically linked library (.dll).
      See `NGSPICE shared library <https://ngspice.sourceforge.io/shared.html>`_ for details.

    * The ``simulator`` keyword must be set to ``ngspice-suprocess``. Then CharLib will use NGSPICE
      executable instead of shared library.

When installed into a system, Charlib will automatically recognize the NGSPICE installation.
To force usage of NGSPICE from a custom location, set the following environment variables:

.. code-block:: SHELL

    export LD_LIBRARY_PATH=<path_to_your_ngspice_installation>/lib
    export NGSPICE_LIBRARY_PATH=libngspice

Xyce
----------------------------------------------------------------------------------------------------
TODO: Describe Xyce Setup


====================================================================================================
Dependencies
====================================================================================================



