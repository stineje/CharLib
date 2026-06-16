***************************************************************************************************
YAML Syntax Reference
***************************************************************************************************

This section describes syntax of CharLib YAML configuration files.
All configuration data is passed as key-value pairs in the YAML file.
The following keys are required for any valid CharLib configuration:

 - ``settings``: key-value pairs describing common settings for the whole standard cell library.
 - ``cells``: key-value pairs describing individual cells.

The general format of a CharLib configuration file is displayed below.

.. code-block:: YAML

    settings:
        Settings keywords placed here
    cells:
        <first_cell_name>:
            Cell keywords placed here
        <last_cell_name>:
            Cell keywords placed here

This example defines two cells to be characterized:

- ``first_cell_name``
- ``last_cell_name``

There may be arbitrary number of cells defined under ``cells`` keyword.
The cell name must match the ``.subckt`` name in the SPICE netlist that
represents the circuit of this cell.

.. include:: 05_settings_yaml_syntax.rst

.. include:: 05_cell_yaml_syntax.rst
