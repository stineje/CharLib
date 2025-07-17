***************************************************************************************************
Installation
***************************************************************************************************

There are two approaches to installing Charlib:

- :ref:`install_pip`
- :ref:`install_repo`

When installing by either means, we recommend creating a python virtual environment for the
installation. This helps separate CharLib and its dependencies from other software on your system.

.. code-block:: SHELL

    python3 -m venv .venv
    source .venv/bin/activate

.. note::
    If you want to contribute to Charlib, you should fork the repository and install your fork by
    following the instructions under :ref:`install_repo`.

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
Install using pip
====================================================================================================
This is the recommended method to install CharLib for normal use.

..  For now we're recommending installing from the latest git master rather than a particular
    release. This will probably change with the next release.

Execute the following to install CharLib:

.. code-block:: SHELL

    python -m pip install git+https://github.com/stineje/CharLib

.. note::
    If you have any trouble installing CharLib, please
    `open a new issue <https://github.com/stineje/CharLib/issues/new?template=problem-report.md>`_.

.. _install_repo:

====================================================================================================
Install from a cloned repository
====================================================================================================
You should use this method to install CharLib if you want to make tweaks to its code or contribute
to its development.

Begin by using git to clone CharLib:

.. code-block:: SHELL

    git clone https://github.com/stineje/CharLib # If you plan to contribute, clone your fork instead

and then install the cloned repository:

.. code-block:: SHELL

    cd CharLib
    pip install -e .
