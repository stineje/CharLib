# CharLib

## Introduction
An open cell library characterizer.
Current version support timing characterization and power
characterization of combinational cells and sequential cells.  This
open-source characterization tool is modified from the  libretto
characterization tool found here :
https://github.com/snishizawa/libretto.  

## Preconditions
Make sure you change location of ngspice in gen_cmd.py

## How to use
make

## How to prepare .cmd file
.cmd file composes three blocks.
(1) common settings for library
(2) common settings for cell
(3) individual settings for cell

### common settings for library
Define common settings for target library.
(called **set command**)
| Command | Argument example | Description |
|:-----------|------------:|:------------|
| set_lib_name | OSU035 | library name |
| set_dotlib_name | OSU035.lib | .lib file name |
| set_verilog_name | OSU035.v | .v file name |
| set_cell_name_suffix | OSU035_ | cell name suffix (option) |
| set_cell_name_prefix | \_V1 | cell name prefix (option) |
| set_voltage_unit | V | voltage unit |
| set_capacitance_unit | pF | capacitance unit |
| set_resistance_unit | Ohm | resistance unit |
| set_current_unit | mA | current unit |
| set_leakage_power_unit | pW | power unit | 
| set_time_unit | ns | time unit |
| set_vdd_name | VDD | vdd name, used to detect vdd |
| set_vss_name | VSS | vss name, used to detect vss |
| set_pwell_name | VPW | pwell name, used to detect pwell (option)|
| set_nwell_name | VNW | nwell name, used to detect nwell (option)|
| set_run_sim | true | true: clean working directory and run simulation (default), false: reuse previous simulation result for .lib creation|

### common characterization conditions
Define common settings for logic cells.
(called **set command**)
| Command | Argument example | Description |
|:-----------|------------:|:------------|
| set_process | typ | define process condition (written into .lib) | 
| set_temperature | 25 | simulation temperature  (written into .lib) |
| set_vdd_voltage | 3.5 | simulation vdd voltage (unit in set_voltage_unit)|
| set_vss_voltage | 0 |  simulation vss voltage (unit in set_voltage_unit) |
| set_pwell_voltage | 0 |  simulation pwell voltage (unit in set_voltage_unit) |
| set_nwell_voltage | 3.5 |  simulation nwell voltage (unit in set_voltage_unit) |
| set_logic_threshold_high | 0.8 | logic threshold for slew table (ratio: 0~1) |
| set_logic_threshold_low | 0.2 | logic threshold for slew table (ratio: 0~1) |
| set_logic_high_to_low_threshold | 0.5 | logic threshold for delay table (ratio: 0~1) |
| set_logic_low_to_high_threshold | 0.5 | logic threshold for delay table (ratio: 0~1) |
| set_work_dir | work | simulation working directory |
| set_simulator | /usr/local/bin/ngspice | binary for ngspice | 
| set_energy_meas_low_threshold | 0.01 | threshold to define voltage low for energy calculation (ratio:0~1) |
| set_energy_meas_high_threshold | 0.99 | threshold to define voltage high for energy calculation (ratio:0~1) |
| set_energy_meas_time_extent | 4 | simulation time extension for energy calculation target large output slew (real val.) |
| set_operating_conditions | PVT_3P5V_25C | define operation condition (written into .lib) |

If common characterization commands are done, use **initialize command**
to initialize characterizor.
| Command | Argument example | Description |
|:-----------|------------:|:------------|
| initialize | n/a | initialize characteizer | 

### individual characterization commands
Define individual settings for cells.
(called **add command**)
Except **add_cell** command, other **add command** requires one argument.
**add_cell** command requires several arguments with option.

**add command** block should be start from **add_cell** command,
**characterize**and **export** commands finalize the 
simulation output into .lib and .v.
If another **add command** is applied before running
the **characterize** and **export** commands, latest 
**add command** overwrite the previous setting.

Combinational cells and sequential cells requires different 
**add command**. 

(1) **add command** for combinational cells

**add_cell** for combinational cells
(**add_cell** command should be one-line)
| Command | Argument example | Description |
|:-----------|------------:|:------------|
| add_cell |  | add cell for characterize | 
| -n cell_name | -n NAND2_1X | cell name in netlist|
| -l logic_def. | -l NAND2 | logic of target cell (\*) |
| -i inport | -i A B | inport list |
| -o outport | -o YB | outport list |
| -f verilog_func| YB = !(A\|B) | verilog function | 

Supported logic functions (\*) are listed as follow,
(Dec. 2021)
| logic def |  Description |
|:-----------|:------------|
| INV | 1-input 1-output inverter | 
| BUF | 1-input 1-output inverter | 
| AND2 | 2-input 1-output AND | 
| AND3 | 3-input 1-output AND | 
| AND4 | 4-input 1-output AND | 
| OR2 | 2-input 1-output OR | 
| OR3 | 3-input 1-output OR | 
| OR4 | 4-input 1-output OR | 
| NAND2 | 2-input 1-output NAND | 
| NAND3 | 3-input 1-output NAND | 
| NAND4 | 4-input 1-output NAND | 
| NOR2 | 2-input 1-output NOR | 
| NOR3 | 3-input 1-output NOR | 
| NOR4 | 4-input 1-output NOR | 
| XOR2 | 2-input 1-output XOR | 
| XNOR2 | 2-input 1-output XNOR | 
| SEL2 | 2-input 1-select 1-output selector | 

Other **add command**(s) for combinational cells
| Command | Argument example | Description |
|:-----------|------------:|:------------|
| add_slope | {1 4 16 64} | slope index (unit in set_time_unit) | 
| add_load  | {1 4 16 64}  | slope index (unit in set_capacitance_unit) | 
| add_area  | 1 | area (real val, no unit) | 
| add_netlist | NETLIST/INV_1X.spi | location of netlist | 
| add_model | NETLIST/model.sp | location of model file (include simulation options) | 
| add_simulation_timestep | real val/auto | simulation timestep. If **auto** is selected then simulator automatically define timestep from min. slope | 

**characterize** and **export** commands
| Command | Argument example | Description |
|:-----------|------------:|:------------|
| characterize | n/a | run characterization |
| export| n/a | export data into .lib and .v| 

(2) **add command** for sequential cells
**add_cell** for sequential cells
(**add_cell** command shoul be one-line)
| Command | Argument example | Description |
|:-----------|------------:|:------------|
| add_cell |  | add cell for characterize | 
| -n cell_name | -n DFF_ARAS_1X | cell name in netlist|
| -l logic_def. | -l DFF_PCPU_NRNS | logic of target cell (\*) |
| -i inport | -i DATA | inport |
| -c clock port | -c CLK | clock port |
| -s set inport | -s NSET | set port (optional) |
| -r reset inport | -r NRST | reset port (optional) |
| -o outport | -o Q | outport |
| -q storage | -q IQ IQN | storage elements |
| -f func| Q=IQ QN=IQN | operation function | 

Supported sequential functions (\*) are listed as follow,
(Dec. 2021)
| logic def |  Description |
|:-----------|:------------|
| DFF_PCPU | D-Flip-Flop with pos-edge clock and positive unate output | 
| DFF_PCNU | D-Flip-Flop with pos-edge clock and negative unate output | 
| DFF_NCPU | D-Flip-Flop with neg-edge clock and positive unate output | 
| DFF_NCNU | D-Flip-Flop with neg-edge clock and negative unate output | 
| DFF_PCPU_NR | D-Flip-Flop with pos-edge clock, positive unate output, async. neg-edge reset | 
| DFF_PCPU_NRNS | D-Flip-Flop with pos-edge clock, positive unate output, async. neg-edge reset, async. neg-edge set | 

Other **add command**(s) for sequential cells
| Command | Argument example | Description |
|:-----------|------------:|:------------|
| add_slope | {1 4 16 64} | slope index (unit in set_time_unit) | 
| add_load  | {1 4 16 64}  | slope index (unit in set_capacitance_unit) | 
| add_area  | 1  | area (real val, no unit) | 
| add_netlist | NETLIST/DFF_ARAS_1X.spi | location of netlist | 
| add_model | NETLIST/model.sp | location of model file (include simulation options) | 
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

**characterize** and **export** commands
| Command | Argument example | Description |
|:-----------|------------:|:------------|
| characterize | n/a | run characterization |
| export| n/a | export data into .lib and .v| 

### exit
use **exit** command to return into shell.
| Command | Argument example | Description |
|:-----------|------------:|:------------|
| exit | n/a | exit |

### sample
```txt CharLib.cmd
# common settings for library
set_lib_name OSU035
set_dotlib_name OSU035.lib
set_verilog_name OSU035.v
set_cell_name_suffix OSU035_
set_cell_name_prefix _V1
set_voltage_unit V
set_capacitance_unit pF
set_resistance_unit Ohm
set_current_unit mA
set_leakage_power_unit pW 
set_time_unit ns
set_vdd_name VDD
set_vss_name VSS
set_pwell_name VPW
set_nwell_name VNW

# characterization conditions 
set_process typ
set_temperature 25
set_vdd_voltage 3.5
set_vss_voltage 0
set_pwell_voltage 0
set_nwell_voltage 3.5
set_logic_threshold_high 0.8
set_logic_threshold_low 0.2
set_logic_high_to_low_threshold 0.5
set_logic_low_to_high_threshold 0.5
set_work_dir work
set_simulator /usr/local/bin/ngspice 
set_energy_meas_low_threshold 0.01
set_energy_meas_high_threshold 0.99
set_energy_meas_time_extent 4
set_operating_conditions PVT_3P5V_25C

# initialize workspace
initialize

## add circuit
add_cell -n INV_1X -l INV -i A -o Y -f Y=!A 
add_slope {1 4 16 64} 
add_load  {1 4 16 64} 
add_netlist NETLIST/INV_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export

add_cell -n AND2_1X -l AND2 -i A B -o Y -f Y=A*B 
add_slope {1 4 16 64} 
add_load  {1 4 16 64} 
add_netlist NETLIST/AND2_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export

## DFF, positive clock positive unate, async neg-reset, async neg-set
add_flop -n DFF_ARAS_1X -l DFF_PCPU_NRNS -i DATA -c CLK -s NSET -r NRST -o Q -q IQ IQN -f Q=IQ QN=IQN 
add_slope {1 4 16 64} 
add_load  {1 4 16 64} 
add_clock_slope auto 
add_netlist NETLIST/DFF_ARAS_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
add_simulation_setup_auto
add_simulation_hold_auto
characterize
export

exit
```
