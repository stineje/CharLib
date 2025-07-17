 

.. _04_syntax_reference_cell.json#/:

cell
========================

Any of keys under ``cells`` can be omitted from cell entries by instead specifying them in the ``settings.cell_defaults``. CharLib automatically merges any key-value pairs from ``settings.cell_defaults`` to each cell entry when characterizing the cell.
 If a key appears in a cell's entry, and in ``cell_defaults``, the value in the cell entry overrides the value from ``cell_defaults``.

:Required keywords: :ref:`04_syntax_reference_cell.json#/properties/netlist`, :ref:`04_syntax_reference_cell.json#/properties/models`, :ref:`04_syntax_reference_cell.json#/properties/inputs`, :ref:`04_syntax_reference_cell.json#/properties/outputs`, :ref:`04_syntax_reference_cell.json#/properties/functions`, :ref:`04_syntax_reference_cell.json#/properties/slews`, :ref:`04_syntax_reference_cell.json#/properties/loads`

:Allowed keywords: :ref:`04_syntax_reference_cell.json#/properties/area`, :ref:`04_syntax_reference_cell.json#/properties/clock`, :ref:`04_syntax_reference_cell.json#/properties/clock_skew`, :ref:`04_syntax_reference_cell.json#/properties/flops`, :ref:`04_syntax_reference_cell.json#/properties/footprint`, :ref:`04_syntax_reference_cell.json#/properties/functions`, :ref:`04_syntax_reference_cell.json#/properties/hold_time_range`, :ref:`04_syntax_reference_cell.json#/properties/inputs`, :ref:`04_syntax_reference_cell.json#/properties/loads`, :ref:`04_syntax_reference_cell.json#/properties/models`, :ref:`04_syntax_reference_cell.json#/properties/netlist`, :ref:`04_syntax_reference_cell.json#/properties/outputs`, :ref:`04_syntax_reference_cell.json#/properties/plots`, :ref:`04_syntax_reference_cell.json#/properties/reset`, :ref:`04_syntax_reference_cell.json#/properties/set`, :ref:`04_syntax_reference_cell.json#/properties/setup_time_range`, :ref:`04_syntax_reference_cell.json#/properties/simulation_timestep`, :ref:`04_syntax_reference_cell.json#/properties/slews`


.. _04_syntax_reference_cell.json#/properties/area:

area
++++

The physical area occupied by the cell layout, specified in ``um^2``.

:type: ``float`` or ``int``

:default: ``0``


.. _04_syntax_reference_cell.json#/properties/clock:

clock
+++++

The clock pin name and edge direction.                                The format is: ``<edge_direction> <clock_pin_name>``, where ``edge_direction`` can be one of: ``posedge`` or ``negedge``.                                E.g. ``posedge CLK`` or ``negedge CKB``.

:type: ``string``

:pattern: ``^(posedge|negedge) [a-zA-Z0-9_]+``


.. _04_syntax_reference_cell.json#/properties/clock_skew:

clock_skew
++++++++++

The slew rate to use for the clock signal in simulation.                              For sequential cells only.                              Unit is specified by ``settings.units.time``.

:type: ``float`` or ``int``


.. _04_syntax_reference_cell.json#/properties/flops:

flops
+++++

A list of storage element names. These are the names of flip-flops that Charlib puts under                                ``ff`` keyword in the generated liberty file

:type: ``array``

.. container:: sub-title

 Every element of **flops**  is:

:type: ``string``


.. _04_syntax_reference_cell.json#/properties/footprint:

footprint
+++++++++

Footprint of the cell as placed into the liberty file.

:type: ``string``


.. _04_syntax_reference_cell.json#/properties/functions:

functions
+++++++++

A list of verilog functions describing each output as logical                          function of inputs. Shall be in the same order as ``outputs``

:type: ``array``

.. container:: sub-title

 Every element of **functions**  is:

:type: ``string``


.. _04_syntax_reference_cell.json#/properties/hold_time_range:

hold_time_range
+++++++++++++++

A list of margins to be used when characterizing hold time.

:type: ``array``

.. container:: sub-title

 Every element of **hold_time_range**  is:

:type: ``float`` or ``int``


.. _04_syntax_reference_cell.json#/properties/inputs:

inputs
++++++

A list of input pin names as they appear in the cell netlist.

:type: ``array``

.. container:: sub-title

 Every element of **inputs**  is:

:type: ``string``


.. _04_syntax_reference_cell.json#/properties/loads:

loads
+++++

A list of output capacitive loads to characterize.                          Unit is specified by ``settings.units.capacitive_load``.

:type: ``array``

.. container:: sub-title

 Every element of **loads**  is:

:type: ``float`` or ``int``


.. _04_syntax_reference_cell.json#/properties/models:

models
++++++

A list of paths to the spice models for transistors used in this                             cell's netlist. If omitted, CharLib assumes each cell has no                             dependencies. 
                             * Using the syntax ``path/to/file`` will result in                             ``.include path/to/file`` in SPICE simulations. 
                             * Using the syntax ``path/to/dir`` will allow CharLib to search                               the directory for subcircuits used in a particular cell and                               include them using ``.include path/to/dir/file``.
                             * Using the syntax ``path/to/file section`` will result in                               ``.lib path/to/file section`` in SPICE simulations.

:type: ``array``

.. container:: sub-title

 Every element of **models**  is:

:type: ``string``


.. _04_syntax_reference_cell.json#/properties/netlist:

netlist
+++++++

The path to the spice file containing the netlist for this cell.

:type: ``string``


.. _04_syntax_reference_cell.json#/properties/outputs:

outputs
+++++++

A list of output pin names as they appear in the cell netlist.

:type: ``array``

.. container:: sub-title

 Every element of **outputs**  is:

:type: ``string``


.. _04_syntax_reference_cell.json#/properties/plots:

plots
+++++

A string, or list of strings specifying which plots to show                              for this cell.

May satisfy *any* of the following definitions:


.. _04_syntax_reference_cell.json#/properties/plots/anyOf/0:

0
#

:const: ``all``


.. _04_syntax_reference_cell.json#/properties/plots/anyOf/1:

1
#

:const: ``none``


.. _04_syntax_reference_cell.json#/properties/plots/anyOf/2:

2
#

:type: ``array``

.. container:: sub-title

 Every element of **2**  is:

**Allowed values:** 

- io
- delay
- energy


.. _04_syntax_reference_cell.json#/properties/reset:

reset
+++++

The asynchronous reset pin name, and edge direction. For sequential cells only. If omitted, CharLib assumes the cell does not have a reset pin. The format is ``<edge_direction> <pin_name>``. Where ``edge_direction`` can be one of: ``posedge`` or ``negedge``. E.g. ``posedge AR`` defines active high reset pin.

:type: ``string``

:pattern: ``^(posedge|negedge) [a-zA-Z0-9_]+``


.. _04_syntax_reference_cell.json#/properties/set:

set
+++

The asynchronous set pin name, and edge direction. For sequential cells only. If omitted, CharLib assumes the cell does not have a set pin. The format is ``<edge_direction> <pin_name>``, where ``edge_direction`` can be one of: ``posedge`` or ``negedge``. E.g. ``negedge AS`` defines active low set pin.

:type: ``string``

:pattern: ``^(posedge|negedge) [a-zA-Z0-9_]+``


.. _04_syntax_reference_cell.json#/properties/setup_time_range:

setup_time_range
++++++++++++++++

A list of margins to be used when characterizing setup time.

:type: ``array``

.. container:: sub-title

 Every element of **setup_time_range**  is:

:type: ``float`` or ``int``


.. _04_syntax_reference_cell.json#/properties/simulation_timestep:

simulation_timestep
+++++++++++++++++++

The simulation timestep. The unit is specified by                             ``settings.units.time``.

:type: ``float`` or ``int``

:default: ``0.001``


.. _04_syntax_reference_cell.json#/properties/slews:

slews
+++++

A list of input pin slew rates to characterize.                              Unit is specified by ``settings.units.time``.

:type: ``array``

.. container:: sub-title

 Every element of **slews**  is:

:type: ``float`` or ``int``
