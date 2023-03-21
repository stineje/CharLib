# library settings
set_lib_name         OSU350
set_cell_name_suffix OSU350_
set_cell_name_prefix _V1
set_voltage_unit V
set_capacitance_unit pF
set_resistance_unit kOhm
set_current_unit uA
set_leakage_power_unit nW 
set_energy_unit fJ 
set_time_unit ns
set_vdd_name VDD
set_vss_name GND
set_pwell_name VPW
set_nwell_name VNW

# characterization settings
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
set_run_sim true
set_mt_sim true
set_suppress_message false
set_suppress_sim_message false
set_suppress_debug_message true
set_energy_meas_low_threshold 0.01
set_energy_meas_high_threshold 0.99
set_energy_meas_time_extent 10
set_operating_conditions typical

# initialize workspace
initialize

add_cell -n HAX1 -i A B -o YC YS -f YC=A&B YS=A^B
add_slope {0.015 0.04 0.08 0.2 0.4} 
add_load  {0.06 0.18 0.42 0.6 1.2} 
add_area 320
add_netlist spice_temp/HAX1.sp
add_model test/spice_osu350/model.sp
add_simulation_timestep auto

add_cell -n FAX1 -i A B C -o YC YS -f YC=(A&B)|(C&(A^B)) YS=A^B^C
add_slope {0.015 0.04 0.08 0.2 0.4} 
add_load  {0.06 0.18 0.42 0.6 1.2} 
add_area 320
add_netlist spice_temp/FAX1.sp
add_model test/spice_osu350/model.sp
add_simulation_timestep auto

characterize
export

exit
