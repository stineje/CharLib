#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, os, shutil

from characterizer.LibrarySettings import LibrarySettings
from characterizer.LogicCell import LogicCell
from characterizer.myFunc import my_exit
from characterizer.ExportUtils import exportFiles, exitFiles
from characterizer.char_comb import runCombIn1Out1, runCombIn2Out1, runCombIn3Out1, runCombIn4Out1,  runSpiceCombDelay, genFileLogic_trial1
from characterizer.char_seq import runFlop, runSpiceFlopDelay, genFileFlop_trial1


# Globals
targetLib = LibrarySettings()
targetCell = None
num_gen_file = 0

def main():
    """Reads in command line arguments, then enters the requested execution mode.

    Batch mode (-b arg) executes a batch of commands from the specified cmd file.
    Library mode (-l arg) parses in a user-provided library from the specified directory
    and	characterizes it automatically. If a mode is not specified, we enter shell mode 
    to read in commands one at a time."""
    
    # Read in arguments
    parser = argparse.ArgumentParser(
            prog='CharLib',
            description='Characterize combinational and sequential standard cells')
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('-b','--batch', type=str,
            help='Execute specified batch .cmd file')
    mode_group.add_argument('-l', '--library', type=str,
            help='Read in a library of standard cells from the specified directory, and automatically characterize')
    args = parser.parse_args()

    # Dispatch based on operating mode
    print(args)
    if args.batch is not None:
        execute_batch(args.batch)
    elif args.library is not None:
        execute_lib(args.batch)
    else:
        execute_shell()

    my_exit()

def execute_batch(batchfile):
    """Read in a batch of commands from batchfile and execute."""

    print("Executing batch file " + batchfile)

    # file open
    with open(batchfile, 'r') as f:
        lines = f.readlines()
        f.close()
    
    for line in lines:
        line = line.strip('\n')
        num_gen_file = execute_command(line)

def execute_lib(library_dir):
    """Parse a library of standard files, generate a cmd file, and characterize"""

    # TODO
    print("Searching for standard cells in " + str(library_dir))

def execute_shell():
    """Enter CharLib shell"""

    print("Entering CharLib shell. Type 'exit' or ^C to quit")
    
    exit_flag = False
    try:
        while not exit_flag:
            command = input("CharLib > ")
            try:
                execute_command(command)
            except ValueError:
                print("Invalid command.")
            if command == "exit":
                exit_flag = True
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Exiting...")

def execute_command(command: str):
    (cmd, *args) = command.split()
    
    ##-- set function : common settings--#
    if cmd == 'set_lib_name':
        targetLib.lib_name = args[0]
    elif cmd == 'set_dotlib_name':
        targetLib.dotlib_name = args[0]
    elif cmd == 'set_verilog_name':
        targetLib.verilog_name = args[0]
    elif cmd == 'set_cell_name_suffix':
        targetLib.cell_name_suffix = args[0]
    elif cmd == 'set_cell_name_prefix':
        targetLib.cell_name_prefix = args[0]
    elif cmd == 'set_voltage_unit':
        targetLib.units.voltage = args[0]
    elif cmd == 'set_capacitance_unit':
        targetLib.units.capacitance = args[0]
    elif cmd == 'set_resistance_unit':
        targetLib.units.resistance = args[0]
    elif cmd == 'set_time_unit':
        targetLib.units.capacitance = args[0]
    elif cmd == 'set_current_unit':
        targetLib.units.current = args[0]
    elif cmd == 'set_leakage_power_unit':
        targetLib.units.leakage_power = args[0]
    elif cmd == 'set_energy_unit':
        targetLib.units.energy = args[0]
    elif cmd == 'set_vdd_name':
        targetLib.vdd.name = args[0]
    elif cmd == 'set_vss_name':
        targetLib.vss.name = args[0]
    elif cmd == 'set_pwell_name':
        targetLib.pwell.name = args[0]
    elif cmd == 'set_nwell_name':
        targetLib.nwell.name = args[0]

    ##-- set function : characterization settings--#
    elif cmd == 'set_process':
        targetLib.process = args[0]
    elif cmd == 'set_temperature':
        targetLib.temperature = args[0]
    elif cmd == 'set_vdd_voltage':
        targetLib.vdd.voltage = args[0]
    elif cmd == 'set_vss_voltage':
        targetLib.vss.voltage = args[0]
    elif cmd == 'set_pwell_voltage':
        targetLib.pwell.voltage = args[0]
    elif cmd == 'set_nwell_voltage':
        targetLib.nwell.voltage = args[0]
    elif cmd == 'set_logic_threshold_high':
        targetLib.logic_threshold_high = args[0]
    elif cmd == 'set_logic_threshold_low':
        targetLib.logic_threshold_low = args[0]
    elif cmd == 'set_logic_high_to_low_threshold':
        targetLib.logic_high_to_low_threshold = args[0]
    elif cmd == 'set_logic_low_to_high_threshold':
        targetLib.logic_low_to_high_threshold = args[0]
    elif cmd == 'set_work_dir':
        targetLib.work_dir = ''.join(args) # This should handle paths with spaces
    elif cmd == 'set_simulator':
        targetLib.simulator = ''.join(args) # This should handle paths with spaces
    elif cmd == 'set_run_sim':
        targetLib.run_sim = args[0]
    elif cmd == 'set_mt_sim':
        targetLib.mt_sim = args[0]
    elif cmd == 'set_supress_message':
        targetLib.suppress_message = args[0]
        raise PendingDeprecationWarning('WARNING: "set_supress_message" will be replaced with "set_suppress_message" in the future.')
    elif cmd == 'set_suppress_message':
        targetLib.suppress_message = args[0]
    elif cmd == 'set_supress_sim_message':
        targetLib.suppress_sim_message = args[0]
        raise PendingDeprecationWarning('WARNING: "set_supress_sim_message" will be replaced with "set_suppress_sim_message" in the future.')
    elif cmd == 'set_suppress_sim_message':
        targetLib.suppress_sim_message = args[0]
    elif cmd == 'set_supress_debug_message':
        targetLib.suppress_debug_message = args[0]
        raise PendingDeprecationWarning('WARNING: "set_supress_debug_message" will be replaced with "set_suppress_debug_message" in the future.')
    elif cmd == 'set_energy_meas_low_threshold':
        targetLib.energy_meas_low_threshold = args[0]
    elif cmd == 'set_energy_meas_high_threshold':
        targetLib.energy_meas_high_threshold = args[0]
    elif cmd == 'set_energy_meas_time_extent':
        targetLib.energy_meas_time_extent = args[0]
    elif cmd == 'set_operating_conditions':
        targetLib.operating_conditions = args[0]

    ##-- add function : common for comb. and seq. --#
    ## add_cell
    elif(command.startswith('add_cell')):
        targetCell = LogicCell()
        targetCell.add_cell(command) 

    ## add_slope
    elif(command.startswith('add_slope')):
        targetCell.add_slope(command) 

    ## add_load
    elif(command.startswith('add_load')):
        targetCell.add_load(command) 

    ## add_area
    elif(command.startswith('add_area')):
        targetCell.add_area(command) 

    ## add_netlist
    elif(command.startswith('add_netlist')):
        targetCell.add_netlist(command) 

    ## add_model
    elif(command.startswith('add_model')):
        targetCell.add_model(command) 

    ## add_simulation_timestep
    elif(command.startswith('add_simulation_timestep')):
        targetCell.add_simulation_timestep(command) 

    ##-- add function : for seq. cell --#
    ## add_flop
    elif(command.startswith('add_flop')):
        targetCell = LogicCell()
        targetCell.add_flop(command) 

    ## add_clock_slope
    elif(command.startswith('add_clock_slope')):
        targetCell.add_clock_slope(command) 

    ## add_simulation_setup_auto
    elif(command.startswith('add_simulation_setup_auto')):
        targetCell.add_simulation_setup_lowest('add_simulation_setup_lowest auto') 
        targetCell.add_simulation_setup_highest('add_simulation_setup_highest auto') 
        targetCell.add_simulation_setup_timestep('add_simulation_setup_timestep auto') 

    ## add_simulation_setup_lowest
    elif(command.startswith('add_simulation_setup_lowest')):
        targetCell.add_simulation_setup_lowest(command) 

    ## add_simulation_setup_highest
    elif(command.startswith('add_simulation_setup_highest')):
        targetCell.add_simulation_setup_highest(command) 

    ## add_simulation_setup_timestep
    elif(command.startswith('add_simulation_setup_timestep')):
        targetCell.add_simulation_setup_timestep(command) 

    ## add_simulation_hold_auto
    elif(command.startswith('add_simulation_hold_auto')):
        targetCell.add_simulation_hold_lowest('add_simulation_hold_lowest auto') 
        targetCell.add_simulation_hold_highest('add_simulation_hold_highest auto') 
        targetCell.add_simulation_hold_timestep('add_simulation_hold_timestep auto') 

    ## add_simulation_hold_lowest
    elif(command.startswith('add_simulation_hold_lowest')):
        targetCell.add_simulation_hold_lowest(command) 

    ## add_simulation_hold_highest
    elif(command.startswith('add_simulation_hold_highest')):
        targetCell.add_simulation_hold_highest(command) 

    ## add_simulation_hold_timestep
    elif(command.startswith('add_simulation_hold_timestep')):
        targetCell.add_simulation_hold_timestep(command) 

    ##-- execution --#
    ## initialize
    elif(command.startswith('create')):
        initializeFiles(targetLib, targetCell) 

    ## create
    elif(command.startswith('characterize')):
        harnessList2 = characterizeFiles(targetLib, targetCell) 
        os.chdir("../")
        #print(len(harnessList))

    ## export
    elif(command.startswith('export')):
        exportFiles(targetLib, targetCell, harnessList2) 
        num_gen_file += 1

    ## exit
    elif(command.startswith('quit') or command.startswith('exit')):
        exitFiles(targetLib, num_gen_file)

    # Handle malformed command
    else:
        raise ValueError("Invalid command")

def initializeFiles(targetLib, targetCell):
    ## initialize working directory
    if (targetLib.runsim.lower() == "true"):
        if os.path.exists(targetLib.work_dir):
            shutil.rmtree(targetLib.work_dir)
        os.mkdir(targetLib.work_dir)
    elif (targetLib.runsim.lower() == "false"):
        print("save past working directory and files\n")
    else:
        print ("Illegal setting for set_runsim option: "+targetLib.runsim+"\n")
        my_exit()
    
def characterizeFiles(targetLib, targetCell):
    print ("characterize\n")
    os.chdir(targetLib.work_dir)

    ## Branch to each logic function
    if(targetCell.logic == 'INV'):
        print ("INV\n")
        ## [in0, out0]
        expectationList2 = [['01','10'],['10','01']]
        return runCombIn1Out1(targetLib, targetCell, expectationList2,"neg")

    elif(targetCell.logic == 'BUF'):
        print ("BUF\n")
        ## [in0, out0]
        expectationList2 = [['01','01'],['10','10']]
        return runCombIn1Out1(targetLib, targetCell, expectationList2,"pos")

    elif(targetCell.logic == 'AND2'):
        print ("AND2\n")
                                         ## [in0, in1, out0]
        expectationList2 = [['01','1','01'],
                                                ['10','1','10'],
                                                ['1','01','01'],
                                                ['1','10','10']]
        return runCombIn2Out1(targetLib, targetCell, expectationList2,"pos")

    elif(targetCell.logic == 'AND3'):
        print ("AND3\n")
        ## [in0, in1, in2, in3, out0]
        expectationList2 = [['01','1','1','01'],['10','1','1','10'],\
                                                ['1','01','1','01'],['1','10','1','10'],\
                                                ['1','1','01','01'],['1','1','10','10']]
        return runCombIn3Out1(targetLib, targetCell, expectationList2,"pos")

    elif(targetCell.logic == 'AND4'):
        print ("AND4\n")
        ## [in0, in1, in2, in3,  out0]
        expectationList2 = [['01','1','1','1','01'],['10','1','1','1','10'],\
                                                ['1','01','1','1','01'],['1','10','1','1','10'],\
                                                ['1','1','01','1','01'],['1','1','10','1','10'],\
                                                ['1','1','1','01','01'],['1','1','1','10','10']]
        return runCombIn4Out1(targetLib, targetCell, expectationList2,"pos")
    
    elif(targetCell.logic == 'OR2'):
        print ("OR2\n")
        ## [in0, in1, out0]
        expectationList2 = [['01','0','01'],['10','0','10'],['0','01','01'],['0','10','10']]
        return runCombIn2Out1(targetLib, targetCell, expectationList2,"pos")

    elif(targetCell.logic == 'OR3'):
        print ("OR3\n")
        ## [in0, in1, in2, out0]
        expectationList2 = [['01','0','0','01'],['10','0','0','10'],\
                                                ['0','01','0','01'],['0','10','0','10'],\
                                                ['0','0','01','01'],['0','0','10','10']]
        return runCombIn3Out1(targetLib, targetCell, expectationList2,"pos")

    elif(targetCell.logic == 'OR4'):
        print ("OR4\n")
        ## [in0, in1, in2, in3, out0]
        expectationList2 = [['01','0','0','0','01'],['10','0','0','0','10'],\
                                                ['0','01','0','0','01'],['0','10','0','0','10'],\
                                                ['0','0','01','0','01'],['0','0','10','0','10'],\
                                                ['0','0','0','01','01'],['0','0','0','10','10']]
        return runCombIn4Out1(targetLib, targetCell, expectationList2,"pos")

    elif(targetCell.logic == 'NAND2'):
        print ("NAND2\n")
        ## [in0, in1, out0]
        expectationList2 = [['01','1','10'],\
                                                ['10','1','01'],\
                                                ['1','01','10'],\
                                                ['1','10','01']]
        return runCombIn2Out1(targetLib, targetCell, expectationList2,"neg")

    elif(targetCell.logic == 'NAND3'):
        print ("NAND3\n")
        ## [in0, in1, in2, out0]
        expectationList2 = [['01','1','1','10'],['10','1','1','01'],\
                                                ['1','01','1','10'],['1','10','1','01'],\
                                                ['1','1','01','10'],['1','1','10','01']]
        return runCombIn3Out1(targetLib, targetCell, expectationList2,"neg")

    elif(targetCell.logic == 'NAND4'):
        print ("NAND4\n")
        ## [in0, in1, in2, out0]
        expectationList2 = [['01','1','1','1','10'],['10','1','1','1','01'],\
                                                ['1','01','1','1','10'],['1','10','1','1','01'],\
                                                ['1','1','01','1','10'],['1','1','10','1','01'],\
                                                ['1','1','1','01','10'],['1','1','1','10','01']]
        return runCombIn4Out1(targetLib, targetCell, expectationList2,"neg")

    elif(targetCell.logic == 'NOR2'):
        print ("NOR2\n")
        ## [in0, in1, out0]
        expectationList2 = [['01','0','10'],['10','0','01'],['0','01','10'],['0','10','01']]
        return runCombIn2Out1(targetLib, targetCell, expectationList2,"neg")

    elif(targetCell.logic == 'NOR3'):
        print ("NOR3\n")
        ## [in0, in1, in2, out0]
        expectationList2 = [['01','0','0','10'],['10','0','0','01'],\
                                                ['0','01','0','10'],['0','10','0','01'],\
                                                ['0','0','01','10'],['0','0','10','01']]
        return runCombIn3Out1(targetLib, targetCell, expectationList2,"neg")

    elif(targetCell.logic == 'NOR4'):
        print ("NOR4\n")
        ## [in0, in1, in2, in3, out0]
        expectationList2 = [['01','0','0','0','10'],['10','0','0','0','01'],\
                                                ['0','01','0','0','10'],['0','10','0','0','01'],\
                                                ['0','0','01','0','10'],['0','0','10','0','01'],\
                                                ['0','0','0','01','10'],['0','0','0','10','01']]
        return runCombIn4Out1(targetLib, targetCell, expectationList2,"neg")

    elif(targetCell.logic == 'AO21'):
        print ("AO21\n")
        ## [in0, in1, out0]
        expectationList2 = [['10','1','0','10'],['01','1','0','01'],\
                                                ['1','10','0','10'],['1','01','0','01'],\
                                                ['0','0','10','10'],['0','0','01','01']]
        return runCombIn3Out1(targetLib, targetCell, expectationList2,"pos")

    elif(targetCell.logic == 'AO22'):
        print ("AO22\n")
        ## [in0, in1, out0]
        expectationList2 = [['10','1','0','0','10'],['01','1','0','0','01'],\
                                                ['1','10','0','0','10'],['1','01','0','0','01'],\
                                                ['0','0','10','1','10'],['0','0','01','1','01'],\
                                                ['0','0','1','10','10'],['0','0','1','01','01']]
        return runCombIn4Out1(targetLib, targetCell, expectationList2,"pos")

    elif(targetCell.logic == 'OA21'):
        print ("OA21\n")
        ## [in0, in1, out0]
        expectationList2 = [['10','0','1','10'],['01','0','1','01'],\
                                                ['0','10','1','10'],['0','01','1','01'],\
                                                ['0','1','10','10'],['0','1','01','01']]
        return runCombIn3Out1(targetLib, targetCell, expectationList2,"pos")

    elif(targetCell.logic == 'OA22'):
        print ("OA22\n")
        ## [in0, in1, out0]
        expectationList2 = [['10','1','0','1','10'],['01','1','0','1','01'],\
                                                ['0','10','0','1','10'],['0','01','0','1','01'],\
                                                ['0','1','10','0','10'],['0','1','01','0','01'],\
                                                ['0','1','0','10','10'],['0','1','0','10','01']]
        return runCombIn4Out1(targetLib, targetCell, expectationList2,"pos")

    elif(targetCell.logic == 'AOI21'):
        print ("AOI21\n")
        ## [in0, in1, out0]
        expectationList2 = [['10','1','0','01'],['01','1','0','10'],\
                                                ['1','10','0','01'],['1','01','0','10'],\
                                                ['0','0','10','01'],['0','0','01','10']]
        return runCombIn3Out1(targetLib, targetCell, expectationList2,"neg")

    elif(targetCell.logic == 'AOI22'):
        print ("AOI22\n")
        ## [in0, in1, out0]
        expectationList2 = [['10','1','0','0','01'],['01','1','0','0','10'],\
                                                ['1','10','0','0','01'],['1','01','0','0','10'],\
                                                ['0','0','10','1','01'],['0','0','01','1','10'],\
                                                ['0','0','1','10','01'],['0','0','1','01','10']]
        return runCombIn4Out1(targetLib, targetCell, expectationList2,"neg")

    elif(targetCell.logic == 'OAI21'):
        print ("OAI21\n")
        ## [in0, in1, out0]
        expectationList2 = [['10','0','1','01'],['01','0','1','10'],\
                                                ['0','10','1','01'],['0','01','1','10'],\
                                                ['0','1','10','01'],['0','1','01','10']]
        return runCombIn3Out1(targetLib, targetCell, expectationList2,"neg")

    elif(targetCell.logic == 'OAI22'):
        print ("OAI22\n")
        ## [in0, in1, out0]
        expectationList2 = [['10','1','0','1','01'],['01','1','0','1','10'],\
                                                ['0','10','0','1','01'],['0','01','0','1','10'],\
                                                ['0','1','10','0','01'],['0','1','01','0','10'],\
                                                ['0','1','0','10','01'],['0','1','0','10','10']]
        return runCombIn4Out1(targetLib, targetCell, expectationList2,"neg")

    elif(targetCell.logic == 'XOR2'):
        print ("XOR2\n")
        ## [in0, in1, out0]
        expectationList2 = [['01','0','01'],['10','0','10'],\
                                                ['01','1','10'],['10','1','01'],\
                                                ['0','01','01'],['0','10','10'],\
                                                ['1','01','10'],['1','10','01']]
        return runCombIn2Out1(targetLib, targetCell, expectationList2,"pos")

    elif(targetCell.logic == 'XNOR2'):
        print ("XNOR2\n")
        ## [in0, in1, out0]
        expectationList2 = [['01','0','10'],['10','0','01'],\
                                                ['01','1','01'],['10','1','10'],\
                                                ['0','01','10'],['0','10','01'],\
                                                ['1','01','01'],['1','10','10']]
        return runCombIn2Out1(targetLib, targetCell, expectationList2,"pos")

    elif(targetCell.logic == 'SEL2'):
        print ("SEL2\n")
        ## [in0, in1, sel, out]
        expectationList2 = [['01','0','0','01'],['10','0','0','10'],\
                                                ['0','01','1','01'],['0','10','1','10'],\
                                                ['1','0','01','10'],['1','0','10','01'],\
                                                ['0','1','01','01'],['0','1','10','10']]
        return runCombIn3Out1(targetLib, targetCell, expectationList2,"pos")

    elif(targetCell.logic == 'HA'):
        print ("HA\n")
        ## [in0, in1, cout, sum]
        expectationList2 = [['01','0','0','01'],['10','0','0','10'],\
                                                ['0','01','0','01'],['0','10','0','10'],\
                                                ['01','1','01','10'],['10','1','10','10'],\
                                                ['1','01','01','10'],['1','10','10','01']]
        return runCombIn2Out2(targetLib, targetCell, expectationList2,"pos")

    elif(targetCell.logic == 'FA'):
        print ("FA\n")
        ## [in0, in1, sel, cout, sum]
        expectationList2 = [['01','0','0','0','01'],['10','0','0','0','10'],\
                                                ['0','01','0','0','01'],['0','10','0','0','10'],\
                                                ['0','0','01','0','01'],['0','0','10','0','10'],\
                                                ['01','1','0','01','10'],['10','1','0','10','01'],\
                                                ['01','0','1','01','10'],['10','0','1','10','01'],\
                                                ['1','01','0','01','10'],['1','10','0','10','01'],\
                                                ['0','01','1','01','10'],['0','10','1','10','01'],\
                                                ['1','0','01','01','10'],['1','0','10','10','01'],\
                                                ['0','1','01','01','10'],['0','1','10','10','01'],\
                                                ['01','1','1','1','01'],['10','1','1','1','10'],\
                                                ['1','01','1','1','01'],['1','10','1','1','10'],\
                                                ['1','1','01','1','01'],['1','1','10','1','10']]
        return runCombIn3Out2(targetLib, targetCell, expectationList2,"pos")


    ## Branch to sequencial logics
    elif(targetCell.logic == 'DFF_PCPU'):
        print ("DFF, positive clock, positive unate\n")
        ## D1 & C01 -> Q01
        ## D0 & C01 -> Q10
        ## 									 [D,   C,     Q]
        expectationList2 = [['01','0101', '01'], \
                                              ['10','0101', '10']] 
        ## run spice deck for flop
        return runFlop(targetLib, targetCell, expectationList2)

    elif(targetCell.logic == 'DFF_PCNU'):
        print ("DFF, positive clock, negative unate\n")
        ## D1 & C01 -> Q01
        ## D0 & C01 -> Q10
        ## 									 [D,   C,     Q]
        expectationList2 = [['01','0101', '10'], \
                                              ['10','0101', '01']] 
        ## run spice deck for flop
        return runFlop(targetLib, targetCell, expectationList2)

    elif(targetCell.logic == 'DFF_NCPU'):
        print ("DFF, negative clock, positive unate\n")
        ## D1 & C01 -> Q01
        ## D0 & C01 -> Q10
        ## 									 [D,   C,     Q]
        expectationList2 = [['01','1010', '01'], \
                                              ['10','1010', '10']] 
        ## run spice deck for flop
        return runFlop(targetLib, targetCell, expectationList2)

    elif(targetCell.logic == 'DFF_NCNU'):
        print ("DFF, negative clock, negative unate\n")
        ## D1 & C01 -> Q01
        ## D0 & C01 -> Q10
        ## 									 [D,   C,     Q]
        expectationList2 = [['01','1010', '10'], \
                                              ['10','1010', '01']] 
        ## run spice deck for flop
        return runFlop(targetLib, targetCell, expectationList2)

    elif(targetCell.logic == 'DFF_PCPU_NR'):
        print ("DFF, positive clock, positive unate, async neg-reset\n")
        ## D1 & C01 -> Q01
        ## D0 & C01 -> Q10
        ## R01      -> Q10
        ## 									 [D,   C,    R,    Q]
        expectationList2 = [['01','0101', '1', '01'], \
                                              ['10','0101', '1', '10'], \
                                              [ '1', '0101','01', '10']]
        ## run spice deck for flop
        return runFlop(targetLib, targetCell, expectationList2)

    elif(targetCell.logic == 'DFF_PCPU_NRNS'):
        print ("DFF, positive clock, positive unate, async neg-reset, async neg-set\n")
        ## D1 & C01 -> Q01 QN10
        ## D0 & C01 -> Q10 QN01
        ## S01      -> Q01 QN10
        ## R01      -> Q10 QN01
        ## 									 [D,   C,  S,   R,    Q]
        expectationList2 = [['01','0101','1', '1', '01'], \
                                              ['10','0101','1', '1', '10'], \
                                                ['0','0101','01', '1', '01'], \
                                              ['1','0101', '1','01', '10']]

        ## run spice deck for flop
        return runFlop(targetLib, targetCell, expectationList2)

    else:
        print ("Target logic:"+targetCell.logic+" is not registered for characterization!\n")
        print ("Add characterization function for this program! -> die\n")
        my_exit()


if __name__ == '__main__':
    main()

