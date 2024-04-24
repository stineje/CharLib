# CharLib YAML Configuration

CharLib requires a YAML file with configuration settings to be present in the specified library directory. This document describes the key-value pairs that CharLib expects to find in that file.

## Library and Simulation Settings
Library and characterization settings are specified as key-value pairs under the `settings` key.

### Recommended Keys
While CharLib does provide defaults for all key-value pairs under the `settings` key, many of them may be incorrect for your characterization needs. For this reason, we recommend including the following keys (at minimum):

* `lib_name`: The library name to use within the exported liberty file. Defaults to 'unnamed_lib'.
* `units`: A dictionary describing the unit symbols to use for input and output values. If omitted, the default units below are used. May contain the following key-value pairs:
    * `time`: The unit symbol to use when expressing time values. Defaults to nanoseconds.
    * `voltage`: The unit symbol to use when expressing electrical potential values. Defaults to Volts.
    * `current`: The unit symbol to use when expressing electrical current values. Defaults to microamps.
    * `capacitive_load`: The unit symbol to use when expressing capacitance values. Defaults to picofarads.
    * `pulling_resistance`: The unit symbol to use when expressing resistance values. Defaults to Ohms.
    * `leakage_power`: The unit symbol to use when expressing power values. Defaults to nanowatts.
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
    * `low_to_high`: The threshold which must be crossed before a particular signal can be considered rising from zero to one. Defaults to 0.5 (50% of supply voltage).
* `process`: The process condition to include in the exported liberty file. Defaults t0 1.
* `temperature`: The temperature to use during spice simulations. Defaults to 25C. 
* `operating_conditions`: The operating conditions to include in the exported liberty file. Empty by default.
* `cell_defaults`: A dictionary of default values to use for all cells. See **Cells** below for more information. May contain any key-value pair valid for a cell entry.

### Optional Behavioral Keys
These keys may optionally be included to adjust CharLib behavior:

* `multithreaded`: A boolean which tells CharLib whether to dispatch jobs to multiple threads for asynchronous execution. Defaults to True.
* `results_dir`: The directory to use for exporting characterization results. If omitted, CharLib creates a `results` directory in the current folder.
* `debug`: A boolean which tells CharLib to display debug messages and store simulation SPICE files. Defaults to False.
* `debug_dir`: The directory to use when storing simulation debug SPICE files. Defaults to `debug`.

## Cells
Specific cells to characterize are specified as entries under the `cells` key.

### Required Keys for all Cell Entries
Each cell entry is a dictionary with (at minimum) the following required keys:

* `netlist`: The path to the spice file containing the netlist for this cell.
* `models`: A sequence of paths to the spice models for transistors used in this cell's netlist. If omitted, CharLib assumes each cell has no dependencies.
	* Using the syntax `path/to/file` will result in `.include path/to/file` in SPICE simulations.
	* Using the syntax `path/to/dir` will allow CharLib to search the directory for subcircuits used in a particular cell and include them using `.include path/to/dir/file`.
	* Using the syntax `path/to/file section` will result in `.lib path/to/file section` in SPICE simulations.
* `inputs`: A sequence of input pin names.
* `outputs`: A sequence of output pin names.
* `functions`: A sequence of verilog functions describing how the inputs relate to each output.
* `slews`: A sequence of input pin slew rates to test with.
* `loads`: A sequence of output capacitive loads to test with.
* `simulation_timestep`: The simulation timestep.

Several of these keys can easily be omitted from cell entries by instead specifying them in the `settings.cell_defaults` dictionary. Any key-value pairs in `settings.cell_defaults` are automatically merged into each cell entry when adding the cell to the characterizer. If a key appears in a cell's entry and in `cell_defaults`, the value in the cell entry overrides the value from `cell_defaults`.

> If you prefer to keep individual cell configurations separate from your toplevel CharLib configuration file, YAML files for individual cells may be specified using the syntax `cell_name: relative/path/to/cell/from/current/dir`. This gives you the option of, for example, storing your cell YAML files in the same place as your cell SPICE models.

### Additional Required Keys for Sequential Cell Entries
Sequential Cell entries must specify the following key-value pairs in addition to the above:

* `clock`: The clock pin name and edge direction, e.g. 'posedge CLK'.
* `flops`: A sequence of storage element names.
* `setup_time_range`: 
* `hold_time_range`: 

### Optional Keys
These keys may optionally be included to provide additional cell documentation or improve CharLib performance.

* `area`: The physical area occupied by the cell layout. Defaults to 0 if omitted.
* `set`: For sequential cells only. The set pin name and edge direction, e.g. 'negedge S'. If omitted, CharLib assumes the cell does not have a set pin.
* `reset`: For sequential cells only. The reset pin name and edge direction, e.g. 'negedge R'. If omitted, CharLib assumes the cell does not have a reset pin.
* `clock_slew`: For sequential cells only. The slew rate to use for the clock signal in simulation. Defaults to 0 if omitted.
* `plots`: A string (or list of strings) specifying which plots to show for this cell. May be set to 'all', 'none', or a subset of 'io', 'delay', and 'energy'. Defaults to 'none'.

## Examples 

### Example 1: OSU350 INVX1 Characterization
The YAML below configures CharLib to perform timing and power characterization for a single-input single-output inverter cell.

``` YAML
settings:
    lib_name:           test_OSU350
    units:
        time:               ns
        voltage:            V
        current:            uA
        pulling_resistance: kOhm
        leakage_power:      nW
        capacitive_load:    pF
        energy:             fJ
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
        models:     [test/osu350/model.sp]
        area:       128
        inputs:     [A]
        outputs:    ['Y'] # We have to put this in quotes because YAML interprets Y as boolean True by default
        functions:  [Y=!A]
        slews: [0.015, 0.04, 0.08, 0.2, 0.4]
        loads: [0.06, 0.18, 0.42, 0.6, 1.2]
```


### Example 2: Characterizing Multiple OSU350 Combinational Cells
The YAML below configures CharLib to perform timing and power characterization for full adder and half adder cells. Note the contents of `settings` are mostly the same, but several cell parameters are moved into `settings.cell_defaults` to avoid repeating them for each cell.

``` YAML
settings:
    lib_name:           test_OSU350
    units:
        time:               ns
        voltage:            V
        current:            uA
        pulling_resistance: kOhm
        leakage_power:      nW
        capacitive_load:    pF
        energy:             fJ
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
```

### Example 3: OSU350 DFFSR Characterization
``` YAML
settings:
    lib_name:           test_OSU350
    units:
        time:               ns
        voltage:            V
        current:            uA
        pulling_resistance: kOhm
        leakage_power:      nW
        capacitive_load:    pF
        energy:             fJ
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
        functions:
            - Q<=D
```

### Example 4: Characterizing Multiple GF180 Cells
``` YAML
settings:
    lib_name:           test_GF180
    units:
        time:               ns
        voltage:            V
        current:            uA
        pulling_resistance: kOhm
        leakage_power:      nW
        capacitive_load:    pF
        energy:             fJ
    named_nodes:
        vdd:
            name:       VDD
            voltage:    3.3
        vss:
            name:       VSS
            voltage:    0
        pwell:
            name:       VPW
            voltage:    0
        nwell:
            name:       VNW
            voltage:    3.3
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
```
