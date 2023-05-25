#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, os, yaml
from pathlib import Path

from characterizer.Characterizer import Characterizer
from liberty.LibrarySettings import LibrarySettings
from liberty.ExportUtils import exportFiles, exitFiles


def main():
    """Reads in command line arguments, then enters the requested execution mode.

    Batch mode (-b arg) executes a batch of commands from the specified batchfile.

    Library mode (-l arg) searches for a YAML configuration file in the specified directory, then
    characterizes cells according to that configuration.
    
    If a mode is not specified, we enter shell mode to read in commands one at a time."""
    
    # Read in arguments
    parser = argparse.ArgumentParser(
            prog='CharLib',
            description='Characterize combinational and sequential standard cells.',
            epilog='If no options are provided, a shell is launched where users may enter CharLib commands.')
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
    """Parse a library of standard cells and characterize"""

    print("Searching for YAML files in " + str(library_dir))
    # Search for a YAML file with the required config information
    config = None
    for file in Path(library_dir).rglob('*.yml'):
        try:
            with open(file, 'r') as f:
                config = yaml.safe_load(f)
                f.close()
        except yaml.YAMLError:
            print(f'Skipping "{str(file)}": file contains invalid YAML')
            continue
        if config.keys() >= {'settings', 'cells'}:
            break # We have found a YAML file with config information
    if not config:
        raise FileNotFoundError(f'Unable to locate a YAML file containing configuration settings in {library_dir} or its subdirectories.')

    # Read in library settings
    characterizer.settings = LibrarySettings(**config['settings'])

    # Read cells
    for name, properties in config['cells'].items():
        # If properties is a (name, filepath) pair, fetch cell config from YAML at filepath
        if isinstance(properties, str):
            # Search within library_dir for the specified file
            for file in Path(library_dir).rglob(properties):
                with open(file, 'r') as f:
                    properties = yaml.safe_load(f)
                    f.close()
                    break # Quit searching after successfully reading a match

        # Merge settings.cell_defaults into properties, keeping entries from properties
        for key, value in characterizer.settings.cell_defaults.items():
            if not key in properties.keys():
                properties[key] = value

        # Read config data for this cell
        inputs = properties.pop('inputs')
        outputs = properties.pop('outputs')
        functions = properties.pop('functions')
        clock = properties.pop('clock', None)
        flops = properties.pop('flops', [])

        # Add cells
        if clock:
            characterizer.add_flop(name, inputs, outputs, clock, flops, functions, **properties)
        else:
            characterizer.add_cell(name, inputs, outputs, functions, **properties)

    # TODO: Add print statements to display which keys in YAML were not used

    # Initialize workspace, characterize, and export
    characterizer.initialize_work_dir()
    characterizer.characterize()
    for cell in characterizer.cells:
        exportFiles(characterizer.settings, cell)
        characterizer.num_files_generated += 1
    exitFiles(characterizer.settings, characterizer.num_files_generated)

def execute_shell(characterizer: Characterizer):
    """Enter CharLib shell"""

    print("Entering CharLib shell. Type 'exit' or ^C to quit")
    
    exit_flag = False
    try:
        while not exit_flag:
            command = input('CharLib > ')
            try:
                execute_command(characterizer, command)
            except ValueError as e:
                print(str(e))
            if command == 'exit' or command == 'quit':
                exit_flag = True
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Exiting...")

def execute_command(characterizer: Characterizer, command: str):
    (cmd, *args) = command.split()
    if not command[0] == '#':
        characterizer.print_debug(f'Executing {command}')
    
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
            characterizer.settings.units.power = args[0]
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
            characterizer.settings.use_multithreaded = args[0]
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
                    pass
                elif opt.startswith('i '): # -i option
                    in_ports = opt[2:].strip().split()
                elif opt.startswith('o '): # -o option
                    out_ports = opt[2:].strip().split()
                elif opt.startswith('f '): # -f option
                    function = opt[2:].strip()
                else:
                    raise ValueError(f'Unrecognized option: -{opt}')
            characterizer.add_cell(name, in_ports, out_ports, function) 
        elif cmd == 'add_flop':
            area = 0
            opts = ' '.join(args).strip().split('-')[1:] # Split on hyphen instead of space
            set_pin = None
            reset_pin = None
            for opt in opts:
                if opt.startswith('n '):
                    name = opt[2:].strip()
                    for cell in characterizer.cells: # Search cells in case we added this cell previously using add_cell
                        if cell.name == name:
                            in_ports = cell.in_ports
                            out_ports = cell.out_ports
                            function = cell.function
                            area = cell.area
                            characterizer.cells.remove(cell)
                elif opt.startswith('l '):
                    pass # Ignore logic argument
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
            kwargs = {}
            if set_pin:
                kwargs['set_pin'] = set_pin
            if reset_pin:
                kwargs['reset_pin'] = reset_pin
            characterizer.add_flop(name, in_ports, out_ports, clock_pin, flops, function, area, **kwargs)
        elif cmd == 'add_slope':
            # Expected arg format: {1 2 ... N}
            for arg in args:
                if '{' in arg:
                    arg = arg.replace('{', '')
                if '}' in arg:
                    arg = arg.replace('}', '')
                characterizer.last_cell().add_in_slew(float(arg))
        elif cmd == 'add_load':
            # Expected arg format: {1 2 ... N}
            for arg in args:
                if '{' in arg:
                    arg = arg.replace('{', '')
                if '}' in arg:
                    arg = arg.replace('}', '')
                characterizer.last_cell().add_out_load(float(arg))
        elif cmd == 'add_area':
            characterizer.last_cell().area = args[0]
        elif cmd == 'add_netlist':
            characterizer.last_cell().netlist = args[0]
        elif(command.startswith('add_model')):
            characterizer.last_cell().model = args[0]
        elif(command.startswith('add_simulation_timestep')):
            characterizer.last_cell().sim_timestep = args[0]
        elif cmd == 'add_clock_slope':
            characterizer.last_cell().clock_slope = args[0]
        elif(command.startswith('add_simulation_setup_auto')):
            characterizer.last_cell().sim_setup_lowest = 'auto'
            characterizer.last_cell().sim_setup_highest = 'auto'
            characterizer.last_cell().sim_setup_timestep = 'auto'
        elif cmd == 'add_simulation_setup_lowest':
            characterizer.last_cell().sim_setup_lowest = args[0]
        elif(command.startswith('add_simulation_setup_highest')):
            characterizer.last_cell().simulation_setup = args[0]
        elif(command.startswith('add_simulation_setup_timestep')):
            characterizer.last_cell().sim_setup_timestep = args[0]
        elif(command.startswith('add_simulation_hold_auto')):
            characterizer.last_cell().sim_hold_lowest = 'auto'
            characterizer.last_cell().sim_hold_highest = 'auto'
            characterizer.last_cell().sim_hold_timestep = 'auto'
        elif(command.startswith('add_simulation_hold_lowest')):
            characterizer.last_cell().sim_hold_lowest = args[0]
        elif(command.startswith('add_simulation_hold_highest')):
            characterizer.last_cell().sim_hold_highest = args[0]
        elif(command.startswith('add_simulation_hold_timestep')):
            characterizer.last_cell().sim_hold_timestep = args[0]

    # get command
    elif cmd.startswith('get_'):
        if cmd == 'get_all': 
            print(str(characterizer))
        elif cmd == 'get_settings':
            print(str(characterizer.settings))
        elif cmd == 'get_cell_names':
            if characterizer.cells:
                for cell in characterizer.cells:
                    print(str(cell.name))
            else:
                print('No cells to display. Add cells using the add_cell and add_flop commands.')
        elif cmd == 'get_cells':
            if characterizer.cells:
                for cell in characterizer.cells:
                    print(str(cell))
            else:
                print('No cells to display. Add cells using the add_cell and add_flop commands.')
        elif cmd == 'get_cell_by_name':
            if characterizer.cells:
                print(str([cell for cell in characterizer.cells if cell.name == args[0]][0]))

    # execution
    elif cmd == 'create' or cmd == 'initialize':
        characterizer.initialize_work_dir()
    elif(command.startswith('characterize')):
        characterizer.characterize(*[cell for cell in characterizer.cells if cell.name in args])

    # export
    elif(command.startswith('export')):
        # If called with no cell names passed, export all cells
        cells = [cell for cell in characterizer.cells if cell.name in args]
        for cell in cells if cells else characterizer.cells:
            exportFiles(characterizer.settings, cell)
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

def load_settings(characterizier: Characterizer, settings_json: Path):
    pass # TODO

if __name__ == '__main__':
    main()
