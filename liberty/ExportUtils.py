
import re, sys

from liberty.LibrarySettings import LibrarySettings
from liberty.LogicCell import LogicCell, CombinationalCell, SequentialCell
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
    outlines = [
        f'library ({target_lib.lib_name}) {{',
        f'',
        f'  delay_model : "{target_lib.delay_model}";'
        f'  in_place_swap_mode : match_footprint;',
        f'',
        f'  /* unit attributes */',
        f'  time_unit : "1{target_lib.units.time.prefixed_unit.str_spice()}";',
        f'  voltage_unit : "1{target_lib.units.voltage.prefixed_unit.str_spice()}";',
        f'  current_unit : "1{target_lib.units.current.prefixed_unit.str_spice()}";',
        f'  pulling_resistance_unit : "1{target_lib.units.resistance.prefixed_unit.str_spice()}";',
        f'  leakage_power_unit : "1{target_lib.units.power.prefixed_unit.str_spice()}";',
        f'  capacitive_load_unit (1,{target_lib.units.capacitance.prefixed_unit.str_spice()});',
        f'',
        f'  slew_upper_threshold_pct_rise : {str(target_lib.logic_threshold_high*100)};',
        f'  slew_lower_threshold_pct_rise : {str(target_lib.logic_threshold_low*100)};',
        f'  slew_upper_threshold_pct_fall : {str(target_lib.logic_threshold_high*100)};',
        f'  slew_lower_threshold_pct_fall : {str(target_lib.logic_threshold_low*100)};',
        f'  input_threshold_pct_rise : {str(target_lib.logic_low_to_high_threshold*100)};',
        f'  input_threshold_pct_fall : {str(target_lib.logic_high_to_low_threshold*100)};',
        f'  output_threshold_pct_rise : {str(target_lib.logic_low_to_high_threshold*100)};',
        f'  output_threshold_pct_fall : {str(target_lib.logic_high_to_low_threshold*100)};',
        f'  nom_process : 1;',
        f'  nom_voltage : {str(target_lib.vdd.voltage)};',
        f'  nom_temperature : {str(target_lib.temperature)};',
        f'  operating_conditions ({target_lib.operating_conditions}) {{',
        f'    process : 1;',
        f'    voltage : {str(target_lib.vdd.voltage)};',
        f'    temperature : {str(target_lib.temperature)};',
        f'  }}',
        f'  default_operating_conditions : {target_lib.operating_conditions};',
        f'',
        f'  lu_table_template (constraint_template) {{',
        f'    variable_1 : constrained_pin_transition;',
        f'    variable_2 : related_pin_transition;',
        f'    index_1 ("{", ".join([str(slope) for slope in target_cell.in_slews])}");',
        f'    index_2 ("{", ".join([str(slope) for slope in target_cell.in_slews])}");',
        f'  }}',
        f'  lu_table_template (delay_template_{len(target_cell.in_slews)}x{len(target_cell.out_loads)}) {{',
        f'    variable_1 : input_net_transition;',
        f'    variable_2 : total_output_net_capacitance;',
        f'    index_1 ("{", ".join([str(slope) for slope in target_cell.in_slews])}");',
        f'    index_2 ("{", ".join([str(load) for load in target_cell.out_loads])}");',
        f'  }}',
        f'  lu_table_template (recovery_template) {{',
        f'    variable_1 : related_pin_transition;',
        f'    variable_2 : constrained_pin_transition;',
        f'    index_1 ("{", ".join([str(slope) for slope in target_cell.in_slews])}");',
        f'    index_2 ("{", ".join([str(slope) for slope in target_cell.in_slews])}");',
        f'  }}',
        f'  lu_table_template (removal_template) {{',
        f'    variable_1 : related_pin_transition;',
        f'    variable_2 : constrained_pin_transition;',
        f'    index_1 ("{", ".join([str(slope) for slope in target_cell.in_slews])}");',
        f'    index_2 ("{", ".join([str(slope) for slope in target_cell.in_slews])}");',
        f'  }}',
        f'  lu_table_template (mpw_constraint_template) {{',
        f'    variable_1 : constrained_pin_transition;',
        f'    index_1 ("{", ".join([str(slope) for slope in target_cell.in_slews])}");',
        f'  }}',
        f'  power_lut_template (passive_energy_template) {{',
        f'    variable_1 : input_transition_time;',
        f'    index_1 ("{", ".join([str(slope) for slope in target_cell.in_slews])}");',
        f'  }}',
        f'  power_lut_template (energy_template_{len(target_cell.in_slews)}x{len(target_cell.out_loads)}) {{',
        f'    variable_1 : input_transition_time;',
        f'    variable_2 : total_output_net_capacitance;',
        f'    index_1 ("{", ".join([str(slope) for slope in target_cell.in_slews])}");',
        f'    index_2 ("{", ".join([str(load) for load in target_cell.out_loads])}");',
        f'  }}\n\n',
    ]
    
    with open(target_lib.dotlib_name, 'w') as f:
        f.writelines('\n'.join(outlines))
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
def exportCombinationalCell(target_lib: LibrarySettings, target_cell: CombinationalCell):
    outlines = []
    for line in target_cell.export(target_lib).split('\n'):
        outlines.append(f'  {line}\n')

    with open(target_lib.dotlib_name, 'a') as f:
        f.writelines(outlines)
        f.close()
    target_cell.set_exported()


## export harness data to .lib
def exportSequentialCell(targetLib: LibrarySettings, targetCell: SequentialCell):
    outlines = []
    for line in targetCell.export(targetLib).split('\n'):
        outlines.append(f'  {line}\n')

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
            ## clock
            # TODO: replace
            # if 'PC' in targetCell.logic:    ## posedge clock
            #     line += "posedge " + targetCell.clock
            # elif 'NC' in targetCell.logic:  ## negedge clock
            #     line += "negedge " + targetCell.clock
            # else:
            #     print("Error! failed to generate DFF verilog!") # TODO: Error properly
            #     exit()

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
