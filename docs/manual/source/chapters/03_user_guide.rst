***************************************************************************************************
User Guide
***************************************************************************************************

====================================================================================================
Flow of operation
====================================================================================================

CharLib runs analog simulation of the cells to be characterized to determine their electrical
properties. The overal flow is shown in the figure below.

.. image:: figures/flow_block_diagram.svg
    :width: 400
    :align: center

To run characterization, you must provide:

1. SPICE netlists of the cells to be characterized (ideally with extracted parasistics)
2. Analog transistor models from your PDK
3. A YAML configuration file

Typically the first two items are provided by your foundry as part of the PDK. The third item tells
CharLib how to process the SPICE netlists and transistor models. Using CharLib basically boils down
to constructing a YAML file detailing your cells and characterization conditions.

.. note::

    See :ref:`yaml_examples` for more information on configuring CharLib.

====================================================================================================
Invoking CharLib
====================================================================================================

To interact with CharLib's command line interface, execute:

.. code-block:: SHELL

    charlib <command>

CharLib supports the following commands:

- ``run``: characterize cells using an existing configuration file
- *``compare``: compare a liberty file against a benchmark "golden" liberty file
- *``generate_functions``: generate test vectors for a particular function

.. note::

    Commands marked with * are experimental features which may or may not be functional in any
    given release of CharLib.

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

Example 1: OSU350 INVX1 Characterization
----------------------------------------------------------------------------------------------------

The example below is a configuration file for characterization of a single ``INVX1`` inverter cell.
When run with this configuration file, CharLib will measure the properties of the inverter and
produce a liberty file called "test_OSU350.lib".

.. literalinclude:: ../../../../test/pdks/osu350/ex_invx1.yaml
    :language: yaml
    :linenos:

You can run this configuration by navigating to the ``test/pdks/osu350`` directory and executing
the following commands.

.. code-block:: SHELL

    ./fetch_spice.sh # Download OSU350 cell spice & transistor models (tested on Linux)
    charlib run ex_invx1.yaml

Example 2: Characterizing Multiple OSU350 Combinational Cells
----------------------------------------------------------------------------------------------------

The YAML below configures CharLib to perform characterization of full adder (``FAX1``) and half
adder (``HAX1``) cells. Notice the following changes from example 1:

* Several cell parameters are moved into ``settings.cell_defaults`` to avoid repeating them for
  each cell.
* The ``inputs`` and ``outputs`` keys are omitted from cell configurations. CharLib infers these
  from the cells' functions instead.

.. literalinclude:: ../../../../test/pdks/osu350/ex_adders.yaml
    :language: yaml
    :linenos:

You can run this configuration by navigating to the ``test/pdks/osu350`` directory and executing
the following commands.

.. code-block:: SHELL

    ./fetch_spice.sh # Not required if run previously
    charlib run ex_adder.yaml

Example 3: OSU350 DFFSR Characterization
---------------------------------------------------------------------------------------------------

.. note::
    The timing procedures for sequential cells in CharLib 1.X were inaccurate and have been
    deprecated as of CharLib 2.0.0. As a result, the example below does not work with the current
    release. This will be updated when sequential cell characterization is restored.

The example below is a config file for positive-edge triggered flip-flop (``DFFSR``) with
asynchronous set and reset.

.. code-block:: YAML

    settings:
        lib_name: test_OSU350
        units:
            pulling_resistance: kOhm
        named_nodes:
            primary_ground:
                name: GND
        cell_defaults:
            models:     [model.sp]
            clock_slews:[0.01, 0.08, 0.25]
            data_slews: [0.015, 0.04, 0.08, 0.2, 0.4]
            loads:      [0.06, 0.18, 0.42, 0.6, 1.2]
    cells:
        DFFSR:
            netlist:    osu350_spice_temp/DFFSR.sp
            area:       704
            clock:      posedge CLK
            set:        not S
            reset:      not R
            functions:  [Q <= D]
            state:      [IQ = Q]

Example 4: Characterizing Multiple GF180 Cells
----------------------------------------------------------------------------------------------------

The example below is a configuration file for characterization of multiple cells.

.. code-block:: YAML

    settings:
        lib_name: gf180mcu_osu_sc_gp9t3v3_tt_25c.nldm
        results_dir: lib
        cell_defaults:
            models: # Download from corresponding links & place in the correct locations, or point to your clone of gf180mcu_fd_pr
                - ../models/sm141064.ngspice typical # https://raw.githubusercontent.com/fossi-foundation/globalfoundries-pdk-libs-gf180mcu_fd_pr/refs/heads/main/models/ngspice/sm141064.ngspice
                - ../models/design.ngspice           # https://raw.githubusercontent.com/fossi-foundation/globalfoundries-pdk-libs-gf180mcu_fd_pr/refs/heads/main/models/ngspice/design.ngspice
            netlist: spice/gf180mcu_osu_sc_gp9t3v3.spice
            data_slews:  [0.0706, 0.1903, 0.5123, 1.3794, 3.7140, 10]
            loads:       [0.0013, 0.0048, 0.0172, 0.0616, 0.2206, 0.7901]
    cells:
        gf180mcu_osu_sc_gp9t3v3__addf_1:
            functions:
                - SUM=A^B^CI
                - CO=A&B | CI&(A^B)
        gf180mcu_osu_sc_gp9t3v3__addh_1:
            inputs: [A, B]
            outputs: [SUM, CO]
            functions:
                - SUM=A^B
                - CO=A&B
        gf180mcu_osu_sc_gp9t3v3__and2_1:
            inputs: [A, B]
            outputs: ['Y']
            functions: [Y=A&B]
        gf180mcu_osu_sc_gp9t3v3__aoi21_1:
            inputs: [A0, A1, B]
            outputs: ['Y']
            functions: [Y=(!A0&!B) | (!A1&!B)]
        gf180mcu_osu_sc_gp9t3v3__inv_1:
            inputs: [A]
            outputs: ['Y']
            functions: [Y=!A]
        gf180mcu_osu_sc_gp9t3v3__mux2_1:
            inputs: [A, B, SEL]
            outputs: ['Y']
            functions: [Y=(A&!SEL) | (B&SEL)]
        gf180mcu_osu_sc_gp9t3v3__nand2_1:
            inputs: [A, B]
            outputs: ['Y']
            functions: [Y=!(A&B)]
        gf180mcu_osu_sc_gp9t3v3__nor2_1:
            inputs: [A, B]
            outputs: ['Y']
            functions: [Y=!(A|B)]
        gf180mcu_osu_sc_gp9t3v3__or2_1:
            inputs: [A, B]
            outputs: ['Y']
            functions: [Y=A|B]
        gf180mcu_osu_sc_gp9t3v3__xor2_1:
            inputs: [A, B]
            outputs: ['Y']
            functions: [Y=A^B]

This configuration can be run against the 9-track cells in https://github.com/stineje/globalfoundries-pdk-libs-gf180mcu_osu_sc.
