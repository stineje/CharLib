***************************************************************************************************
User Guide
***************************************************************************************************

====================================================================================================
Basic Operation
====================================================================================================

CharLib runs analog simulation of the configured cells to determine their electrical properties.
The overal flow is shown in the figure below.

.. mermaid:: figures/charlib_internal_flow.mmd

To run characterization, you must provide:

1. SPICE netlists of the cells to be characterized (ideally with extracted parasistics)
2. Analog transistor models from your PDK
3. A YAML configuration file

Typically the first two items are provided by your foundry as part of the PDK. The third item tells
CharLib how to process the SPICE netlists and transistor models. Using CharLib basically boils down
to constructing a YAML file detailing your cells and characterization conditions.

.. note::

    See :ref:`yaml_examples` for more information on configuring CharLib.

We have also created a video guide that walks through the process of installing CharLib, creating a
configuration file, and characterizing a cell. You can
`watch that video here on YouTube <https://youtu.be/QYgwKUkUTOc?si=QH0ajlIu4vUQsxAa>`_.

====================================================================================================
Running CharLib
====================================================================================================

To interact with CharLib's command line interface, execute:

.. code-block:: SHELL

    charlib <command>

CharLib supports the following commands:

- ``run``: characterize cells using an existing configuration file
- ``compare``: (experimental) compare a liberty file against a benchmark "golden" liberty file
- ``generate_functions``: (experimental) generate test vectors for a particular function

.. note::

    Commands marked with (experimental) may or may not be functional in any given release of
    CharLib.

Usage
----------------------------------------------------------------------------------------------------

.. code-block:: SHELL

    charlib --help

will display lots of useful information. You can also run ``charlib <command> --help`` to show
usage information for a particular command.

Running characterization
----------------------------------------------------------------------------------------------------

To characterize a standard cell library with CharLib, execute:

.. code-block:: SHELL

    charlib run <path_to_library_config>

``<path_to_library_config>`` may be either a path directly to the YAML configuration file, or to
a directory containing a configuration file. If ``<path_to_library_config>`` is a directory,
CharLib recursively searches the specified directory for a YAML file containing a valid cell
library configuration. Once a configuration is identified, CharLib characterizes each cell included
in the configuration file.

Optional arguments for ``charlib run`` include:

- ``--output <output>``: place characterization results in the specified ``<output>``
  directory.
- ``--jobs <jobs>``: specify the maximum number of threads to use for characterization.
- ``--filter <filters>``: only characterize cells whose names match the regex pattern given in
  ``<filters>``.

More information about optional arguments can be found by running ``charlib run --help``.

.. _yaml_examples:

====================================================================================================
YAML configuration examples
====================================================================================================

The examples in this section can be run after `installing CharLib <02_installation.html>`_ and
downloading the corresponding standard cells.

To download the OSU350 cells and models:

.. literalinclude:: ../../../../test/examples/get_osu350.sh
    :language: bash
    :linenos:

To download the gf180mcu OSU 9t cells and models:

.. literalinclude:: ../../../../test/examples/get_gf180mcu_osu_9t.sh
    :language: bash
    :linenos:

Example 1: OSU350 INVX1 Characterization
----------------------------------------------------------------------------------------------------

The example below is a configuration file for characterization of a single ``INVX1`` inverter cell.
When run with this configuration file, CharLib will measure the properties of the inverter and
produce a liberty file called "osu350_inverter_example.lib".

.. literalinclude:: ../../../../test/examples/ex_osu350_invx1.yaml
    :language: yaml
    :linenos:

You can run this configuration by navigating to CharLib's ``test/examples`` directory and executing
the following commands.

.. code-block:: SHELL

    ./get_osu350.sh # Download OSU350 cell spice & transistor models
    charlib run ex_osu350_invx1.yaml

Example 2: Characterizing Multiple OSU350 Combinational Cells
----------------------------------------------------------------------------------------------------

The YAML below configures CharLib to perform characterization of full adder (``FAX1``) and half
adder (``HAX1``) cells. Notice the following changes from example 1:

* Several cell parameters are moved into ``settings.cell_defaults`` to avoid repeating them for
  each cell.
* The ``inputs`` and ``outputs`` keys are omitted from cell configurations. CharLib infers these
  from the cells' functions instead.

.. literalinclude:: ../../../../test/examples/ex_osu350_adders.yaml
    :language: yaml
    :linenos:

You can run this configuration by navigating to CharLib's ``test/examples`` directory and executing
the following commands.

.. code-block:: SHELL

    ./get_osu350.sh # Download OSU350 cell spice & transistor models
    charlib run ex_osu350_adders.yaml

Example 3: YAML-Free OSU350 DFFSR Characterization
---------------------------------------------------------------------------------------------------

CharLib may be used as a Python module without creating a separate YAML configuration file. The
example below shows the characterization of an OSU350 sequential cell using this method. Note that
this example will take quite a bit longer to run than the combinational examples above, as
sequential cell characterization is much more complex than combinational.

.. note::

    Using a CharLib ``Characterizer`` object directly (as shown below) bypasses all of the
    validation checks built into CharLib's command-line interface. While this method of using
    CharLib can grant much finer control over the characterization process, we recommend the use of
    YAML configuration files to help avoid configuration errors.

.. literalinclude:: ../../../../test/examples/ex_osu350_dffsr.py
    :language: python
    :linenos:

Example 4: Characterizing Multiple gf180mcu Cells
----------------------------------------------------------------------------------------------------

The example below is a configuration file for characterization of several cells from the OSU
9-track standard cell library. This configuration includes a mix of combinational and sequential
cells.

.. literalinclude:: ../../../../test/examples/ex_gf180_osu_9t.yaml
    :language: yaml
    :linenos:
