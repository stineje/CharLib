***************************************************************************************************
Syntax reference
***************************************************************************************************

.. TODO: This section could be generated if we used schema module !!

This section describes syntax of YAML configuration file. All configuration data is passed as
key-value pairs in the YAML file.

There are two keywords on the top level of the YAML configuration file:

* ``settings`` - Defines global settings for the whole library and simulation process.
* ``cells`` - Defines list of cells. May define per-cell local setting that overrides global settings.

====================================================================================================
Settings
====================================================================================================

All key-value pairs under ``settings`` keyword are optional. If a configuration value is not present,
CharLib chooses default value. We recommend including the following keys (at minimum):

Recommended Keys
----------------------------------------------------------------------------------------------------

* ``lib_name``: The library name to put to the exported liberty file.

    - Default value: ``unnamed_lib``.

* ``units``: Specifies physical units to use for input and output values. May contain the following key-value pairs:

    * ``time``: The unit of time.

        - Allowed values: (``fs``, ``ps``, ``ns``, ``us``, ``ms``)
        - Default value: ``ns``

    * ``voltage``: The unit of electrical voltage.

        - Allowed values: (``mV``, ``V``)
        - Default value: ``V``

    * ``current``: The unit of electrical current.

        - Allowed values: (``pA``, ``nA``, ``uA``, ``mA``)
        - Default value: ``uA``

    * ``capacitive_load``: The unit of capacitance.

        - Allowed values: (``fF``, ``pF``, ``nF``)
        - Default value: ``pF``

    * ``pulling_resistance``: The unit of resistance.

        - Allowed values (``mOhm``, ``Ohm``, ``kOhm``)
        - Default value: ``Ohm``

    * ``leakage_power``: The unit of power.

        - Allowed values: (``pW``, ``nW``, ``uW``)
        - Default value: ``nW``

    * ``energy``: The unit of energy.

        - Allowed values: (``aJ``, ``fJ``, ``nJ``)
        - Default value: ``fJ``

* ``named_nodes``: Specifies important node names in the SPICE netlist or transistor models. May contain the following key-value pairs:

    * ``vdd``: Node for devices supply voltage terminal.

        * ``name``: Name of the node:

            - Default value: ``VDD``

        * ``voltage``: Voltage of the node:

            - Default value: ``3.3``

    * ``vss``: Node for devices ground terminal.

        * ``name``: Name of the node:

            - Default value: ``GND``

        * ``voltage``: Voltage of the node:

            - Default value: ``0``

    * ``pwell``: Node for devices p-well terminal.

        * ``name``: Name of the node:

            - Default value: ``VPW``

        * ``voltage``: Voltage of the node:

            - Default value: ``0``

    * ``nwell``: Node for devices p-well terminal.

        * ``name``: Name of the node:

            - Default value: ``VNW``

        * ``voltage``: Voltage of the node:

            - Default value: ``3.3``

Optional Keys
----------------------------------------------------------------------------------------------------

* ``simulator``: Specifies which Spice simulator to use.

    - Allowed values:

        - ``ngspice-suprocess`` - NGPSICE launched as separate process
        - ``ngspice-shared`` - NGSPICE called directly by CharLib from shared library
        - ``xyce-serial`` - Xyce serial simulation
        - ``xyce-parallel`` - Xyce parallel simulation

    - Default value: ``ngspice-shared``.
    - For more information see: `PySpice FAQ <https://pyspice.fabrice-salvaire.fr/releases/latest/faq.html#how-to-set-the-simulator>`_

* ``logic_thresholds``: Voltage thresholds to recognize signals as logical 0 or 1. Values are relative to ``named_nodes.vdd``. May contain the following key-value pairs:

    * ``low``: The maximum fraction supply voltage recognized as a logical 0.

        - Default value: ``0.2`` (20 percent of supply voltage).

    * ``high``: The minimum fraction of supply voltage recognized as a logical 1.

        - Default value: ``0.8`` (80 percent of supply voltage).

    * ``high_to_low``: The threshold which must be crossed before CharLib considers a signal falling from one to zero.

        - Default value: ``0.5`` (50% of supply voltage).

    * ``low_to_high``: The threshold which must be crossed before Charlib considers a signal rising from zero to one.

        - Default value: ``0.5`` (50% of supply voltage).

* ``process``: The process condition to set in the exported liberty file.

    - Default value: ``1``.

* ``temperature``: The temperature to use during spice simulations.

    - Default value: ``25C``

* ``operating_conditions``: The operating conditions to set in the exported liberty file.

    - Default value: Empty, no operating conditions are put to the liberty file.

* ``cell_defaults``: Default values to use for all cells. See ``cells`` keyword below for more information. May contain any key-value pair valid for a cell entry.

.. How many cores are used ? Can this be somehow set ?

* ``multithreaded``: Run simulations in parallel.

    - Allowed values: (``True``, ``False``)
    - Default value: ``True``

* ``results_dir``: The directory where Charlib exports characterization results. If omitted, CharLib creates a ``results`` directory in the current folder.

* ``debug``: Display debug messages, and store simulation SPICE files.

    - Allowed values: (``True``, ``False``)
    - Default value: ``True``

* ``debug_dir``: The directory where to store simulation SPICE files if ``debug`` keyword is set to ``True``.

    - Default value: ``debug``.

* ``quiet``: Minimize the number of messages and data Charlib displays to the console.

    - Default value: ``False``.

* ``omit_on_failure``: What to do if a cell fails to characterize.

    - Allowed values:

        - ``True`` - Skip failed cell and continue with the rest.
        - ``False`` - Terminate CharLib.

    - Default value: ``False``

====================================================================================================
Cells
====================================================================================================

Cells to characterize are specified as entries under the ``cells`` keyword.
Name of the cell shall be a top-most key of the dictionary. E.g.:

.. code-block:: YAML

    cells:
        <cell_name>:
            <configuration of first cell>
        <another_cell_name>:
            <configuration of second cell>


Name of the cell shall match the ``.subckt`` name in the SPICE netlist that represents the circuit
of this cell.

Required Keys
----------------------------------------------------------------------------------------------------
Each cell entry shall contain at least following keys:

* ``netlist``: The path to the spice file containing the netlist for this cell.

* ``models``: A list of paths to the spice models for transistors used in this cell's netlist. If omitted, CharLib assumes each cell has no dependencies.

	* Using the syntax ``path/to/file`` will result in ``.include path/to/file`` in SPICE simulations.
	* Using the syntax ``path/to/dir`` will allow CharLib to search the directory for subcircuits used in a particular cell and include them using ``.include path/to/dir/file``.
	* Using the syntax ``path/to/file section`` will result in ``.lib path/to/file section`` in SPICE simulations.

* ``inputs``: A list of input pin names.

* ``outputs``: A list of output pin names.

* ``functions``: A list of verilog functions describing each output as logical function of inputs. Shall be in the same order as ``outputs``

* ``slews``: A list of input pin slew rates to characterize. Unit is specified by ``settings.units.time``.

* ``loads``: A list of output capacitive loads to characterize. Unit is specified by ``settings.units.capacitive_load``.

* ``simulation_timestep``: The simulation timestep.

    - Allowed values: ``<number><unit>`` where ``<unit>`` has the same allowed values as ``settings.units.time``.

Any of these keys can be omitted from cell entries by instead specifying them in the ``settings.cell_defaults``.

CharLib automatically merges any key-value pairs from ``settings.cell_defaults`` to each cell entry when characterizing the cell.

If a key appears in a cell's entry, and in ``cell_defaults``, the value in the cell entry overrides the value from ``cell_defaults``.

To keep individual cell configurations separate from your top level CharLib configuration file,
YAML files for individual cells may be specified using following syntax:

``<cell_name>: <relative_path_to_cell_configuration_yaml_from_current_dir>``.

Required Keys for Sequential Cells
----------------------------------------------------------------------------------------------------
To characterize sequential cells, you shall put following additional entries under the cell definition:

* ``clock``: The clock pin name and edge direction.

    - Allowed values: ``<edge_direction> <clock_pin_name>``. Where ``edge_direction`` can be one of: ``posedge`` or ``negedge``. E.g. ``posedge CLK`` or ``negedge CKB``.

* ``flops``: A list of storage element names. These are the names of flip-flops that Charlib puts under ``ff`` keyword in the generated liberty file.

* ``setup_time_range``: A list of margins to be used when characterizing setup time.

* ``hold_time_range``: A list of margins to be used when characterizing hold time.

Optional Keys
----------------------------------------------------------------------------------------------------

* ``area``: The physical area occupied by the cell layout. The value is in ``um^2``.

    - Default value: 0

* ``set``: The asynchronous set pin name, and edge direction. For sequential cells only. If omitted, CharLib assumes the cell does not have a set pin.

    - Allowed values: ``<edge_direction> <pin_name>``. Where ``edge_direction`` can be one of: ``posedge`` or ``negedge``. E.g. ``negedge AS`` defines active low set pin ``AS``.

* ``reset``: The asynchronous reset pin name, and edge direction. For sequential cells only. If omitted, CharLib assumes the cell does not have a reset pin.

    - Allowed values: ``<edge_direction> <pin_name>``. Where ``edge_direction`` can be one of: ``posedge`` or ``negedge``. E.g. ``posedge AR`` defines active high reset pin  ``AR``.

* ``clock_slew``: The slew rate to use for the clock signal in simulation. For sequential cells only. In units specified by ``settings.units.time``.

    - Default value: 0

* ``plots``: A string, or list of strings specifying which plots to show for this cell.

    - Allowed values:

        - ``all`` - Dump all plots
        - ``none`` - Do not dump any plots
        - Any subset of: ``io``, ``delay``, ``energy``

    - Default value: ``none``
