# CharLib YAML Configuration

When running in automatic mode, CharLib requires a YAML file with configuration settings to be present in the specified library directory. This document describes the key-value pairs that CharLib expects to find in that file.

## Library and Simulation Settings
Library and characterization settings are specified as key-value pairs under the `settings` key.

### Required Keys
TODO

### Optional Keys
TODO

## Cells
Specific cells to characterize are specified as entries under the `cells` key. 

### Required Keys for all Cell Entries
Each cell entry is a dictionary with (at minimum) the following required keys:

* `netlist`: The path to the spice file containing the netlist for this cell.
* `model`: The path to the spice models for transistors used in this cell's netlist.
* `inputs`: A sequence of input pin names.
* `outputs`: A sequence of output pin names.
* `functions`: A sequence of verilog functions describing how the inputs relate to each output.
* `slews`: A sequence of input pin slew rates to test with.
* `loads`: A sequence of output capacitive loads to test with.
* `simulation_timestep`: The simulation timestep.

Several of these keys can easily be omitted from cell entries by instead specifying them in the `settings.cell_defaults` dictionary. Any key-value pairs in `settings.cell_defaults` are automatically merged into each cell entry when adding the cell to the characterizer. If a key appears in a cell's entry and in `cell_defaults`, the value in the cell entry overrides the value from `cell_defaults`.

### Additional Required Keys for Sequential Cell Entries
Sequential Cell entries must specify the following key-value pairs in addition to the above:

* `clock_pin`: The pin name for the clock pin.
* `flops`: A sequence of storage element names.
* `simulation`: A dictionary containing timing parameters for simulations. Contains the following key-value pairs:
    * `setup`: A dictionary containing setup time simulation parameters. Contains the following key-value pairs:
        * `highest`: The maximum setup time to check.
        * `lowest`: The minimum setup time to check.
        * `timestep`: The simulation timestep to use during setup time search.
    * `hold`: A dictionary containing hold time simulation parameters. Contains the following key-value pairs:
        * `highest`: The maximum hold time to check.
        * `lowest`: The minimum hold time to check.
        * `timestep`: The simulation timestep to use during hold time search.

### Optional Keys
These keys may optionally be included to provide additional cell documentation or improve CharLib performance.

* `area`: The physical area occupied by the cell layout. Defaults to 0 if omitted.
* `test_vectors`: A sequence of test vectors for simulation. Each test vector should be in the format `[clk, set, reset, flop1, ..., flopK, in1, ..., inN, out1, ..., outM]` (omit `clk, set, reset, flop1, ..., flopK` for combinational cells). If omitted, test vectors are instead generated based on the cell's `functions`.
    * > Including the `test_vectors` key can result in significant reductions in CharLib simulation times. If you already know the test conditions that will reveal critical paths for your cells, you should include them as test vectors under this key.
* `set_pin`: The pin name for the set pin on sequential cells. If omitted, CharLib assumes the cell does not have a set pin.
* `reset_pin`: The pin name for the reset pin on sequential cells. If omitted, CharLib assumes the cell does not have a reset pin.
* `clock_slew`: The slew rate to use for the clock signal in simulation. Defaults to 0 if omitted.