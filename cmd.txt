# common settings for library
set_lib_name         OSD350
set_dotlib_name      OSD350.lib
set_verilog_name     OSD350.v
set_cell_name_suffix OSD350_
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
set_simulator /usr/local/bin/ngspice 
set_run_sim true
set_mt_sim true
set_energy_meas_low_threshold 0.01
set_energy_meas_high_threshold 0.99
set_energy_meas_time_extent 10
set_operating_conditions PVT_3P5V_25C
# initialize workspace
initialize

## add circuit
add_cell -n INV_1X -l INV -i A -o YB -f YB=!A 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/INV_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n NAND2_1X -l NAND2 -i A B -o YB -f YB=!(A&B) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/NAND2_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n NAND3_1X -l NAND3 -i A B C -o YB -f YB=!(A&B&C) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/NAND3_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n NAND4_1X -l NAND4 -i A B C D -o YB -f YB=!(A&B&C&D) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/NAND4_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n NOR2_1X -l NOR2 -i A B -o YB -f YB=!(A|B) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/NOR2_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n NOR3_1X -l NOR3 -i A B C -o YB -f YB=!(A|B|C) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/NOR3_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n NOR4_1X -l NOR4 -i A B C D -o YB -f YB=!(A|B|C|D) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/NOR4_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n AND2_1X -l AND2 -i A B -o Y -f Y=(A&B) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/AND2_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n AND3_1X -l AND3 -i A B C -o Y -f Y=(A&B&C) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/AND3_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n AND4_1X -l AND4 -i A B C D -o Y -f Y=(A&B&C&D) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/AND4_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n OR2_1X -l OR2 -i A B -o Y -f Y=(A|B) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/OR2_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n OR3_1X -l OR3 -i A B C -o Y -f Y=(A|B|C) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/OR3_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n OR4_1X -l OR4 -i A B C D -o Y -f Y=(A|B|C|D) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/OR4_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n AOI21_1X -l AOI21 -i A1 A2 B -o YB -f YB=!(B|(A1&A2)) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/AOI21_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n AOI22_1X -l AOI22 -i A1 A2 B1 B2 -o YB -f YB=!((B1&B2)|(A1&A2)) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/AOI22_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n OAI21_1X -l OAI21 -i A1 A2 B -o YB -f YB=!(B&(A1|A2)) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/OAI21_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n OAI22_1X -l OAI22 -i A1 A2 B1 B2 -o YB -f YB=!((B1|B2)&(A1|A2)) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/OAI22_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n AO21_1X -l AO21 -i A1 A2 B -o Y -f Y=(B|(A1&A2)) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/AO21_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n AO22_1X -l AO22 -i A1 A2 B1 B2 -o Y -f Y=((B1&B2)|(A1&A2)) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/AO22_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n OA21_1X -l OA21 -i A1 A2 B -o Y -f Y=(B&(A1|A2)) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/OA21_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n OA22_1X -l OA22 -i A1 A2 B1 B2 -o Y -f Y=((B1|B2)&(A1|A2)) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/OA22_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n XOR2_1X -l XOR2 -i A B -o Y -f Y=((A&!B)&(!A&B)) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/XOR2_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n XNOR2_1X -l XNOR2 -i A B -o Y -f Y=((!A&!B)&(A&B)) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/XNOR2_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export


## add circuit
add_cell -n SEL2_1X -l SEL2 -i IN1 IN2 SEL -o Y -f Y=((A&!B)&(!A&B)) 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_area 1
add_netlist NETLIST/XOR2_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
characterize
export

## add circuit
add_flop -n DFF_ARAS_1X -l DFF_PCPU_NRNS -i DATA -c CLK -s NSET -r NRST -o Q -q Q QN -f Q=IQ QN=IQN 
add_slope {0.1 0.7 4.9} 
add_load  {0.01 0.1 1.0} 
add_clock_slope auto 
add_area 1
add_netlist NETLIST/DFF_ARAS_1X.spi
add_model NETLIST/model.sp
add_simulation_timestep auto
add_simulation_setup_auto
add_simulation_hold_auto
characterize
export
exit
