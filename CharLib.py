#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, os

from characterizer.Characterizer import Characterizer
from characterizer.ExportUtils import exportFiles, exitFiles


def main():
    """Reads in command line arguments, then enters the requested execution mode.

    Batch mode (-b arg) executes a batch of commands from the specified cmd file.
    Library mode (-l arg) parses in a user-provided library from the specified directory
    and	characterizes it automatically. If a mode is not specified, we enter shell mode 
    to read in commands one at a time."""
    
    # Read in arguments
    parser = argparse.ArgumentParser(
            prog='CharLib',
            description='Characterize combinational and sequential standard cells.',
            epilog='If no options are provided, a shell is launched where users may enter CharLib commands using cmd file syntax.')
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('-b','--batch', type=str,
            help='Execute specified batch .cmd file')
    mode_group.add_argument('-l', '--library', type=str,
            help='Read in a library of standard cells from the specified directory, and automatically characterize')
    args = parser.parse_args()

    # Dispatch based on operating mode
    characterizer = Characterizer()
    if args.batch is not None:
        execute_batch(characterizer, args.batch)
    elif args.library is not None:
        execute_lib(characterizer, args.library)
    else:
        execute_shell(characterizer)

def execute_batch(characterizer: Characterizer, batchfile):
    """Read in a batch of commands from batchfile and execute."""

    print("Executing batch file " + batchfile)

    # file open
    with open(batchfile, 'r') as f:
        lines = f.readlines()
        f.close()
    
    for line in lines:
        line = line.strip()
        if len(line) > 0:
            execute_command(characterizer, line)

def execute_lib(characterizer: Characterizer, library_dir):
    """Parse a library of standard files, generate a cmd file, and characterize"""

    # TODO: Find sc library
    print("Searching for standard cells in " + str(library_dir))

    # TODO: Read in settings.json (or whatever we decide to call it)
    # and apply settings to characterizer

def execute_shell(characterizer: Characterizer):
    """Enter CharLib shell"""

    print("Entering CharLib shell. Type 'exit' or ^C to quit")
    
    exit_flag = False
    try:
        while not exit_flag:
            command = input('CharLib > ')
            try:
                execute_command(characterizer, command)
            except ValueError:
                print('Invalid command.')
            if command == 'exit' or command == 'quit':
                exit_flag = True
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Exiting...")

def execute_command(characterizer: Characterizer, command: str):
    (cmd, *args) = command.split()
    characterizer.print_debug(f'Executing {command}')

    # TODO: Add display commands to print all settings
    
    # set command
    if cmd.startswith('set_'):
        # common settings
        if cmd == 'set_lib_name':
            characterizer.settings.lib_name = args[0]
        elif cmd == 'set_dotlib_name':
            characterizer.settings.dotlib_name = args[0]
        elif cmd == 'set_verilog_name':
            characterizer.settings.verilog_name = args[0]
        elif cmd == 'set_cell_name_suffix':
            characterizer.settings.cell_name_suffix = args[0]
        elif cmd == 'set_cell_name_prefix':
            characterizer.settings.cell_name_prefix = args[0]
        elif cmd == 'set_voltage_unit':
            characterizer.settings.units.voltage = args[0]
        elif cmd == 'set_capacitance_unit':
            characterizer.settings.units.capacitance = args[0]
        elif cmd == 'set_resistance_unit':
            characterizer.settings.units.resistance = args[0]
        elif cmd == 'set_time_unit':
            characterizer.settings.units.time = args[0]
        elif cmd == 'set_current_unit':
            characterizer.settings.units.current = args[0]
        elif cmd == 'set_leakage_power_unit':
            characterizer.settings.units.leakage_power = args[0]
        elif cmd == 'set_energy_unit':
            characterizer.settings.units.energy = args[0]
        elif cmd == 'set_vdd_name':
            characterizer.settings.vdd.name = args[0]
        elif cmd == 'set_vss_name':
            characterizer.settings.vss.name = args[0]
        elif cmd == 'set_pwell_name':
            characterizer.settings.pwell.name = args[0]
        elif cmd == 'set_nwell_name':
            characterizer.settings.nwell.name = args[0]

        # characterization settings
        elif cmd == 'set_process':
            characterizer.settings.process = args[0]
        elif cmd == 'set_temperature':
            characterizer.settings.temperature = float(args[0])
        elif cmd == 'set_vdd_voltage':
            characterizer.settings.vdd.voltage = float(args[0])
        elif cmd == 'set_vss_voltage':
            characterizer.settings.vss.voltage = float(args[0])
        elif cmd == 'set_pwell_voltage':
            characterizer.settings.pwell.voltage = float(args[0])
        elif cmd == 'set_nwell_voltage':
            characterizer.settings.nwell.voltage = float(args[0])
        elif cmd == 'set_logic_threshold_high':
            characterizer.settings.logic_threshold_high = float(args[0])
        elif cmd == 'set_logic_threshold_low':
            characterizer.settings.logic_threshold_low = float(args[0])
        elif cmd == 'set_logic_high_to_low_threshold':
            characterizer.settings.logic_high_to_low_threshold = float(args[0])
        elif cmd == 'set_logic_low_to_high_threshold':
            characterizer.settings.logic_low_to_high_threshold = float(args[0])
        elif cmd == 'set_work_dir':
            characterizer.settings.work_dir = ''.join(args) # This should handle paths with spaces
        elif cmd == 'set_simulator':
            characterizer.settings.simulator = ''.join(args) # This should handle paths with spaces
        elif cmd == 'set_run_sim':
            characterizer.settings.run_sim = args[0]
        elif cmd == 'set_mt_sim':
            characterizer.settings.mt_sim = args[0]
        elif cmd == 'set_supress_message':
            print('WARNING: "set_supress_message" will be replaced with "set_suppress_message" in the future.')
            characterizer.settings.suppress_message = args[0]
        elif cmd == 'set_suppress_message':
            characterizer.settings.suppress_message = args[0]
        elif cmd == 'set_supress_sim_message':
            print('WARNING: "set_supress_sim_message" will be replaced with "set_suppress_sim_message" in the future.')
            characterizer.settings.suppress_sim_message = args[0]
        elif cmd == 'set_suppress_sim_message':
            characterizer.settings.suppress_sim_message = args[0]
        elif cmd == 'set_supress_debug_message':
            print('WARNING: "set_supress_debug_message" will be replaced with "set_suppress_debug_message" in the future.')
            characterizer.settings.suppress_debug_message = args[0]
        elif cmd == 'set_energy_meas_low_threshold':
            characterizer.settings.energy_meas_low_threshold = float(args[0])
        elif cmd == 'set_energy_meas_high_threshold':
            characterizer.settings.energy_meas_high_threshold = float(args[0])
        elif cmd == 'set_energy_meas_time_extent':
            characterizer.settings.energy_meas_time_extent = float(args[0])
        elif cmd == 'set_operating_conditions':
            characterizer.settings.operating_conditions = args[0]

    # add command
    elif cmd.startswith('add_'):
        if cmd == 'add_cell':
            opts = ' '.join(args).strip().split('-')[1:] # Split on hyphen instead of space
            for opt in opts:
                if opt.startswith('n '): # -n option
                    name = opt[2:].strip()
                elif opt.startswith('l '): # -l option
                    logic = opt[2:].strip()
                elif opt.startswith('i '): # -i option
                    in_ports = opt[2:].strip().split()
                elif opt.startswith('o '): # -o option
                    out_ports = opt[2:].strip().split()
                elif opt.startswith('f '): # -f option
                    function = opt[2:].strip()
                else:
                    raise ValueError(f'Unrecognized option: -{opt}')
            characterizer.add_cell(name, logic, in_ports, out_ports, function) 
        elif cmd == 'add_flop':
            area = 0
            opts = ' '.join(args).strip().split('-')[1:] # Split on hyphen instead of space
            for opt in opts:
                if opt.startswith('n '):
                    name = opt[2:].strip()
                    for cell in characterizer.cells: # Search cells in case we added this cell previously using add_cell
                        if cell.name == name:
                            logic = cell.logic
                            in_ports = cell.in_ports
                            out_ports = cell.out_ports
                            function = cell.function
                            area = cell.area
                            characterizer.cells.remove(cell)
                elif opt.startswith('l '):
                    logic = opt[2:].strip()
                elif opt.startswith('i '):
                    in_ports = opt[2:].strip()
                elif opt.startswith('o '):
                    out_ports = opt[2:].strip()
                elif opt.startswith('c '):
                    clock_pin = opt[2:].strip()
                elif opt.startswith('s '):
                    set_pin = opt[2:].strip()
                elif opt.startswith('r '):
                    reset_pin = opt[2:].strip()
                elif opt.startswith('q '):
                    flops = opt[2:].strip()
                elif opt.startswith('f '):
                    function = opt[2:].strip()
                else:
                    raise ValueError(f'Unrecognized option: -{opt}')
            characterizer.add_flop(name, logic, in_ports, out_ports, clock_pin, set_pin, reset_pin, flops, function, area)
        elif cmd == 'add_slope':
            # Expected arg format: {1 2 ... N}
            for arg in args:
                if '{' in arg:
                    arg = arg.replace('{', '')
                if '}' in arg:
                    arg = arg.replace('}', '')
                characterizer.target_cell().add_in_slope(float(arg))
        elif cmd == 'add_load':
            # Expected arg format: {1 2 ... N}
            for arg in args:
                if '{' in arg:
                    arg = arg.replace('{', '')
                if '}' in arg:
                    arg = arg.replace('}', '')
                characterizer.target_cell().add_out_load(float(arg))
        elif cmd == 'add_area':
            characterizer.target_cell().area = args[0]
        elif cmd == 'add_netlist':
            characterizer.target_cell().netlist = args[0]
        elif(command.startswith('add_model')):
            characterizer.target_cell().add_model(command)
        elif(command.startswith('add_simulation_timestep')):
            characterizer.target_cell().add_simulation_timestep(command)
        elif cmd == 'add_clock_slope':
            characterizer.target_cell().clock_slope = args[0]
        elif(command.startswith('add_simulation_setup_auto')):
            characterizer.target_cell().add_simulation_setup_lowest('add_simulation_setup_lowest auto')
            characterizer.target_cell().add_simulation_setup_highest('add_simulation_setup_highest auto')
            characterizer.target_cell().add_simulation_setup_timestep('add_simulation_setup_timestep auto')
        elif cmd == 'add_simulation_setup_lowest':
            characterizer.target_cell().sim_setup_lowest = args[0]
        elif(command.startswith('add_simulation_setup_highest')):
            characterizer.target_cell().add_simulation_setup_highest(command)
        elif(command.startswith('add_simulation_setup_timestep')):
            characterizer.target_cell().add_simulation_setup_timestep(command)
        elif(command.startswith('add_simulation_hold_auto')):
            characterizer.target_cell().add_simulation_hold_lowest('add_simulation_hold_lowest auto')
            characterizer.target_cell().add_simulation_hold_highest('add_simulation_hold_highest auto')
            characterizer.target_cell().add_simulation_hold_timestep('add_simulation_hold_timestep auto')
        elif(command.startswith('add_simulation_hold_lowest')):
            characterizer.target_cell().add_simulation_hold_lowest(command)
        elif(command.startswith('add_simulation_hold_highest')):
            characterizer.target_cell().add_simulation_hold_highest(command)
        elif(command.startswith('add_simulation_hold_timestep')):
            characterizer.target_cell().add_simulation_hold_timestep(command)

    # execution
    elif cmd == 'create' or cmd == 'initialize':
        characterizer.initialize_work_dir()
    elif(command.startswith('characterize')):
        characterizer.characterize(characterizer.target_cell())
        os.chdir("../")

    # export
    elif(command.startswith('export')):
        exportFiles(characterizer.settings, characterizer.target_cell())
        characterizer.num_files_generated += 1

    # exit
    elif cmd == 'quit' or cmd == 'exit':
        exitFiles(characterizer.settings, characterizer.num_files_generated)

    # comment
    elif command.startswith('#'):
        pass

    # Handle malformed command
    else:
        raise ValueError(f'Invalid command: {command}')


if __name__ == '__main__':
    main()
