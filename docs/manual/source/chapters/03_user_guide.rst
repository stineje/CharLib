***************************************************************************************************
User Guide
***************************************************************************************************

====================================================================================================
Flow of operation
====================================================================================================

CharLib runs analog simulation of the cells to be characterized to determine their timing behavior.
The overal flow is shown in the following figure:

.. image:: figures/flow_block_diagram.svg
    :width: 400
    :align: center

To run characterization, you must provide:

1. SPICE netlist of the cells to be characterized (ideally with extracted parasistics for accuracy)
2. Analog transistor models for your PDK
3. YAML configuration file

Typically the first two items are provided by your foundry as part of the PDK. The third item tells
CharLib how to process the SPICE netlists and transistor models.

.. note::

See :ref:`yaml_examples` for more information on configuring CharLib.

====================================================================================================
Invoking CharLib
====================================================================================================

To interact with CharLib's command line interface, execute:
.. code-block:: SHELL

    charlib <command>

CharLib supports the following commands:

    - ``run`` to characterize cells using an existing configuration file
    - ``compare`` to compare a liberty file against a benchmark "golden" liberty file

Help
----------------------------------------------------------------------------------------------------

.. code-block:: SHELL

    charlib --help

will display lots of useful information.

Running characterization
----------------------------------------------------------------------------------------------------

To characterize a standard cell library with CharLib, execute:

.. code-block:: SHELL

    charlib run <path_to_library_config>

``<path_to_library_config>`` may be either a path directly to the YAML configuration file, or to
a directory containing a configuration file. If ``<path_to_library_config>`` is a directory,
CharLib searches the specified directory for a YAML file containing a valid cell library
configuration. Once a configuration is identified, CharLib characterizes each cell included in the
configuration file.

Comparing Liberty files
----------------------------------------------------------------------------------------------------

To compare two Liberty files with CharLib, execute:

.. code-block:: SHELL

    charlib compare <benchmark_lib_file> <compared_lib_file>

where:

- ``benchmark_lib_file`` a "golden" reference liberty file to compare against.
- ``compared_lib_file`` a liberty file (typically produced by CharLib) to be compared against the
    benchmark file.

.. _yaml_examples:
====================================================================================================
YAML configuration examples
====================================================================================================

Example 1: OSU350 INVX1 Characterization
----------------------------------------------------------------------------------------------------

The example below is a configuration file for characterization of a single ``INVX1`` inverter cell.

.. code-block:: YAML

    settings:
        lib_name:           test_OSU350
        units:
            # Specify all units for clarity, even though only resistance differs from the default
            time:               ns
            voltage:            V
            current:            uA
            pulling_resistance: kOhm
            leakage_power:      nW
            capacitive_load:    pF
            energy:             fJ
    cells:
        INVX1:
            netlist:    osu350_spice_temp/INVX1.sp
            models:     [test/osu350/model.sp]
            area:       128
            inputs:     [A]
            outputs:    ['Y'] # Must be in quotes because YAML interprets Y as boolean True
            functions:  [Y=!A]
            slews: [0.015, 0.04, 0.08, 0.2, 0.4]
            loads: [0.06, 0.18, 0.42, 0.6, 1.2]


Example 2: Characterizing Multiple OSU350 Combinational Cells
----------------------------------------------------------------------------------------------------

The YAML below configures CharLib to perform characterization of full adder (``FAX1``) and half
adder (``HAX1``) cells. Notice that several cell parameters are moved into
``settings.cell_defaults`` to avoid repeating them for each cell.

.. code-block:: YAML

    settings:
        lib_name:           test_OSU350
        units:
            pulling_resistance: kOhm # This is the only unit that differs from the defaults
        cell_defaults:
            # The key-value pairs below get copied to all cells
            models: [test/osu350/model.sp]
            slews: [0.015, 0.04, 0.08, 0.2, 0.4]
            loads: [0.06, 0.18, 0.42, 0.6, 1.2]
    cells:
        FAX1:
            netlist:    osu350_spice_temp/FAX1.sp
            area:       480
            inputs:     [A, B, C]
            outputs:    [YC, YS]
            functions:
                - YC=(A&B)|(C&(A^B))
                - YS=A^B^C
        HAX1:
            netlist:    osu350_spice_temp/HAX1.sp
            area:       320
            inputs:     [A, B]
            outputs:    [YC, YS]
            functions:
                - YC=A&B
                - YS=A^B
            loads: [0.012, 0.036, 0.06] # This overrides the value from cell_defaults

Example 3: OSU350 DFFSR Characterization
----------------------------------------------------------------------------------------------------


The example below is a config file for positive-edge triggered flip-flop (``DFFSR``) with
asynchronous set and reset.

.. code-block:: YAML

    settings:
        lib_name:           test_OSU350
        units:
            pulling_resistance: kOhm
        cell_defaults:
            models: [test/osu350/model.sp]
            slews: [0.015, 0.04, 0.08, 0.2, 0.4]
            loads: [0.06, 0.18, 0.42, 0.6, 1.2]
            setup_time_range: [0.001, 1]
            hold_time_range: [0.001, 1]
    cells:
        DFFSR:
            netlist:    osu350_spice_temp/DFFSR.sp
            area:       704
            clock:      posedge CLK
            set:        negedge S
            reset:      negedge R
            inputs:     [D]
            outputs:    [Q]
            flops:      [P0002,P0003]
            functions:  [Q<=D]


Example 4: Characterizing Multiple GF180 Cells
----------------------------------------------------------------------------------------------------

The example below is a configuration file for characterization of multiple cells.

.. code-block:: YAML

    settings:
        lib_name:           test_GF180
        omit_on_failure:    yes # If a cell fails, CharLib will exclude it from the results & continue with the other cells
        units:
            pulling_resistance: kOhm
        named_nodes:
            vss:
                name:       VSS # GF180 uses VSS instead of GND, so we have to override the default
                voltage:    0
        cell_defaults:
            models:
                - gf180_temp/models/sm141064.ngspice typical # This syntax tells CharLib to use the '.lib file section' syntax for this model
                - gf180_temp/models/design.ngspice
            slews:  [0.015, 0.08, 0.4]
            loads:  [0.06, 1.2]
    cells:
        gf180mcu_osu_sc_gp12t3v3__inv_1:
            netlist:    gf180_temp/cells/gf180mcu_osu_sc_gp12t3v3__inv_1.spice
            inputs:     [A]
            outputs:    ['Y']
            functions:  [Y=!A]
        gf180mcu_osu_sc_gp12t3v3__and2_1:
            netlist:    gf180_temp/cells/gf180mcu_osu_sc_gp12t3v3__and2_1.spice
            inputs:     [A,B]
            outputs:    ['Y']
            functions:  [Y=A&B]
        gf180mcu_osu_sc_gp12t3v3__xnor2_1:
            netlist:    gf180_temp/cells/gf180mcu_osu_sc_gp12t3v3__xnor2_1.spice
            inputs:     [A,B]
            outputs:    ['Y']
            functions:  [Y=!(A^B)]
