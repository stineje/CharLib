# common settings for library
set_lib_name         OSU350
set_dotlib_name      OSU350.lib
set_verilog_name     OSU350.v
set_cell_name_suffix OSU350_
set_cell_name_prefix _V1
set_voltage_unit V
set_capacitance_unit pF
set_resistance_unit Ohm
set_current_unit mA
set_leakage_power_unit pW 
set_energy_unit fJ 
set_time_unit ns
set_vdd_name VDD
set_vss_name VSS
set_pwell_name VPW
set_nwell_name VNW
# characterization conditions 
set_process typ
set_temperature 25
set_vdd_voltage 3.3
set_vss_voltage 0
set_pwell_voltage 0
set_nwell_voltage 3.3
set_logic_threshold_high 0.8
set_logic_threshold_low 0.2
set_logic_high_to_low_threshold 0.5
set_logic_low_to_high_threshold 0.5
set_work_dir work
set_simulator /import/programs/ngspice/bin/ngspice 
set_run_sim true
set_mt_sim true
set_supress_message false
set_supress_sim_message false
set_supress_debug_message true
set_energy_meas_low_threshold 0.01
set_energy_meas_high_threshold 0.99
set_energy_meas_time_extent 10
set_operating_conditions PVT_3P5V_25C
# initialize workspace
initialize

## add circuit
add_cell -n INVX1 -l INV -i A -o Y -f Y=!A 
add_slope {0.1 4.9} 
add_load  {0.01 0.49} 
add_area 1
add_netlist spice_osu350/INVX1.spi
add_model spice_osu350/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n NAND2X1 -l NAND2 -i A B -o Y -f Y=!(A&B) 
add_slope {0.1 4.9} 
add_load  {0.01 0.49} 
add_area 1
add_netlist spice_osu350/NAND2X1.spi
add_model spice_osu350/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n NAND3X1 -l NAND3 -i A B C -o Y -f Y=!(A&B&C) 
add_slope {0.1 4.9} 
add_load  {0.01 0.49} 
add_area 1
add_netlist spice_osu350/NAND3X1.spi
add_model spice_osu350/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n NOR2X1 -l NOR2 -i A B -o Y -f Y=!(A|B) 
add_slope {0.1 4.9} 
add_load  {0.01 0.49} 
add_area 1
add_netlist spice_osu350/NOR2X1.spi
add_model spice_osu350/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n NOR3X1 -l NOR3 -i A B C -o Y -f Y=!(A|B|C) 
add_slope {0.1 4.9} 
add_load  {0.01 0.49} 
add_area 1
add_netlist spice_osu350/NOR3X1.spi
add_model spice_osu350/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n OR2X1 -l OR2 -i A B -o Y -f Y=(A|B) 
add_slope {0.1 4.9} 
add_load  {0.01 0.49} 
add_area 1
add_netlist spice_osu350/OR2X1.spi
add_model spice_osu350/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n AOI21X1 -l AOI21 -i A B C -o Y -f Y=!(C|(A&B)) 
add_slope {0.1 4.9} 
add_load  {0.01 0.49} 
add_area 1
add_netlist spice_osu350/AOI21X1.spi
add_model spice_osu350/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n AOI22X1 -l AOI22 -i A B C D -o Y -f Y=!((C&D)|(A&B)) 
add_slope {0.1 4.9} 
add_load  {0.01 0.49} 
add_area 1
add_netlist spice_osu350/AOI22X1.spi
add_model spice_osu350/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n XOR2X1 -l XOR2 -i A B -o Y -f Y=((A&!B)&(!A&B)) 
add_slope {0.1 4.9} 
add_load  {0.01 0.49} 
add_area 1
add_netlist spice_osu350/XOR2X1.spi
add_model spice_osu350/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n XNOR2X1 -l XNOR2 -i A B -o Y -f Y=((!A&!B)&(A&B)) 
add_slope {0.1 4.9} 
add_load  {0.01 0.49} 
add_area 1
add_netlist spice_osu350/XNOR2X1.spi
add_model spice_osu350/model.sp
add_simulation_timestep auto
characterize
export

exit
