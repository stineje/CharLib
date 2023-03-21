# CharLib

## Introduction
This open-source characterization tool is modified from [libretto](https://github.com/snishizawa/).

CharLib is an open cell library characterizer. The current version supports timing characterization and power characterization of combinational and sequential cells. We are currently working on expanding the characterization profile as well as scope of parameters.

CharLib uses OSU 0.35um SCMOS library for testing. This will be expanded to SKY130 and GF180 shortly.

## Preconditions
Make sure you have `ngspice` installed. If `ngspice` is not in your `PATH`, you may have to specify the absolute path to the `ngspice` binary using the `set_simulator` command. 

## How to use
There is a simple Makefile that can run the characterization for a target library of standard cells. This defaults to OSU350. SKY130 and GF180 targets will be added in the future. 

CharLib has three distinct operating modes:

* Shell mode (default)
* Batchfile mode
* Automatic mode

Using CharLib in shell or batchfile mode is a very manual process: you enter commands to configure the characterizer and add your standard cells, then execute characterization and export the results. Automatic mode requires a bit of setup, but can be much easier for large standard cell libraries.


### Shell Mode
Syntax: `python3 CharLib.py`

Shell mode starts an interactive shell where users can enter a single command at a time. See **Command Syntax** for information on available commands.


### Batchfile Mode
Syntax: `python3 CharLib.py -b BATCHFILE`

This mode takes in a text file BATCHFILE with one command on each line. Typically these files use the file extension ".cmd". You can include comments by starting the line with "#". 

Batch files usually have three main sections: 

1. Library configuration
    - Here library-wide settings (such as output filenames) are configured. 
2. Simulation configuration
    - Here simulation data (such as VDD and VSS names and voltages) are configured.
3. Cell-specific settings
    - Here settings for each cell are provided. This varies depending on cell type, but usually includes cell name and SPICE files at minimum.

See **Command Syntax** below for more information.


### Automatic Mode (Coming soon)
Syntax: `python3 CharLib.py -l LIBRARY_PATH`

This mode parses a library of standard cells and attempts to generate a batchfile for that library. If successful, the batchfile is run immediately.

There is some setup work required prior to running in automatic mode. Library and simulation configuration details must be added to a "lib_settings.json" file in directory specified by LIBRARY_PATH. An example of what this should look like is provided in the test/spice_osu350 folder. 

If CharLib successfully generates a batchfile for the standard cell library, it will place that batchfile in the directory specified by LIBRARY_PATH. Subsequent runs in automatic mode will check for this batchfile and use it to run characterization. This allows users to make tweaks to the generated batchfile if desired. If you want to generate a new batchfile, you should delete the existing batchfile prior to running CharLib. 


## Command Syntax

### Library Configuration Commands
These commands define configuration settings for all standard cells in the target library.

| Command                | Argument example | Description |
| ---------------------- | ---------------- | ----------- |
| set_lib_name           | OSU035           | library name. (Default: unnamed_lib) |
| set_dotlib_name        | OSU035.lib       | .lib file name. If unset, uses library name + .lib. |
| set_verilog_name       | OSU035.v         | .v file name. If unset, uses library name + .v. |
| set_cell_name_suffix   | OSU035_          | cell name suffix (optional) |
| set_cell_name_prefix   | _V1              | cell name prefix (optional) |
| set_voltage_unit       | V                | voltage unit. (Default: V) |
| set_capacitance_unit   | pF               | capacitance unit. (Default: pF) |
| set_resistance_unit    | Ohm              | resistance unit. (Default: Ω) |
| set_current_unit       | mA               | current unit. (Default: μA) |
| set_leakage_power_unit | pW               | power unit. (Default: nW) | 
| set_time_unit          | ns               | time unit. (Default: ns) |
| set_vdd_name           | VDD              | vdd name. Used to detect vdd. (Default: VDD) |
| set_vss_name           | VSS              | vss name. Used to detect vss. (Default: VSS) |
| set_pwell_name         | VPW              | pwell name. Used to detect pwell. (Default: VPW) |
| set_nwell_name         | VNW              | nwell name. Used to detect nwell. (Default: VNW) |
| set_run_sim            | True             | If false, reuse existing results to generate .lib and .v files. (Default: True) |


### Simulation Configuration Commands
These commands define simulation settings for all standard cells in the target library. 

| Command                         | Argument example | Description |
| ------------------------------- | ---------------- | ----------- |
| set_process                     | typ              | define process condition (written into .lib) | 
| set_temperature                 | 25               | simulation temperature  (written into .lib) |
| set_vdd_voltage                 | 3.5              | simulation vdd voltage (unit in set_voltage_unit)|
| set_vss_voltage                 | 0                | simulation vss voltage (unit in set_voltage_unit) |
| set_pwell_voltage               | 0                | simulation pwell voltage (unit in set_voltage_unit) |
| set_nwell_voltage               | 3.5              | simulation nwell voltage (unit in set_voltage_unit) |
| set_logic_threshold_high        | 0.8              | logic threshold for slew table (ratio: 0~1) |
| set_logic_threshold_low         | 0.2              | logic threshold for slew table (ratio: 0~1) |
| set_logic_high_to_low_threshold | 0.5              | logic threshold for delay table (ratio: 0~1) |
| set_logic_low_to_high_threshold | 0.5              | logic threshold for delay table (ratio: 0~1) |
| set_work_dir                    | work             | simulation working directory |
| set_simulator                   | /usr/bin/ngspice | binary for ngspice | 
| set_energy_meas_low_threshold   | 0.01             | threshold to define voltage low for energy calculation (ratio:0~1) |
| set_energy_meas_high_threshold  | 0.99             | threshold to define voltage high for energy calculation (ratio:0~1) |
| set_energy_meas_time_extent     | 4                | simulation time extension for energy calculation target large output slew (real val.) |
| set_operating_conditions        | PVT_3P5V_25C     | define operation condition (written into .lib) |

Once library and simulation configuration is complete, use `initialize` to set up the characterizer work directory.
| Command    | Argument example | Description           |
| ---------- | ---------------- | --------------------- |
| initialize | n/a              | Set up work directory | 

### Cell-specific Configuration Commands
These commands define settings specific to a single cell. 

Cell-specific commands typically show up in blocks that initialize the cell and then add characterization parameters. After cells are added, they can be characterized using the `characterize` command.

Cell command blocks should always start out with the `add_cell` or `add_flop` command. Use `add_cell` for combinational cells and `add_flop` with sequential cells. Unlike most other commands, `add_cell` and `add_flop` have several required arguments.

#### `add_cell`
This command should be on one line, e.g. `add_cell -n AND2X1 -i A B -o Y -f Y=A&B`
| Command         | Argument example | Description |
| --------------- | ---------------- | ----------- |
| add_cell        |                  | Add a combinational cell to characterize |
| -n cell_name    | -n HAX1          | Cell name in netlist |
| -i inport       | -i A B           | List of input port names |
| -o outport      | -o YC YS         | List of output port names |
| -f verilog_func | -f YC=A&B YS=A^B | List of verilog functions describing how each output is determined from the inputs |

> Note: The `-f` argument only accepts verilog functions using &, ^, |, ~, !, and parentheses. Other operators are not currently supported.

Other **add** commands for combinational cells:
| Command                 | Argument example     | Description |
| ----------------------- | -------------------- | ----------- |
| add_slope               | {1 4 16 64}          | input slew rates to test (unit in set_time_unit) |
| add_load                | {1 4 16 64}          | output capacitive loads to test (unit in set_capacitance_unit) |
| add_area                | 1                    | area (real val, no unit) |
| add_netlist             | spice_dir/INVX1.spi  | location of netlist |
| add_model               | spice_dir/model.sp   | location of model file (include simulation options) |
| add_simulation_timestep | auto                 | simulation timestep. If set to `auto`, the simulator will use 1/10th of the minimum input slew rate as the timestep. | 

#### `add_flop`
Just like `add_cell`, the `add_flop` command should be on one line.
| Command      | Argument example | Description |
| ------------ | ---------------- |------------|
| add_flop     |                  | Add a sequential cell to characterize |
| -n cell_name | -n DFFSR         | Cell name in netlist|
| -i inport    | -i DATA          | List of input port names |
| -c clockport | -c CLK           | Clock port name |
| -s setport   | -s SET           | Set port name (if present) |
| -r resetport | -r RST           | Reset port name (if present) |
| -o outport   | -o Q             | List of output port names |
| -q storage   | -q IQ IQN        | List of storage element names |
| -f func      | Q=IQ QN=IQN      | List of functions describing how each output relates to the inputs and storage elements |

Other **add** commands for sequential cells:
| Command | Argument example | Description |
|-----------|------------|------------|
| add_slope | {1 4 16 64} | slope index (unit in set_time_unit) | 
| add_load  | {1 4 16 64}  | slope index (unit in set_capacitance_unit) | 
| add_area  | 1  | area (real val, no unit) | 
| add_netlist | spice_XXXX/DFFSR.spi | location of netlist | 
| add_model | spice_XXXX/model.sp | location of model file (include simulation options) | 
| add_clock_slope | real val/auto | slope for clock. If **auto** is selected then simulator automatically select min. slope |
| add_simulation_timestep | real val/auto | simulation timestep. If **auto** is selected then simulator automatically define timestep from min. slope | 
| add_simulation_setup_auto | n/a | automatically set setup simulation time (lowest, highest, timestep) |
| add_simulation_setup_lowest | -10 | manually set lowest time for setup simulation (real val, unit in set_time_unit) |
| add_simulation_setup_highest | 16 | manually set highst time for setup simulation (real val, unit in set_time_unit) |
| add_simulation_setup_timestep | 5 | manually set timestep for setup simulation (real val, unit in set_time_unit) |
| add_simulation_hold_auto | n/a | automatically set hold simulation time (lowest, highest, timestep) |
| add_simulation_hold_lowest | -10 | manually set lowest time for hold simulation (real val, unit in set_time_unit) |
| add_simulation_hold_highest | 16 | manually set highst time for hold simulation (real val, unit in set_time_unit) |
| add_simulation_hold_timestep | 5 | manually set timestep for hold simulation (real val, unit in set_time_unit) |

#### `charaacterize` and `export`
| Command      | Argument example | Description |
| ------------ | ---------------- | ----------- |
| characterize | AND2X1 OR2X1     | Run characterization for the specified cells, or all cells if no arguments are passed. |
| export       | n/a              | export characterization result into .lib and .v files |

### `exit`
| Command | Argument example | Description |
| ------- | ---------------- | ----------- |
| exit    | n/a              | Exit to the parent shell.|

