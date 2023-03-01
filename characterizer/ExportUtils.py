
import re, sys

from characterizer.LibrarySettings import LibrarySettings
from characterizer.LogicCell import LogicCell, SequentialCell
from characterizer.Harness import CombinationalHarness

def exportFiles(targetLib, targetCell):
    if not targetLib.is_exported:
        exportLib(targetLib, targetCell)
    if targetLib.is_exported and not targetCell.is_exported:
        ## export comb. logic
        if not isinstance(targetCell, SequentialCell):
            exportCombinationalCell(targetLib, targetCell)
            exportVerilog(targetLib, targetCell)
        ## export seq. logic
        else:
            exportSequentialCell(targetLib, targetCell)
            exportVerilogFlop(targetLib, targetCell)

## export library definition to .lib
def exportLib(target_lib: LibrarySettings, target_cell: LogicCell):
    """Export library definition to liberty file"""
    outlines = []
    ## general settings
    outlines.append(f'library ({target_lib.lib_name}) {{\n')
    outlines.append(f'  delay_model : "{target_lib.delay_model}";\n')
    outlines.append(f'  capacitive_load_unit (1,{str(target_lib.units.capacitance)});\n')
    outlines.append(f'  current_unit : "1{str(target_lib.units.current)}";\n')
    outlines.append(f'  leakage_power_unit : "1{str(target_lib.units.power)}";\n')
    outlines.append(f'  pulling_resistance_unit : "1{str(target_lib.units.resistance)}";\n')
    outlines.append(f'  time_unit : "1{str(target_lib.units.time)}";\n')
    outlines.append(f'  voltage_unit : "1{str(target_lib.units.voltage)}";\n')
    outlines.append(f'  voltage_map ({str(target_lib.vdd.name)}, {str(target_lib.vdd.voltage)});\n')
    outlines.append(f'  voltage_map ({str(target_lib.vss.name)}, {str(target_lib.vss.voltage)});\n')
    outlines.append(f'  voltage_map (GND , {str(target_lib.vss.voltage)});\n')
    outlines.append(f'  default_cell_leakage_power : 0;\n')
    outlines.append(f'  default_fanout_load : 1;\n')
    outlines.append(f'  default_max_transition : 1000;\n')
    outlines.append(f'  default_input_pin_cap : 0;\n')
    outlines.append(f'  default_inout_pin_cap : 0;\n')
    outlines.append(f'  default_leakage_power_density : 0;\n')
    outlines.append(f'  default_max_fanout : 100;\n')
    outlines.append(f'  default_output_pin_cap : 0;\n')
    outlines.append(f'  in_place_swap_mode : match_footprint;\n')
    outlines.append(f'  input_threshold_pct_fall : {str(target_lib.logic_high_to_low_threshold*100)};\n')
    outlines.append(f'  input_threshold_pct_rise : {str(target_lib.logic_low_to_high_threshold*100)};\n')
    outlines.append(f'  nom_process : 1;\n')
    outlines.append(f'  nom_temperature : "{str(target_lib.temperature)}";\n')
    outlines.append(f'  nom_voltage : "{str(target_lib.vdd.voltage)}";\n')
    outlines.append(f'  output_threshold_pct_fall : {str(target_lib.logic_high_to_low_threshold*100)};\n')
    outlines.append(f'  output_threshold_pct_rise : {str(target_lib.logic_low_to_high_threshold*100)};\n')
    outlines.append(f'  slew_derate_from_library : 1;\n')
    outlines.append(f'  slew_lower_threshold_pct_fall : {str(target_lib.logic_threshold_low*100)};\n')
    outlines.append(f'  slew_lower_threshold_pct_rise : {str(target_lib.logic_threshold_low*100)};\n')
    outlines.append(f'  slew_upper_threshold_pct_fall : {str(target_lib.logic_threshold_high*100)};\n')
    outlines.append(f'  slew_upper_threshold_pct_rise : {str(target_lib.logic_threshold_high*100)};\n')
    ## operating conditions
    outlines.append(f'  operating_conditions ({target_lib.operating_conditions}) {{\n')
    outlines.append(f'    process : 1;\n')
    outlines.append(f'    temperature : {str(target_lib.temperature)};\n')
    outlines.append(f'    voltage : {str(target_lib.vdd.voltage)};\n')
    outlines.append(f'  }}\n')
    outlines.append(f'  default_operating_conditions : {target_lib.operating_conditions};\n')
    outlines.append(f'  lu_table_template (constraint_template) {{\n')
    outlines.append(f'    variable_1 : constrained_pin_transition;\n')
    outlines.append(f'    variable_2 : related_pin_transition;\n')
    outlines.append(f'    index_1 ("{", ".join([str(slope) for slope in target_cell.in_slopes])}");\n')
    outlines.append(f'    index_2 ("{", ".join([str(slope) for slope in target_cell.in_slopes])}");\n')
    outlines.append(f'  }}\n')
    outlines.append(f'  lu_table_template (delay_template) {{\n')
    outlines.append(f'    variable_1 : input_net_transition;\n')
    outlines.append(f'    variable_2 : total_output_net_capacitance;\n')
    outlines.append(f'    index_1 ("{", ".join([str(slope) for slope in target_cell.in_slopes])}");\n')
    outlines.append(f'    index_2 ("{", ".join([str(load) for load in target_cell.out_loads])}");\n')
    outlines.append(f'  }}\n')
    outlines.append(f'  lu_table_template (recovery_template) {{\n')
    outlines.append(f'    variable_1 : related_pin_transition;\n')
    outlines.append(f'    variable_2 : constrained_pin_transition;\n')
    outlines.append(f'    index_1 ("{", ".join([str(slope) for slope in target_cell.in_slopes])}");\n')
    outlines.append(f'    index_2 ("{", ".join([str(slope) for slope in target_cell.in_slopes])}");\n')
    outlines.append(f'  }}\n')
    outlines.append(f'  lu_table_template (removal_template) {{\n')
    outlines.append(f'    variable_1 : related_pin_transition;\n')
    outlines.append(f'    variable_2 : constrained_pin_transition;\n')
    outlines.append(f'    index_1 ("{", ".join([str(slope) for slope in target_cell.in_slopes])}");\n')
    outlines.append(f'    index_2 ("{", ".join([str(slope) for slope in target_cell.in_slopes])}");\n')
    outlines.append(f'  }}\n')
    outlines.append(f'  lu_table_template (mpw_constraint_template) {{\n')
    outlines.append(f'    variable_1 : constrained_pin_transition;\n')
    outlines.append(f'    index_1 ("{", ".join([str(slope) for slope in target_cell.in_slopes])}");\n')
    outlines.append(f'  }}\n')
    outlines.append(f'  power_lut_template (passive_power_template) {{\n')
    outlines.append(f'    variable_1 : input_transition_time;\n')
    outlines.append(f'    index_1 ("{", ".join([str(slope) for slope in target_cell.in_slopes])}");\n')
    outlines.append(f'  }}\n')
    outlines.append(f'  power_lut_template (power_template) {{\n')
    outlines.append(f'    variable_1 : input_transition_time;\n')
    outlines.append(f'    variable_2 : total_output_net_capacitance;\n')
    outlines.append(f'    index_1 ("{", ".join([str(slope) for slope in target_cell.in_slopes])}");\n')
    outlines.append(f'    index_2 ("{", ".join([str(load) for load in target_cell.out_loads])}");\n')
    outlines.append(f'  }}\n')
    outlines.append(f'  input_voltage (default_{target_lib.vdd.name}_{target_lib.vss.name}_input) {{\n')
    outlines.append(f'    vil : {str(target_lib.vss.voltage)};\n')
    outlines.append(f'    vih : {str(target_lib.vdd.voltage)};\n')
    outlines.append(f'    vimin : {str(target_lib.vss.voltage)};\n')
    outlines.append(f'    vimax : {str(target_lib.vdd.voltage)};\n')
    outlines.append(f'  }}\n')
    outlines.append(f'  output_voltage (default_{target_lib.vdd.name}_{target_lib.vss.name}_output) {{\n')
    outlines.append(f'    vol : {str(target_lib.vss.voltage)};\n')
    outlines.append(f'    voh : {str(target_lib.vdd.voltage)};\n')
    outlines.append(f'    vomin : {str(target_lib.vss.voltage)};\n')
    outlines.append(f'    vomax : {str(target_lib.vdd.voltage)};\n')
    outlines.append(f'  }}\n')
    
    with open(target_lib.dotlib_name, 'w') as f:
        f.writelines(outlines)
        f.close()
    target_lib.set_exported()

    ## for verilog file 
    outlines = []
    outlines.append(f'// Verilog model for {target_lib.lib_name};\n')
    # TODO: Implement this
    with open(target_lib.verilog_name, 'w') as f:
        f.writelines(outlines)
        f.close()

## export harness data to .lib
def exportCombinationalCell(targetLib: LibrarySettings, targetCell: LogicCell):
    outlines = []
    outlines.append(f'  cell ({targetCell.name}) {{\n') ## cell start
    outlines.append(f'    area : {str(targetCell.area)};\n')
    outlines.append(f'    cell_leakage_power : {targetCell.harnesses[0].get_leakage_power(targetLib.vdd.voltage, targetLib.units.power):f};\n') ## use leak of 1st harness
    outlines.append(f'    pg_pin ({targetLib.vdd.name}) {{\n')
    outlines.append(f'      pg_type : primary_power;\n')
    outlines.append(f'      voltage_name : "{targetLib.vdd.name}";\n')
    outlines.append(f'    }}\n')
    outlines.append(f'    pg_pin ({targetLib.vss.name}) {{\n')
    outlines.append(f'      pg_type : primary_ground;\n')
    outlines.append(f'      voltage_name : "{targetLib.vss.name}";\n')
    outlines.append(f'    }}\n')

    for out_port in targetCell.out_ports:
        out_port_index = targetCell.out_ports.index(out_port) 
        outlines.append(f'    pin ({out_port}) {{\n') ## out pin start
        outlines.append(f'      direction : output;\n')
        outlines.append(f'      related_power_pin : "{targetLib.vdd.name}";\n')
        outlines.append(f'      related_ground_pin : "{targetLib.vss.name}";\n')
        outlines.append(f'      max_capacitance : "{str(targetCell.out_loads[-1])}";\n') ## use max val. of load table
        outlines.append(f'      function : "{targetCell.functions[out_port_index]})"\n')
        outlines.append(f'      output_voltage : default_{targetLib.vdd.name}_{targetLib.vss.name}_output;\n')
        ## timing
        for in_port in targetCell.in_ports:
            outlines.append(f'      timing () {{\n')
            in_port_index = targetCell.in_ports.index(in_port)
            outlines.append(f'        related_pin : "{in_port}";\n')
            outlines.append(f'        timing_sense : "{targetCell.harnesses[in_port_index*2].timing_sense}";\n')
            outlines.append(f'        timing_type : "{targetCell.harnesses[in_port_index*2].timing_type}";\n')
            ## rise
            ## propagation delay
            outlines.append(f'        {targetCell.harnesses[in_port_index*2].direction_prop} (delay_template_{len(targetCell.in_slopes)}x{len(targetCell.out_loads)}) {{\n')
            for lut_line in targetCell.harnesses[in_port_index*2].get_propagation_delay_lut(targetCell.in_slopes, targetCell.out_loads, targetLib.units.time):
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            ## transition delay
            outlines.append(f'        {targetCell.harnesses[in_port_index*2].direction_tran} (delay_template_{len(targetCell.in_slopes)}x{len(targetCell.out_loads)}) {{\n')
            for lut_line in targetCell.harnesses[in_port_index*2].get_transport_delay_lut(targetCell.in_slopes, targetCell.out_loads, targetLib.units.time):
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            ## fall
            ## propagation delay
            outlines.append(f'        {targetCell.harnesses[in_port_index*2+1].direction_prop} (delay_template_{len(targetCell.in_slopes)}x{len(targetCell.out_loads)}) {{\n')
            for lut_line in targetCell.harnesses[in_port_index*2+1].get_propagation_delay_lut(targetCell.in_slopes, targetCell.out_loads, targetLib.units.time):
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            ## transition delay
            outlines.append(f'        {targetCell.harnesses[in_port_index*2+1].direction_tran} (delay_template_{len(targetCell.in_slopes)}x{len(targetCell.out_loads)}) {{\n')
            for lut_line in targetCell.harnesses[in_port_index*2+1].get_transport_delay_lut(targetCell.in_slopes, targetCell.out_loads, targetLib.units.time):
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            outlines.append(f'      }}\n') ## timing end 
        ## power
        for in_port in targetCell.in_ports:
            outlines.append(f'      internal_power () {{\n')
            in_port_index = targetCell.in_ports.index(in_port) 
            outlines.append(f'        related_pin : "{in_port}";\n')
            ## rise(fall)
            outlines.append(f'        {targetCell.harnesses[in_port_index*2].direction_power} (energy_template_{len(targetCell.in_slopes)}x{len(targetCell.out_loads)}) {{\n')
            for lut_line in targetCell.harnesses[in_port_index*2].get_internal_energy_lut(targetCell.in_slopes, targetCell.out_loads, targetLib.energy_meas_high_threshold_voltage(), targetLib.units.energy):
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            ## fall(rise)
            outlines.append(f'        {targetCell.harnesses[in_port_index*2+1].direction_power} (energy_template_{len(targetCell.in_slopes)}x{len(targetCell.out_loads)}) {{\n')
            for lut_line in targetCell.harnesses[in_port_index*2+1].get_internal_energy_lut(targetCell.in_slopes, targetCell.out_loads, targetLib.energy_meas_high_threshold_voltage(), targetLib.units.energy):
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            outlines.append(f'      }}\n') ## power end 
        outlines.append(f'    }}\n') ## out pin end

    ## select one input pin from pinlist(target_inports) 
    for in_port in targetCell.in_ports:
        out_port_index = targetCell.in_ports.index(in_port) 
        outlines.append(f'    pin ({in_port}){{\n') ## out pin start
        outlines.append(f'      direction : input; \n')
        outlines.append(f'      related_power_pin : {targetLib.vdd.name};\n')
        outlines.append(f'      related_ground_pin : {targetLib.vss.name};\n')
        outlines.append(f'      max_transition : {str(targetCell.in_slopes[-1])};\n')
        # TODO: outlines.append(f'      capacitance : "{str(targetCell.cins[out_port_index])}";\n')
        outlines.append(f'      input_voltage : default_{targetLib.vdd.name}_{targetLib.vss.name}_input;\n')
        outlines.append(f'    }}\n') ## in pin end

    outlines.append(f'  }}\n') ## cell end
    with open(targetLib.dotlib_name, 'a') as f:
        f.writelines(outlines)
        f.close()
    targetCell.set_exported()


## export harness data to .lib
def exportSequentialCell(targetLib: LibrarySettings, targetCell: SequentialCell):
    harnesses = targetCell.harnesses
    outlines = []
    outlines.append(f'  cell ({targetCell.name}) {{\n') #### cell start
    outlines.append(f'    area : {str(targetCell.area)};\n')
    # outlines.append("    cell_leakage_power : "+targetCell.leakage_power+";\n")
    outlines.append(f'    pg_pin ({targetLib.vdd.name}) {{\n')
    outlines.append(f'      pg_type : primary_power;\n')
    outlines.append(f'      voltage_name : "{targetLib.vdd.name}";\n')
    outlines.append(f'    }}\n')
    outlines.append(f'    pg_pin ({targetLib.vss.name}) {{\n')
    outlines.append(f'      pg_type : primary_ground;\n')
    outlines.append(f'      voltage_name : "{targetLib.vss.name}";\n')
    outlines.append(f'    }}\n')

    ## define flop
    outlines.append(f'    ff ({str(targetCell.flops[0])}, {str(targetCell.flops[1])}) {{\n')
    outlines.append(f'    clocked_on : "{targetCell.clock}";\n') 
    for target_inport in targetCell.in_ports:
        outlines.append(f'    next_state : "{target_inport}";\n') 
    if targetCell.reset is not None:
        outlines.append(f'    clear : "{targetCell.reset}";\n') 
    if targetCell.set is not None:
        outlines.append(f'    preset : "{targetCell.set}";\n') 
        if targetCell.reset is not None:
            ## value when set and reset both activate
            ## tool does not support this simulation, so hard coded to low
            outlines.append(f'    clear_preset_var1 : L ;\n') 
            outlines.append(f'    clear_preset_var2 : L ;\n') 
    outlines.append(f'    }}\n') 
    ##
    ## (1) clock
    ##
    if targetCell.clock is not None:
        # index1 = targetCell.clock.index(target_clock) 
        index1 = 0 
        target_inport = targetCell.clock
        outlines.append(f'    pin ({target_inport}) {{\n') ## clock pin start 
        outlines.append(f'      direction : input;\n')
        outlines.append(f'      related_power_pin : "{targetLib.vdd.name}";\n')
        outlines.append(f'      related_ground_pin : "{targetLib.vss.name}";\n')
        outlines.append(f'      max_transition : {str(targetCell.in_slopes[-1])};\n')
        outlines.append(f'      capacitance : "{str(targetCell.cclks[index1])}";\n')
        outlines.append(f'      input_voltage : default_{targetLib.vdd.name}_{targetLib.vss.name}_input;\n')
        outlines.append(f'      clock : true;\n') 
        # internal_power() {
        #     rise_power(passive_energy_template_7x1) {
        #     index_1 ("0.01669, 0.030212, 0.094214, 0.230514, 0.461228, 0.919101, 2.29957");
        #     values ("0.040923, 0.0374, 0.044187, 0.046943, 0.045139, 0.051569, 0.080466");
        #     }
        #     fall_power(passive_energy_template_7x1) {
        #     index_1 ("0.016236, 0.030811, 0.094437, 0.232485, 0.461801, 0.919137, 2.29958");
        #     values ("0.038868, 0.03793, 0.033501, 0.043008, 0.042432, 0.048973, 0.08357");
        #     }
        # }
        # min_pulse_width_high : 0.145244;
        # min_pulse_width_low : 0.226781;
        outlines.append(f'    }}\n') ## clock pin end



    ##
    ## (2) prop/tran/setup/hold for input pins
    ##
    for target_inport in targetCell.in_ports:
        for target_outport in targetCell.out_ports:
            ## select inport with setup/hold informatioin
            index2 = targetCell.in_ports.index(target_inport) 
            index1 = targetCell.out_ports.index(target_outport) 
            #print(harnessList2[index1][index2*2].timing_type_setup)
            if((harnesses[index1][index2*2].timing_type_setup == "setup_rising") or (harnesses[index1][index2*2].timing_type_setup == "setup_falling")):
                outlines.append(f'    pin ({target_inport}) {{\n') #### inport pin start 
                outlines.append(f'      direction : input;\n')
                outlines.append(f'      related_power_pin : "{targetLib.vdd.name}";\n')
                outlines.append(f'      related_ground_pin : "{targetLib.vss.name}";\n')
                outlines.append(f'      max_transition : {str(targetCell.in_slopes[-1])};\n')
                outlines.append(f'      capacitance : "{str(targetCell.cins[index1])}";\n')
                outlines.append(f'      input_voltage : default_{targetLib.vdd.name}_{targetLib.vss.name}_input;\n')
                ## (2-1) setup
                outlines.append(f'      timing () {{\n')
                outlines.append(f'        related_pin : "{targetCell.clock}";\n')
                outlines.append(f'        timing_type : "{harnesses[index1][index2*2].timing_type_setup}";\n')
                ## setup rise
                outlines.append(f'        {harnesses[index1][index2*2].timing_sense_setup} (constraint_template) {{\n')
                for lut_line in harnesses[index1][index2*2].lut_setup:
                    outlines.append(f'          {lut_line}\n')
                outlines.append(f'        }}\n') 
                ## setup fall
                outlines.append(f'        {harnesses[index1][index2*2+1].timing_sense_setup} (constraint_template) {{\n')
                for lut_line in harnesses[index1][index2*2+1].lut_setup:
                    outlines.append(f'          {lut_line}\n')
                outlines.append(f'        }}\n') 
                outlines.append(f'      }}\n') 
                ## (2-2) hold
                outlines.append(f'      timing () {{\n')
                index1 = targetCell.out_ports.index(target_outport) 
                outlines.append(f'        related_pin : "{targetCell.clock}";\n')
                outlines.append(f'        timing_type : "{harnesses[index1][index2*2].timing_type_hold}";\n')
                ## hold rise
                outlines.append(f'        {harnesses[index1][index2*2].timing_sense_hold} (constraint_template) {{\n')
                for lut_line in harnesses[index1][index2*2].lut_hold:
                    outlines.append(f'          {lut_line}\n')
                outlines.append(f'        }}\n') 
                ## hold fall
                outlines.append(f'        {harnesses[index1][index2*2+1].timing_sense_hold} (constraint_template) {{\n')
                for lut_line in harnesses[index1][index2*2+1].lut_hold:
                    outlines.append(f'          {lut_line}\n')
                outlines.append(f'        }}\n') 
                outlines.append(f'      }}\n') 
    outlines.append(f'    }}\n') ## inport pin end

    ##
    ## (3) outport 
    ##
    for target_outport in targetCell.out_ports:
        index1 = targetCell.out_ports.index(target_outport) 
        outlines.append(f'    pin ({target_outport}) {{\n') #### out pin start
        outlines.append(f'      direction : output;\n')
        outlines.append(f'      function : "({targetCell.functions[index1]})"\n')
        outlines.append(f'      related_power_pin : "{targetLib.vdd.name}";\n')
        outlines.append(f'      related_ground_pin : "{targetLib.vss.name}";\n')
        outlines.append(f'      max_capacitance : "{str(targetCell.out_loads[-1])}";\n') ## use max val. of load table
        outlines.append(f'      output_voltage : default_{targetLib.vdd.name}_{targetLib.vss.name}_output;\n')
        ## (3-1) clock
        if targetCell.clock is not None:
            ## index2 is a base pointer for harness search
            ## index2_offset and index2_offset_max are used to 
            ## search harness from harnessList2 which contain "timing_type_set"
            index2 = targetCell.out_ports.index(target_outport) 
            index2_offset = 0
            index2_offset_max = 10
            while(index2_offset < index2_offset_max):
                if hasattr(harnesses[index1][index2*2+index2_offset], "timing_type_setup"):
                    break
                index2_offset += 1
            if(index2_offset == 10):
                print("Error: index2_offset exceed max. search number\n")
                exit()

            ##target_inport = targetCell.clock
            outlines.append(f'      timing () {{\n')
            outlines.append(f'        related_pin : "{targetCell.clock}";\n')
            outlines.append(f'        timing_type : "{harnesses[index1][index2*2+index2_offset].timing_type_clock}";\n')
            outlines.append(f'        timing_sense : "{harnesses[index1][index2*2+index2_offset].timing_sense_clock}";\n')
            #### (3-1-1) rise
            ## propagation delay
            outlines.append(f'        {harnesses[index1][index2*2+index2_offset].direction_prop} (delay_template) {{\n')
            for lut_line in harnesses[index1][index2*2+index2_offset].lut_prop:
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            ## transition delay
            outlines.append(f'        {harnesses[index1][index2*2+index2_offset].direction_tran} (delay_template) {{\n')
            for lut_line in harnesses[index1][index2*2+index2_offset].lut_tran:
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            #### (3-1-2) fall
            ## propagation delay
            outlines.append(f'        {harnesses[index1][index2*2+index2_offset+1].direction_prop} (delay_template) {{\n')
            for lut_line in harnesses[index1][index2*2+index2_offset+1].lut_prop:
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            ## transition delay
            outlines.append(f'        {harnesses[index1][index2*2+index2_offset+1].direction_tran} (delay_template) {{\n')
            for lut_line in harnesses[index1][index2*2+index2_offset+1].lut_tran:
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            outlines.append(f'      }}\n') ## timing end 

        ## (3-2) reset (one directrion)
        if targetCell.reset is not None:
            ##target_inport = targetCell.reset
            outlines.append(f'      timing () {{\n')

            ## Harness search for reset
            ## index2 is an base pointer for harness search
            ## index2_offset and index2_offset_max are used to 
            ## search harness from harnessList2 which contain "timing_type_set"
            index2 = targetCell.out_ports.index(target_outport) 
            index2_offset = 0
            index2_offset_max = 10
            while index2_offset < index2_offset_max:
                #print(harnessList2[index1][index2*2+index2_offset])
                if hasattr(harnesses[index1][index2*2+index2_offset], "timing_type_reset"):
                    break
                index2_offset += 1
            if index2_offset == 10:
                print("Error: index2_offset exceed max. search number\n") #TODO: Error properly here
                exit()

            outlines.append(f'        related_pin : "{targetCell.reset}";\n')
            outlines.append(f'        timing_sense : "{harnesses[index1][index2*2+index2_offset].timing_sense_reset}";\n')
            outlines.append(f'        timing_type : "{harnesses[index1][index2*2+index2_offset].timing_type_reset}";\n')
            ## (3-2-1) propagation delay
            outlines.append(f'        {harnesses[index1][index2*2+index2_offset].direction_reset_prop} (delay_template) {{\n')
            for lut_line in harnesses[index1][index2*2+index2_offset].lut_prop:
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            ## (3-2-2) transition delay
            outlines.append(f'        {harnesses[index1][index2*2+index2_offset].direction_reset_tran} (delay_template) {{\n')
            for lut_line in harnesses[index1][index2*2+index2_offset].lut_tran:
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            outlines.append(f'      }}\n') 

        ## (3-3) set (one directrion)
        if targetCell.set is not None:
            ##target_inport = targetCell.set
            outlines.append(f'      timing () {{\n')
            ## Harness search for set
            ## index2 is an base pointer for harness search
            ## index2_offset and index2_offset_max are used to 
            ## search harness from harnessList2 which contain "timing_type_set"
            index2 = targetCell.out_ports.index(target_outport) 
            index2_offset = 0
            index2_offset_max = 10
            while(index2_offset < index2_offset_max):
                if hasattr(harnesses[index1][index2*2+index2_offset], "timing_type_set"):
                    break
                index2_offset += 1
            if(index2_offset == 10):
                print("Error: index2_offset exceed max. search number\n") # TODO: Error properly
                exit()

            outlines.append(f'        related_pin : "{targetCell.set}";\n')
            outlines.append(f'        timing_sense : "{harnesses[index1][index2*2+index2_offset].timing_sense_set}";\n')
            outlines.append(f'        timing_type : "{harnesses[index1][index2*2+index2_offset].timing_type_set}";\n')
            ## (3-3-1) propagation delay
            outlines.append(f'        {harnesses[index1][index2*2+index2_offset].direction_set_prop} (delay_template) {{\n')
            for lut_line in harnesses[index1][index2*2+index2_offset].lut_prop:
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            ## (3-3-2) transition delay
            outlines.append(f'        {harnesses[index1][index2*2+index2_offset].direction_set_tran} (delay_template) {{\n')
            for lut_line in harnesses[index1][index2*2+index2_offset].lut_tran:
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            outlines.append(f'      }}\n') 
        
        ## (3-4) clock power
        if targetCell.clock is not None:
            ## index2 is a base pointer for harness search
            ## index2_offset and index2_offset_max are used to 
            ## search harness from harnessList2 which contain "timing_type_set"
            index2 = targetCell.out_ports.index(target_outport) 
            index2_offset = 0
            index2_offset_max = 10
            while index2_offset < index2_offset_max:
                if hasattr(harnesses[index1][index2*2+index2_offset], "timing_type_setup"):
                    break
                index2_offset += 1
            if index2_offset == 10:
                print("Error: index2_offset exceed max. search number\n") # TODO: Error properly
                exit()

            outlines.append(f'      internal_power () {{\n')
            index2 = targetCell.in_ports.index(target_inport) 
            outlines.append(f'        related_pin : "{targetCell.clock}";\n')
            ## rise(fall)
            outlines.append(f'        {harnesses[index1][index2*2].direction_power} (power_template) {{\n')
            for lut_line in harnesses[index1][index2*2].get_internal_energy_lut(targetCell.in_slopes, targetCell.out_loads, targetLib.energy_meas_high_threshold_voltage(), targetLib.units.energy):
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            ## fall(rise)
            outlines.append(f'        {harnesses[index1][index2*2+1].direction_power} (power_template) {{\n')
            for lut_line in harnesses[index1][index2*2+1].get_internal_energy_lut(targetCell.in_slopes, targetCell.out_loads, targetLib.energy_meas_high_threshold_voltage(), targetLib.units.energy):
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            outlines.append(f'      }}\n') ## power end 

        ## (3-5) reset power 
        if targetCell.reset is not None:

            ## Harness search for reset
            ## index2 is an base pointer for harness search
            ## index2_offset and index2_offset_max are used to 
            ## search harness from harnessList2 which contain "timing_type_set"
            index2 = targetCell.out_ports.index(target_outport) 
            index2_offset = 0
            index2_offset_max = 10
            while(index2_offset < index2_offset_max):
                #print(harnessList2[index1][index2*2+index2_offset])
                if hasattr(harnesses[index1][index2*2+index2_offset], "timing_type_reset"):
                    break
                index2_offset += 1
            if(index2_offset == 10):
                print("Error: index2_offset exceed max. search number\n")
                exit()

            outlines.append(f'      internal_power () {{\n')
            index2 = targetCell.in_ports.index(target_inport) 
            outlines.append(f'        related_pin : "{targetCell.reset}";\n')
            ## rise(fall)
            outlines.append(f'        {harnesses[index1][index2*2].direction_power} (power_template) {{\n')
            for lut_line in harnesses[index1][index2*2].get_internal_energy_lut(targetCell.in_slopes, targetCell.out_loads, targetLib.energy_meas_high_threshold_voltage(), targetLib.units.energy):
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            ## fall(rise)
            outlines.append(f'        {harnesses[index1][index2*2+1].direction_power} (power_template) {{\n')
            for lut_line in harnesses[index1][index2*2+1].get_internal_energy_lut(targetCell.in_slopes, targetCell.out_loads, targetLib.energy_meas_high_threshold_voltage(), targetLib.units.energy):
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            outlines.append(f'      }}\n') ## power end 

        ## (3-6) set power 
        if targetCell.set is not None:

            ## Harness search for set
            ## index2 is an base pointer for harness search
            ## index2_offset and index2_offset_max are used to 
            ## search harness from harnessList2 which contain "timing_type_set"
            index2 = targetCell.out_ports.index(target_outport) 
            index2_offset = 0
            index2_offset_max = 10
            while index2_offset < index2_offset_max:
                #print(harnessList2[index1][index2*2+index2_offset])
                if hasattr(harnesses[index1][index2*2+index2_offset], "timing_type_set"):
                    break
                index2_offset += 1
            if index2_offset == 10:
                print("Error: index2_offset exceed max. search number\n") # TODO: Error properly
                exit()

            outlines.append(f'      internal_power () {{\n')
            index2 = targetCell.in_ports.index(target_inport) 
            outlines.append(f'        related_pin : "{targetCell.set}";\n')
            ## rise(fall)
            outlines.append(f'        {harnesses[index1][index2*2].direction_power} (power_template) {{\n')
            for lut_line in harnesses[index1][index2*2].get_internal_energy_lut(targetCell.in_slopes, targetCell.out_loads, targetLib.energy_meas_high_threshold_voltage(), targetLib.units.energy):
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            ## fall(rise)
            outlines.append(f'        {harnesses[index1][index2*2+1].direction_power} (power_template) {{\n')
            for lut_line in harnesses[index1][index2*2+1].get_internal_energy_lut(targetCell.in_slopes, targetCell.out_loads, targetLib.energy_meas_high_threshold_voltage(), targetLib.units.energy):
                outlines.append(f'          {lut_line}\n')
            outlines.append(f'        }}\n') 
            outlines.append(f'      }}\n') ## power end 
        ##outlines.append("    }\n") #### out pin end
    outlines.append(f'    }}\n') ## out pin end

    ## (4) Reset
    if targetCell.reset is not None:
        # for target_reset in targetCell.reset:
        target_reset = targetCell.reset
        index1 = targetCell.reset.index(target_reset) 
        outlines.append(f'    pin ({target_reset}) {{\n') #### out pin start
        outlines.append(f'      direction : input;\n')
        #outlines.append(f'      function : "({targetCell.functions[index1]})"\n')
        outlines.append(f'      related_power_pin : "{targetLib.vdd.name}";\n')
        outlines.append(f'      related_ground_pin : "{targetLib.vss.name}";\n')
        outlines.append(f'      max_transition : {str(targetCell.in_slopes[-1])};\n')
        ##outlines.append(f'      capacitance : "{str(targetCell.crsts[index1])}";\n')
        outlines.append(f'      capacitance : "{str(targetCell.crsts[0])}";\n') # use 0 as representative
        outlines.append(f'      input_voltage : default_{targetLib.vdd.name}_{targetLib.vss.name}_input;\n')
        ##target_inport = targetCell.reset

        ## Harness search for reset
        ## index2 is an base pointer for harness search
        ## index2_offset and index2_offset_max are used to 
        ## search harness from harnessList2 which contain "timing_type_set"
        index2 = targetCell.out_ports.index(target_outport) 
        index2_offset = 0
        index2_offset_max = 10
        while index2_offset < index2_offset_max:
            #print(harnessList2[index1][index2*2+index2_offset])
            if hasattr(harnesses[index1][index2*2+index2_offset], "timing_type_reset"):
                break
            index2_offset += 1
        if index2_offset == 10:
            print("Error: index2_offset exceed max. search number\n") # TODO: Error properly
            exit()
        #for a in inspect.getmembers(harnessList2[index1][index2*2+index2_offset]):
        #	print (a) 
        ## (4-1) recovery
        outlines.append(f'      timing () {{\n')
        outlines.append(f'        related_pin : "{targetCell.clock}";\n')
        outlines.append(f'        timing_type : "{harnesses[index1][index2*2+index2_offset].timing_type_reset_recov}";\n')
        if (1 != len(targetCell.in_ports)):
            print (f'Error: number of targetCell.in_ports is {str(len(targetCell.in_ports))}, not one!') # TODO: Error properly
            exit()
        #for target_inport in targetCell.in_ports: ## only one target_inport should be available
        #	outlines.append("        when : \""+harnessList2[index1][index2*2+index2_offset].timing_type_reset+"\";\n")
        outlines.append(f'        {harnesses[index1][index2*2+index2_offset].timing_sense_reset_recov} (recovery_template) {{\n')
        for lut_line in harnesses[index1][index2*2+index2_offset].lut_setup:
            outlines.append(f'          {lut_line}\n')
        outlines.append(f'        }}\n') 
        outlines.append(f'      }}\n') 
        ## (4-2)removal 
        outlines.append(f'      timing () {{\n')
        outlines.append(f'        related_pin : "{targetCell.clock}";\n')
        outlines.append(f'        timing_type : "{harnesses[index1][index2*2+index2_offset].timing_type_reset_remov}";\n')
        if (1 != len(targetCell.in_ports)):
            print (f'Error: number of targetCell.in_ports is {str(len(targetCell.in_ports))}, not one!') # TODO: Error properly
            exit()
        #for target_inport in targetCell.in_ports: ## only one target_inport should be available
        #	outlines.append("        when : \""+harnessList2[index1][index2*2+index2_offset].timing_type_reset+"\";\n")
        outlines.append(f'        {harnesses[index1][index2*2+index2_offset].timing_sense_reset_remov} (removal_template) {{\n')
        for lut_line in harnesses[index1][index2*2+index2_offset].lut_hold:
            outlines.append(f'          {lut_line}\n')
        outlines.append(f'        }}\n') 
        outlines.append(f'      }}\n') 
    outlines.append(f'    }}\n') #### out pin end -> continue for set

    ## (5) set
    if targetCell.set is not None:
        #for target_set in targetCell.set:
        target_set = targetCell.set
        index1 = targetCell.set.index(target_set) 
        outlines.append(f'    pin ({target_set}) {{\n') #### out pin start
        outlines.append(f'      direction : input;\n')
        #outlines.append(f'      function : "({targetCell.functions[index1]})"\n')
        outlines.append(f'      related_power_pin : "{targetLib.vdd.name}";\n')
        outlines.append(f'      related_ground_pin : "{targetLib.vss.name}";\n')
        outlines.append(f'      max_transition : {str(targetCell.in_slopes[-1])};\n')
        #outlines.append(f'      capacitance : "{str(targetCell.csets[index1])}";\n')
        outlines.append(f'      capacitance : "{str(targetCell.csets[0])}";\n') # use 0 as representative val
        outlines.append(f'      input_voltage : default_{targetLib.vdd.name}_{targetLib.vss.name}_input;\n')
        ##target_inport = targetCell.set

        ## Harness search for set
        ## index2 is an base pointer for harness search
        ## index2_offset and index2_offset_max are used to 
        ## search harness from harnessList2 which contain "timing_type_set"
        index2 = targetCell.out_ports.index(target_outport) 
        index2_offset = 0
        index2_offset_max = 10
        while index2_offset < index2_offset_max:
            #print(harnessList2[index1][index2*2+index2_offset])
            if hasattr(harnesses[index1][index2*2+index2_offset], "timing_type_set"):
                break
            index2_offset += 1
        if index2_offset == 10:
            print("Error: index2_offset exceed max. search number\n") # TODO: Error properly
            exit()

        ## (5-1) recovery
        outlines.append(f'      timing () {{\n')
        outlines.append(f'        related_pin : "{targetCell.clock}";\n')
        outlines.append(f'        timing_type : "{harnesses[index1][index2*2+index2_offset].timing_type_set_recov}";\n')
        if (1 != len(targetCell.in_ports)):
            print (f'Error: number of targetCell.in_ports is {str(len(targetCell.in_ports))}, not one!') # TODO: Error properly
            exit()
        #for target_inport in targetCell.in_ports: ## only one target_inport should be available
        #	outlines.append("        when : \""+harnessList2[index1][index2*2+index2_offset].timing_type_set+"\";\n")
        outlines.append(f'        {harnesses[index1][index2*2+index2_offset].timing_sense_set_recov} (recovery_template) {{\n')
        for lut_line in harnesses[index1][index2*2+index2_offset].lut_setup:
            outlines.append(f'          {lut_line}\n')
        outlines.append(f'        }}\n')
        outlines.append(f'      }}\n')

        ## (5-2)removal 
        outlines.append(f'      timing () {{\n')
        outlines.append(f'        related_pin : "{targetCell.clock}";\n')
        outlines.append(f'        timing_type : "{harnesses[index1][index2*2+index2_offset].timing_type_set_remov}";\n')
        if (1 != len(targetCell.in_ports)):
            print (f'Error: number of targetCell.in_ports is {str(len(targetCell.in_ports))}, not one!') # TODO: Error properly
            exit()
        #for target_inport in targetCell.in_ports: ## only one target_inport should be available
        #	outlines.append("        when : \""+harnessList2[index1][index2*2+index2_offset].timing_type_set+"\";\n")
        outlines.append(f'        {harnesses[index1][index2*2+index2_offset].timing_sense_set_remov} (removal_template) {{\n')
        for lut_line in harnesses[index1][index2*2+index2_offset].lut_hold:
            outlines.append(f'          {lut_line}\n')
        outlines.append(f'        }}\n')
        outlines.append(f'      }}\n')
    outlines.append(f'    }}\n') #### out pin end -> continue for set

    outlines.append(f'  }}\n') #### cell end
    with open(targetLib.dotlib_name, 'a') as f:
        f.writelines(outlines)
        f.close()
    targetCell.set_exported()


## export library definition to .lib
def exportVerilog(targetLib, targetCell):
    outlines = []

    ## list ports in one line 
    portlist = "("
    numport = 0
    for target_outport in targetCell.out_ports:
        if numport != 0:
            portlist += ", "
        portlist += target_outport
        numport += 1
    for target_inport in targetCell.in_ports:
        portlist += "," + target_inport
        numport += 1
    portlist += ");"

    outlines.append(f'module {targetCell.name + portlist}\n')

    ## input/output statement
    for target_outport in targetCell.out_ports:
        outlines.append(f'output {target_outport};\n')
    for target_inport in targetCell.in_ports:
        outlines.append(f'input {target_inport};\n')

    ## branch for sequential cell
    if targetCell.logic == "DFFARAS":
        print ("This cell "+targetCell.logic+" is not supported for verilog out\n") # TODO: Error properly
        exit()

    ## branch for combinational cell
    else:
    ## assign statement
        for target_outport in targetCell.out_ports:
            port_index = targetCell.out_ports.index(target_outport) 
            outlines.append(f'assign {target_outport} = {targetCell.functions[port_index]};\n')

    outlines.append("endmodule\n\n")
    
    with open(targetLib.verilog_name, 'a') as f:
        f.writelines(outlines)
        f.close()


## export library definition to .lib
def exportVerilogFlop(targetLib, targetCell):

    outlines = []

    ## list ports in one line 
    portlist = "("
    numport = 0
    for target_outport in targetCell.out_ports:
        if numport != 0:
            portlist += ", "
        portlist += target_outport
        numport += 1
    for target_inport in targetCell.in_ports:
        portlist += "," + target_inport
        numport += 1
    if targetCell.clock is not None:
        portlist += "," + targetCell.clock
        numport += 1
    if targetCell.reset is not None:
        portlist += "," + targetCell.reset
        numport += 1
    if targetCell.set is not None:
        portlist += "," + targetCell.set
        numport += 1
    portlist += ");"

    outlines.append(f'module {targetCell.name + portlist}\n')

    ## input/output statement
    for target_outport in targetCell.out_ports:
        outlines.append(f'output {target_outport};\n')
    for target_inport in targetCell.in_ports:
        outlines.append(f'input {target_inport};\n')
    if targetCell.clock is not None:
        outlines.append(f'input {targetCell.clock};\n')
    if targetCell.reset is not None:
        outlines.append(f'input {targetCell.reset};\n')
    if targetCell.set is not None:
        outlines.append(f'input {targetCell.set};\n')

    ## assign statement
    for target_outport in targetCell.out_ports:
        for target_inport in targetCell.in_ports:
            line = 'always @('
            resetlines = []
            setlines = []
            #print(str(targetCell.logic))
            ## clock
            if 'PC' in targetCell.logic:    ## posedge clock
                line += "posedge " + targetCell.clock
            elif 'NC' in targetCell.logic:  ## negedge clock
                line += "negedge " + targetCell.clock
            else:
                print("Error! failed to generate DFF verilog!") # TODO: Error properly
                exit()

            ## reset (option)
            if targetCell.reset is not None:    ## reset
                if 'PR' in targetCell.reset:    ## posedge async. reset
                    line += " or posedge " + targetCell.reset
                    resetlines.append(f'if ({targetCell.reset}) \n')
                    resetlines.append(f'  {target_outport}<=0;\n')
                    resetlines.append(f'else begin\n')
                elif 'NR' in targetCell.reset:  ## negedge async. reset
                    line += " or negedge " + targetCell.reset
                    resetlines.append(f'if (!{targetCell.reset}) \n')
                    resetlines.append(f'  {target_outport}<=0;\n')
                    resetlines.append(f'else begin\n')
            ## set (option)
            if targetCell.set is not None: ## reset
                if 'PS' in targetCell.set:  ## posedge async. set
                    line += " or posedge " + targetCell.set
                    setlines.append(f'if ({targetCell.set}) begin\n')
                    setlines.append(f'  {target_outport}<=1;\n')
                    setlines.append(f'end\n')
                    setlines.append(f'else begin\n')
                elif 'NS' in targetCell.set:    ## negedge async. set
                    line += " or negedge " + targetCell.set
                    setlines.append(f'if (!{targetCell.set}) begin\n')
                    setlines.append(f'  {target_outport}<=1;\n')
                    setlines.append(f'end\n')
                    setlines.append(f'else begin\n')
            line += ") begin\n"
            outlines.append(line)
            if targetCell.set is not None:
                outlines.append(setlines[0])
                outlines.append(setlines[1])
                outlines.append(setlines[2])
            if targetCell.reset is not None:
                outlines.append(resetlines[0])
                outlines.append(resetlines[1])
                outlines.append(resetlines[2])
            outlines.append(target_outport+'<='+target_inport)
            outlines.append('\nend\n')
            outlines.append('end\n')
        ## for target_inport
    ## for target_outport
    outlines.append("endmodule\n\n")

    with open(targetLib.verilog_name, 'a') as f:
        f.writelines(outlines)
        f.close()


## export harness data to .lib
def exitFiles(targetLib, num_gen_file):
    if targetLib.is_exported:
        outlines = []
        outlines.append("}\n")
        with open(targetLib.dotlib_name, 'a') as f:
            f.writelines(outlines)
            f.close()
        print("\n-- .lib file exported")
    else:
        print("\n-- Nothing to export")
    print("-- "+str(num_gen_file)+" cells generated\n")
