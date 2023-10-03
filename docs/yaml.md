# CharLib YAML Configuration

When running in automatic mode, CharLib requires a YAML file with configuration settings to be present in the specified library directory. This document describes the key-value pairs that CharLib expects to find in that file.

## Library and Simulation Settings
Library and characterization settings are specified as key-value pairs under the `settings` key.

### Recommended Keys
While CharLib does provide defaults for all key-value pairs under the `settings` key, many of them may be incorrect for your characterization needs. For this reason, we recommend including the following keys (at minimum):

* `lib_name`: The library name to use within the exported liberty file. Defaults to 'unnamed_lib'.
* `units`: A dictionary describing the unit symbols to use for input and output values. If omitted, the default units below are used. May contain the following key-value pairs:
    * `voltage`: The unit symbol to use when expressing electrical potential values. Defaults to Volts.
    * `capacitance`: The unit symbol to use when expressing capacitance values. Defaults to picofarads.
    * `resistance`: The unit symbol to use when expressing resistance values. Defaults to Ohms.
    * `current`: The unit symbol to use when expressing electrical current values. Defaults to microamps.
    * `time`: The unit symbol to use when expressing time values. Defaults to nanoseconds.
    * `power`: The unit symbol to use when expressing power values. Defaults to nanowatts.
    * `energy`: The unit symbol to use when expressing energy values. Defaults to femtojoules.
* `named_nodes`: A dictionary mapping important node names to the names used in spice models. May contain the following key-value pairs:
    * `vdd`: A dictionary containing the name and voltage used for device supply voltage. Defaults to 'VDD' with voltage 3.3V.
    * `vss`: A dictionary containing the name and voltage used for device ground. Defaults to 'VSS' with voltage 0V.
    * `pwell`: A dictionary containing the name and voltage used for device p-wells. Defaults to 'VPW' with voltage 0V.
    * `nwell`: A dictionary containing the name and voltage used for device n-wells. Defaults to 'VNW' with voltage 3.3V.
    * Each entry in `named_nodes` contains the following keys:
        * `name`: The name used to refer to this node in spice files.
        * `voltage`: The voltage at this node.

### Optional Simulation Parameter Keys
These keys may optionally be included to specify simulation parameters:

* `simulator`: A string specifying which PySpice simulator backend to use. See the [PySpice FAQ](https://pyspice.fabrice-salvaire.fr/releases/latest/faq.html#how-to-set-the-simulator) for available options. Defaults to 'ngspice-shared'.
* `logic_thresholds`: A dictionary containing logic thresholds specified relative to `named_nodes.vdd`. May contain the following key-value pairs:
    * `low`: The maximum fraction supply voltage which registers as a logical zero. Defaults to 0.2 (20 percent of supply voltage).
    * `high`: The minimum fraction of supply voltage which registers as a logical one. Defaults to 0.8 (80 percent of supply voltage).
    * `high_to_low`: The threshold which must be crossed before a particular signal can be considered falling from one to zero. Defaults to 0.5 (50% of supply voltage).
    * `low to high`: The threshold which must be crossed before a particular signal can be considered rising from zero to one. Defaults to 0.5 (50% of supply voltage).
* `energy_measurement`: A dictionary containing parameters for energy measurement during simulation. May contain the following key-value pairs:
    * `low_threshold`: The minimum fraction of supply voltage to include in switching energy measurements. Defaults to 0.01 (1% of supply voltage).
    * `high_threshold`: The maximum fraction of supply voltage to include in switching energy measurements. Defaults to 0.99 (99% of supply voltage).
    * `time_extent`: The time interval to use for energy measurements. Defaults to 10 time units.
* `process`: The process condition to include in the exported liberty file. Empty by default.
* `temperature`: The temperature to use during spice simulations. Defaults to 25C. 
* `operating_conditions`: The operating conditions to include in the exported liberty file. Empty by default.
* `delay_model`: The delay model keyword to include in the exported liberty file. Defaults to 'table_lookup`.
* `cell_defaults`: A dictionary of default values to use for all cells. See **Cells** below for more information. May contain any key-value pair valid for a cell entry.

### Optional Behavioral Keys
These keys may optionally be included to adjust CharLib behavior:

* `dotlib_name`: The file name to use for the exported liberty file. Defaults to whatever `lib_name` is set to + '.lib'.
* `verilog_name`: The file name to use for the exported verilog file. Defaults to whatever `lib_name` is set to + '.v'.
* `cell_name_prefix`: A static prefix to append to the start of each cell name in the exported liberty file. Empty by default.
* `cell_name_suffix`: A static prefix to append to the end of each cell name in the exported liberty file. Empty by default.
* `run_simulation`: A boolean which tells CharLib whether to run spice simulation or re-use existing results in the work directory. Defaults to True.
* `multithreaded`: A boolean which tells CharLib whether to dispatch jobs to multiple threads for asynchronous execution. Defaults to True.
* `work_dir`: The directory to use for intermediate simulation spice files and other characterization artifacts. If omitted, CharLib creates a `work` directory in the current folder.
* `results_dir`: The directory to use for exporting characterization results. If omitted, CharLib creates a `results` directory in the current folder.

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

* `clock`: The clock pin name and edge direction, e.g. 'posedge CLK'.
* `flops`: A sequence of storage element names.
* `simulation`: A dictionary containing timing parameters for simulations. Contains the following key-value pairs:
    * `setup`: A dictionary containing setup time simulation parameters. Contains the following key-value pairs:
        * `highest`: The maximum setup time to check.
        * `lowest`: The minimum setup time to check.
        * `timestep`: The resolution to use for the setup time search.
    * `hold`: A dictionary containing hold time simulation parameters. Contains the following key-value pairs:
        * `highest`: The maximum hold time to check.
        * `lowest`: The minimum hold time to check.
        * `timestep`: The resolution to use for the hold time search.

### Optional Keys
These keys may optionally be included to provide additional cell documentation or improve CharLib performance.

* `area`: The physical area occupied by the cell layout. Defaults to 0 if omitted.
* `test_vectors`: A sequence of test vectors for simulation. If omitted, test vectors are instead generated based on the cell's `functions`.
    * Each test vector should be in the format `[clk, set (if present), reset (if present), flop1, ..., flopK, in1, ..., inN, out1, ..., outM]` (omit `clk, set, reset, flop1, ..., flopK` for combinational cells).
    * Including the `test_vectors` key can result in significant reductions in CharLib simulation times. If you already know the test conditions that will reveal critical paths for your cells, you should include them as test vectors under this key.
* `set`: For sequential cells only. The set pin name and edge direction, e.g. 'negedge S'. If omitted, CharLib assumes the cell does not have a set pin.
* `reset`: For sequential cells only. The reset pin name and edge direction, e.g. 'negedge R'. If omitted, CharLib assumes the cell does not have a reset pin.
* `clock_slew`: For sequential cells only. The slew rate to use for the clock signal in simulation. Defaults to 0 if omitted.
* `plots`: A string (or list of strings) specifying which plots to show for this cell. May be set to 'all', 'none', or a subset of 'io', 'delay', and 'energy'. Defaults to 'none'.

## Examples 

### Example 1: OSU350 INVX1 Characterization
The YAML below configures CharLib to perform timing and power characterization for a single-input single-output inverter cell.

``` YAML
settings:
    lib_name:           OSU350
    cell_name_prefix:   OSU350_
    cell_name_suffix:   _V1
    units:
        voltage:        V
        capacitance:    pF
        resistance:     kOhm
        current:        uA
        leakage_power:  nW
        energy:         fJ
        time:           ns
    named_nodes:
        vdd:
            name:       VDD
            voltage:    3.3
        vss:
            name:       GND
            voltage:    0
        pwell:
            name:       VPW
            voltage:    0
        nwell:
            name:       VNW
            voltage:    3.3
cells:
    INVX1:
        netlist:    osu350_spice_temp/INVX1.sp
        models:     test/osu350/model.sp
        area:       128
        inputs:     [A]
        outputs:    ['Y'] # We have to put this in quotes because YAML interprets Y as boolean True by default
        functions:  [Y=~A]
        slews: [0.015, 0.04, 0.08, 0.2, 0.4]
        loads: [0.06, 0.18, 0.42, 0.6, 1.2]
        simulation_timestep: auto
```


### Example 2: Characterizing Multiple OSU350 Combinational Cells
The YAML below configures CharLib to perform timing and power characterization for full adder and half adder cells. Note the contents of `settings` are mostly the same, but several cell parameters are moved into `settings.cell_defaults` to avoid repeating them for each cell.

``` YAML
settings:
    lib_name:           OSU350
    cell_name_prefix:   _V1
    cell_name_suffix:   OSU350_
    units:
        voltage:        V
        capacitance:    pF
        resistance:     kOhm
        current:        uA
        leakage_power:  nW
        energy:         fJ
        time:           ns
    named_nodes:
        vdd:
            name:       VDD
            voltage:    3.3
        vss:
            name:       GND
            voltage:    0
        pwell:
            name:       VPW
            voltage:    0
        nwell:
            name:       VNW
            voltage:    3.3
    cell_defaults:
        model: test/osu350/model.sp
        slews: [0.015, 0.04, 0.08, 0.2, 0.4]
        loads: [0.06, 0.18, 0.42, 0.6, 1.2]
        simulation_timestep: auto
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
```

### Example 3: OSU350 DFFSR Characterization
TODO