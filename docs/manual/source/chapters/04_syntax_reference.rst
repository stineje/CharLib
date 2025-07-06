***************************************************************************************************
Syntax reference
***************************************************************************************************

This section describes syntax of CharLibs YAML configuration file.
All configuration data is passed as key-value pairs in the YAML file.
The format of YAML contains two obligatory keywords:

 - ``settings``
 - ``cells``

 An example of the file is following:

.. code-block:: YAML

    settings:
        Settings keywords placed here
    cells:
        <first_cell_name>:
            Cell keywords placed here
        <last_cell_name>:
            Cell keywords placed here

The example above defines two cells to be characterized:

- ``first_cell_name``
- ``last_cell_name``

There may be arbitrary number of cells defined under ``cells`` keyword.
The cell name must match the ``.subckt`` name in the SPICE netlist that
represents the circuit of this cell.

.. include:: 04_syntax_reference_settings.rst

.. include:: 04_syntax_reference_cell.rst
