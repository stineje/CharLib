 

.. _04_syntax_reference_settings.json#/:

settings
============================

All keywords under ``settings`` are optional.                  If a keyword is not present, CharLib uses default value.

:Allowed keywords: :ref:`04_syntax_reference_settings.json#/properties/cell_defaults`, :ref:`04_syntax_reference_settings.json#/properties/debug`, :ref:`04_syntax_reference_settings.json#/properties/debug_dir`, :ref:`04_syntax_reference_settings.json#/properties/lib_name`, :ref:`04_syntax_reference_settings.json#/properties/logic_thresholds`, :ref:`04_syntax_reference_settings.json#/properties/multithreaded`, :ref:`04_syntax_reference_settings.json#/properties/named_nodes`, :ref:`04_syntax_reference_settings.json#/properties/omit_on_failure`, :ref:`04_syntax_reference_settings.json#/properties/operating_conditions`, :ref:`04_syntax_reference_settings.json#/properties/process`, :ref:`04_syntax_reference_settings.json#/properties/quiet`, :ref:`04_syntax_reference_settings.json#/properties/results_dir`, :ref:`04_syntax_reference_settings.json#/properties/simulator`, :ref:`04_syntax_reference_settings.json#/properties/temperature`, :ref:`04_syntax_reference_settings.json#/properties/units`


.. _04_syntax_reference_settings.json#/properties/cell_defaults:

cell_defaults
+++++++++++++

Default values to use for all cells.                              See ``cells`` keyword for more information.                             May contain any key-value pair valid for a :ref:`04_syntax_reference_cell.json#/` entry.

:Allowed keywords: 


.. _04_syntax_reference_settings.json#/properties/debug:

debug
+++++

Display debug messages, and store simulation SPICE files.

:type: ``boolean``

:default: ``False``


.. _04_syntax_reference_settings.json#/properties/debug_dir:

debug_dir
+++++++++

The directory where simulation SPICE files are stored if ``debug``                              keyword is set to ``True``

:type: ``string``

:default: ``debug``


.. _04_syntax_reference_settings.json#/properties/lib_name:

lib_name
++++++++

The library name to put to the exported liberty file.

:type: ``string``

:default: ``unnamed_lib``


.. _04_syntax_reference_settings.json#/properties/logic_thresholds:

logic_thresholds
++++++++++++++++

Voltage thresholds to recognize signals as logical 0 or 1.                              Values are relative to voltage given by ``named_nodes.vdd``

:Allowed keywords: :ref:`04_syntax_reference_settings.json#/properties/logic_thresholds/properties/high`, :ref:`04_syntax_reference_settings.json#/properties/logic_thresholds/properties/high_to_low`, :ref:`04_syntax_reference_settings.json#/properties/logic_thresholds/properties/low`, :ref:`04_syntax_reference_settings.json#/properties/logic_thresholds/properties/low_to_high`


.. _04_syntax_reference_settings.json#/properties/logic_thresholds/properties/high:

high
####

The minimum fraction of supply voltage recognized as a logical 1.

:type: ``float`` or ``int``

:default: ``0.8``


.. _04_syntax_reference_settings.json#/properties/logic_thresholds/properties/high_to_low:

high_to_low
###########

The threshold which must be crossed before CharLib considers                                  a signal falling from one to zero.

:type: ``float`` or ``int``

:default: ``0.5``


.. _04_syntax_reference_settings.json#/properties/logic_thresholds/properties/low:

low
###

The maximum fraction supply voltage recognized as a logical 0.

:type: ``float`` or ``int``

:default: ``0.2``


.. _04_syntax_reference_settings.json#/properties/logic_thresholds/properties/low_to_high:

low_to_high
###########

The threshold which must be crossed before Charlib considers                                  a signal rising from zero to one.

:type: ``float`` or ``int``

:default: ``0.5``


.. _04_syntax_reference_settings.json#/properties/multithreaded:

multithreaded
+++++++++++++

Run simulations in parallel, using as many threads as possible.

:type: ``boolean``

:default: ``True``


.. _04_syntax_reference_settings.json#/properties/named_nodes:

named_nodes
+++++++++++

:Allowed keywords: :ref:`04_syntax_reference_settings.json#/properties/named_nodes/properties/nwell`, :ref:`04_syntax_reference_settings.json#/properties/named_nodes/properties/pwell`, :ref:`04_syntax_reference_settings.json#/properties/named_nodes/properties/vdd`, :ref:`04_syntax_reference_settings.json#/properties/named_nodes/properties/vss`


.. _04_syntax_reference_settings.json#/properties/named_nodes/properties/nwell:

nwell
#####

Devices N-WELL terminal

:Allowed keywords: :ref:`04_syntax_reference_settings.json#/properties/named_nodes/properties/nwell/properties/name`, :ref:`04_syntax_reference_settings.json#/properties/named_nodes/properties/nwell/properties/voltage`


.. _04_syntax_reference_settings.json#/properties/named_nodes/properties/nwell/properties/name:

name
>>>>

:type: ``string``

:default: ``VNW``


.. _04_syntax_reference_settings.json#/properties/named_nodes/properties/nwell/properties/voltage:

voltage
>>>>>>>

:type: ``float`` or ``int``

:default: ``3.3``


.. _04_syntax_reference_settings.json#/properties/named_nodes/properties/pwell:

pwell
#####

Devicess P-WELL terminal

:Allowed keywords: :ref:`04_syntax_reference_settings.json#/properties/named_nodes/properties/pwell/properties/name`, :ref:`04_syntax_reference_settings.json#/properties/named_nodes/properties/pwell/properties/voltage`


.. _04_syntax_reference_settings.json#/properties/named_nodes/properties/pwell/properties/name:

name
>>>>

:type: ``string``

:default: ``VPW``


.. _04_syntax_reference_settings.json#/properties/named_nodes/properties/pwell/properties/voltage:

voltage
>>>>>>>

:type: ``float`` or ``int``

:default: ``0``


.. _04_syntax_reference_settings.json#/properties/named_nodes/properties/vdd:

vdd
###

Devices power supply terminal

:Allowed keywords: :ref:`04_syntax_reference_settings.json#/properties/named_nodes/properties/vdd/properties/name`, :ref:`04_syntax_reference_settings.json#/properties/named_nodes/properties/vdd/properties/voltage`


.. _04_syntax_reference_settings.json#/properties/named_nodes/properties/vdd/properties/name:

name
>>>>

:type: ``string``

:default: ``VDD``


.. _04_syntax_reference_settings.json#/properties/named_nodes/properties/vdd/properties/voltage:

voltage
>>>>>>>

:type: ``float`` or ``int``

:default: ``3.3``


.. _04_syntax_reference_settings.json#/properties/named_nodes/properties/vss:

vss
###

Devices ground terminal

:Allowed keywords: :ref:`04_syntax_reference_settings.json#/properties/named_nodes/properties/vss/properties/name`, :ref:`04_syntax_reference_settings.json#/properties/named_nodes/properties/vss/properties/voltage`


.. _04_syntax_reference_settings.json#/properties/named_nodes/properties/vss/properties/name:

name
>>>>

:type: ``string``

:default: ``GND``


.. _04_syntax_reference_settings.json#/properties/named_nodes/properties/vss/properties/voltage:

voltage
>>>>>>>

:type: ``float`` or ``int``

:default: ``0``


.. _04_syntax_reference_settings.json#/properties/omit_on_failure:

omit_on_failure
+++++++++++++++

Specifies whether to terminate if a cell fails to characterize                              (``False``), or continue with next cells (``True``).

:type: ``boolean``

:default: ``False``


.. _04_syntax_reference_settings.json#/properties/operating_conditions:

operating_conditions
++++++++++++++++++++

The operating conditions to set in the exported liberty file.

:type: ``string``


.. _04_syntax_reference_settings.json#/properties/process:

process
+++++++

The process condition to set in the exported liberty file.

:type: ``string``

:default: ``typ``


.. _04_syntax_reference_settings.json#/properties/quiet:

quiet
+++++

Minimize the number of messages and data Charlib displays to the                              console.

:type: ``boolean``

:default: ``False``


.. _04_syntax_reference_settings.json#/properties/results_dir:

results_dir
+++++++++++

The directory where Charlib exports characterization results.                             If omitted, CharLib creates a ``results`` directory in the                              current folder.

:type: ``string``

:default: ``results``


.. _04_syntax_reference_settings.json#/properties/simulator:

simulator
+++++++++

Specifies which Spice simulator to use

:default: ``ngspice-shared``

**Allowed values:** 

- ngspice-shared
- ngspice-subprocess
- xyce-serial
- xyce-parallel


.. _04_syntax_reference_settings.json#/properties/temperature:

temperature
+++++++++++

The temperature to use during spice simulations.

:type: ``float`` or ``int``

:default: ``25``


.. _04_syntax_reference_settings.json#/properties/units:

units
+++++

Specifies physical units to use for input and output values.

:Allowed keywords: :ref:`04_syntax_reference_settings.json#/properties/units/properties/capacitive_load`, :ref:`04_syntax_reference_settings.json#/properties/units/properties/current`, :ref:`04_syntax_reference_settings.json#/properties/units/properties/energy`, :ref:`04_syntax_reference_settings.json#/properties/units/properties/leakage_power`, :ref:`04_syntax_reference_settings.json#/properties/units/properties/pulling_resistance`, :ref:`04_syntax_reference_settings.json#/properties/units/properties/time`, :ref:`04_syntax_reference_settings.json#/properties/units/properties/voltage`


.. _04_syntax_reference_settings.json#/properties/units/properties/capacitive_load:

capacitive_load
###############

The unit of capacitance

:type: ``string``

:pattern: ``^((yocto|y)|(zepto|z)|(atto|a)|(femto|f)|(pico|p)|(nano|n)|(micro|u)|(milli|m)|()|(kilo|k)|(mega|M)|(giga|G)|(tera|T)|(peta|P)|(exa|E)|(zetta|Z)|(yotta|Y))(f|F|farads|Farads)``

:default: ``pF``


.. _04_syntax_reference_settings.json#/properties/units/properties/current:

current
#######

The unit of electrical current

:type: ``string``

:pattern: ``^((yocto|y)|(zepto|z)|(atto|a)|(femto|f)|(pico|p)|(nano|n)|(micro|u)|(milli|m)|()|(kilo|k)|(mega|M)|(giga|G)|(tera|T)|(peta|P)|(exa|E)|(zetta|Z)|(yotta|Y))(a|A|amp|amps|Amp|Amps)``

:default: ``uA``


.. _04_syntax_reference_settings.json#/properties/units/properties/energy:

energy
######

The unit of energy

:type: ``string``

:pattern: ``^((yocto|y)|(zepto|z)|(atto|a)|(femto|f)|(pico|p)|(nano|n)|(micro|u)|(milli|m)|()|(kilo|k)|(mega|M)|(giga|G)|(tera|T)|(peta|P)|(exa|E)|(zetta|Z)|(yotta|Y))(j|J|joules|Joules)``

:default: ``fJ``


.. _04_syntax_reference_settings.json#/properties/units/properties/leakage_power:

leakage_power
#############

The unit of power

:type: ``string``

:pattern: ``^((yocto|y)|(zepto|z)|(atto|a)|(femto|f)|(pico|p)|(nano|n)|(micro|u)|(milli|m)|()|(kilo|k)|(mega|M)|(giga|G)|(tera|T)|(peta|P)|(exa|E)|(zetta|Z)|(yotta|Y))(w|W|watts|Watts)``

:default: ``nW``


.. _04_syntax_reference_settings.json#/properties/units/properties/pulling_resistance:

pulling_resistance
##################

The unit of resistance

:type: ``string``

:pattern: ``^((yocto|y)|(zepto|z)|(atto|a)|(femto|f)|(pico|p)|(nano|n)|(micro|u)|(milli|m)|()|(kilo|k)|(mega|M)|(giga|G)|(tera|T)|(peta|P)|(exa|E)|(zetta|Z)|(yotta|Y))(Ω|ohm|ohms|Ohm|Ohms)``

:default: ``Ohm``


.. _04_syntax_reference_settings.json#/properties/units/properties/time:

time
####

The unit of time.

:type: ``string``

:pattern: ``^((yocto|y)|(zepto|z)|(atto|a)|(femto|f)|(pico|p)|(nano|n)|(micro|u)|(milli|m)|()|(kilo|k)|(mega|M)|(giga|G)|(tera|T)|(peta|P)|(exa|E)|(zetta|Z)|(yotta|Y))(s|seconds|Seconds)``

:default: ``ns``


.. _04_syntax_reference_settings.json#/properties/units/properties/voltage:

voltage
#######

The unit of electrical voltage.

:type: ``string``

:pattern: ``^((yocto|y)|(zepto|z)|(atto|a)|(femto|f)|(pico|p)|(nano|n)|(micro|u)|(milli|m)|()|(kilo|k)|(mega|M)|(giga|G)|(tera|T)|(peta|P)|(exa|E)|(zetta|Z)|(yotta|Y))(v|V|volts|Volts)``

:default: ``V``
