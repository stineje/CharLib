***************************************************************************************************
Procedures
***************************************************************************************************

This section describes the structure of CharLib's measurement procedures and provides guidance on
how to add your own custom measurement routines.

====================================================================================================
Introduction and Structure
====================================================================================================

In CharLib, a procedure is a routine used to make one or more specific measurements on a standard
cell. Each procedure consists of two components:

1. A generator used to marshall a list of measurement tasks by iterating over all possible cell
   test configurations. This generator yields tuples of the form ``(Callable, *args)``, and is
   registered to a list of procedures using the ``@register`` decorator.
2. A function (the ``Callable`` above) which returns a Liberty ``Group`` object populated with
   measurement data.

Procedures can be found in `CharLib's source code <https://github.com/stineje/CharLib/tree/main>`_
in the `charlib/characterizer/procedures directory <https://github.com/stineje/CharLib/tree/main/charlib/characterizer/procedures>`_.

====================================================================================================
Registering a Procedure
====================================================================================================

Each procedure's generator must be registered to the characterizer using the ``@register``
decorator. This decorator serves two purposes:

1. It saves the generator to a list of registered procedures. These are looked up by name and
   executed during cell analysis (the first phase of CharLib execution) to build a list of
   characterization tasks.
2. It stores a list of simulation parameters specifically required by each procedure. This is used
   to make sure all cell test configurations are measured.

.. note::

    Multiple procedures may be registered for a specific task. For example,
    ``combinational_average`` and ``combinational_worst_case`` are both valid options for the key
    ``settings.simulation.combinational_delay_procedure``. Only one procedure is used at runtime
    for combinational delay measurements. If not specified in the YAML configuration, the default
    ``combinational_worst_case`` procedure is used.

====================================================================================================
Custom Procedures
====================================================================================================

To create a custom measurement procedure, you must:

1. Create a new Python file and add a generator and callble as described above. Use the existing
   procedures as reference material to build your own.
2. Register your procedure using the ``@register`` decorator. Make sure to include any parameters
   from the cell configuration YAML as string arguments.
3. Document any new YAML parameters in ``charlib/config/syntax.py``.
4. Import your procedure in ``charlib/characterizer/characterizer.py``.

Once the above steps are complete, you should be able to select your procedure using the
appropriate ``settings.simulation`` key in your configuration YAML file. For example, if you wanted
to add a new procedure called "my_min_pulse_width" for measuring minimum pulse width, you would
include the following in your YAML configuration:

.. code-block:: YAML

    settings:
        simulation:
            min_pulse_width_constraint_procedure: my_min_pulse_width
        ...

Assuming a procedure called ``my_min_pulse_width`` is registered, CharLib will now call that
procedure when performing minumum pulse width measurements. For a complete list of available
procedure types, see the :ref:`05_settings_yaml_syntax.json#/properties/simulation` key in the YAML
syntax reference.
