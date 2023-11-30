#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, os, yaml
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from liberty.parser import parse_liberty
from PySpice.Logging import Logging

from charlib.characterizer.Characterizer import Characterizer
from charlib.characterizer.functions.functions import generate_yml


def main():
    """Run CharLib"""
    # Set up charlib arguments
    parser = argparse.ArgumentParser(
            prog='charlib',
            description='Characterize combinational and sequential standard cells.')
    parser.add_argument('--debug', action='store_true',
            help='Display extra information useful for debugging')
            
    # Set up run, compare, and generate_functions subcommands
    subparser = parser.add_subparsers(title='subcomamands', required=True)
    parser_characterize = subparser.add_parser('run', help='Characterize a cell library')
    parser_compare = subparser.add_parser('compare', help='Compare two liberty files')
    parser_genfunctions = subparser.add_parser('generate_functions', help='Generate YAML maps for registered functions')

    # Set up charlib run arguments
    parser_characterize.add_argument('library', type=str,
            help='The directory containing the library characterization configuration file')
    parser_characterize.add_argument('--multithreaded', action='store_true',
            help='Enable multithreaded execution')
    parser_characterize.add_argument('--comparewith', type=str, default='',
            help='A liberty file to compare results with.')
    parser_characterize.set_defaults(func=run_charlib)

    # Set up charlib compare arguments
    def compare_helper(args):
        """Helper function for compare subcommand"""
        with open(Path(args.compared), 'r') as compared:
            compare(args.benchmark, compared.read())
    parser_compare.add_argument('benchmark',  type=str,
            help='A liberty file to use as a benchmark for comparison')
    parser_compare.add_argument('compared', type=str,
            help='A liberty file to compare against the benchmark')
    parser_compare.set_defaults(func=compare_helper)

    # Set up charlib generate_functions arguments
    def genfunctions_helper(args):
        """Helper function for generate_functions subcommand"""
        generate_yml()
    # TOOD: Add argument for expression map
    parser_genfunctions.set_defaults(func=genfunctions_helper)

    # Parse args and execute
    args = parser.parse_args()
    args.func(args)


def run_charlib(args):
    """Run characterization and return the library"""
    library_dir = args.library
    
    # Search for a YAML file with the required config information
    print(f'Searching for YAML files in {str(library_dir)}')
    config = None
    for file in Path(library_dir).rglob('*.yml'):
        try:
            with open(file, 'r') as f:
                config = yaml.safe_load(f)
                f.close()
        except yaml.YAMLError as e:
            print(e)
            print(f'Skipping "{str(file)}": file contains invalid YAML')
            continue
        if config.keys() >= {'settings', 'cells'}:
            break # We have found a YAML file with config information
    if not config:
        raise FileNotFoundError(f'Unable to locate a YAML file containing configuration settings in {library_dir} or its subdirectories.')
    print(f'Reading configuration found in "{str(file)}"')

    # Override settings with command line settings
    settings = config['settings']
    settings['debug'] = args.debug
    settings['multithreaded'] = args.multithreaded
    cells = config['cells']

    # Read in library settings
    characterizer = Characterizer(**settings)
    logger = Logging.setup_logging(logging_level='ERROR')

    # Read cells
    for name, properties in cells.items():
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

    # Characterize
    library = characterizer.characterize()

    # Export
    results_dir = characterizer.settings.results_dir
    results_dir.mkdir(parents=True, exist_ok=True)
    libfile_name = results_dir / f'{library.name}.lib'
    with open(libfile_name, 'w') as libfile:
        libfile.write(str(library))
        print(f'Results written to {str(libfile_name.resolve())}')

    # Run any post-characterization analysis
    if args.comparewith:
        compare(args.comparewith, library)


def compare(benchmark, characterized):
    """Compare prop delay and trans delay for each cell and make scatter plots"""
    charlib_rise_prop_data = []
    benchmark_rise_prop_data = []
    charlib_fall_prop_data = []
    benchmark_fall_prop_data = []
    charlib_rise_trans_data = []
    benchmark_rise_trans_data = []
    charlib_fall_trans_data = []
    benchmark_fall_trans_data = []
    
    benchmark_lib = parse_liberty(open(Path(benchmark), 'r').read())
    characterized_lib = parse_liberty(str(characterized))

    # Iterate over cells
    for charlib_cell in characterized_lib.get_groups('cell'):
        # Find this cell in the benchmark lib
        benchmark_cell = None
        for cell in benchmark_lib.get_groups('cell'):
            if cell.args[0] == charlib_cell.args[0]:
                benchmark_cell = cell
                break
        if benchmark_cell is None:
            print(f'Skipping cell "{charlib_cell.args[0]}": not found in {str(benchmark)}.')
            continue # Skip to next cell

        # Iterate over pins
        for charlib_pin in charlib_cell.get_groups('pin'):
            # Find the pin on the benchmark cell
            benchmark_pin = None
            for pin in benchmark_cell.get_groups('pin'):
                if pin.args[0] == charlib_pin.args[0]:
                    benchmark_pin = pin
                    break
            if benchmark_pin is None:
                print(f'Skipping pin "{charlib_cell.args[0]}.{charlib_pin.args[0]}": not found in {str(benchmark)}')
                continue # Skip to next pin

            # Iterate over timings
            for charlib_timing in charlib_pin.get_groups('timing'):
                # Find the timing on the benchmark pin
                benchmark_timing = None
                for timing in benchmark_pin.get_groups('timing'):
                    if timing['related_pin'] == charlib_timing['related_pin']:
                        benchmark_timing = timing
                        break
                if benchmark_timing is None:
                    print(f'Skipping timing for {charlib_cell.args[0]}.{charlib_pin.args[0]}.{charlib_timing["related_pin"]}')
                    continue

                # Average propagation delay
                charlib_rise_prop_data.append(np.mean(charlib_timing.get_groups('cell_rise')[0].get_array('values')))
                benchmark_rise_prop_data.append(np.mean(benchmark_timing.get_groups('cell_rise')[0].get_array('values')))
                charlib_fall_prop_data.append(np.mean(charlib_timing.get_groups('cell_fall')[0].get_array('values')))
                benchmark_fall_prop_data.append(np.mean(benchmark_timing.get_groups('cell_fall')[0].get_array('values')))

                # Average transient delay
                charlib_rise_trans_data.append(np.mean(charlib_timing.get_groups('rise_transition')[0].get_array('values')))
                benchmark_rise_trans_data.append(np.mean(benchmark_timing.get_groups('rise_transition')[0].get_array('values')))
                charlib_fall_trans_data.append(np.mean(charlib_timing.get_groups('fall_transition')[0].get_array('values')))
                benchmark_fall_trans_data.append(np.mean(benchmark_timing.get_groups('fall_transition')[0].get_array('values')))

    # Plot propagation delay data
    prop_figure, prop_ax = plt.subplots()
    prop_ax.grid()
    print(benchmark_rise_prop_data, charlib_rise_prop_data)
    prop_ax.scatter(benchmark_rise_prop_data, charlib_rise_prop_data, label='Rising')
    prop_ax.scatter(benchmark_fall_prop_data, charlib_fall_prop_data, label='Falling')
    prop_limits = [0, 1.1*max(max(benchmark_rise_prop_data), max(charlib_rise_prop_data))]
    prop_ax.plot(prop_limits, prop_limits, color='black', alpha=0.2, label='Ideal')
    prop_ax.set(
        xlim=prop_limits,
        ylim=prop_limits,
        xlabel='Benchmark Propagation Delay [ns]',
        ylabel='CharLib Propagation Delay [ns]',
        title='Propagation Delay Correlation'
    )
    prop_ax.legend()

    # Plot transient delay data
    tran_figure, tran_ax = plt.subplots()
    tran_ax.grid()
    tran_ax.scatter(benchmark_rise_trans_data, charlib_rise_trans_data, label='Rising')
    tran_ax.scatter(benchmark_fall_trans_data, charlib_fall_trans_data, label='Falling')
    tran_limits = [0, 1.1*max(max(benchmark_rise_trans_data), max(charlib_rise_trans_data))]
    tran_ax.plot(tran_limits, tran_limits, color='black', alpha=0.2, label='Ideal')
    tran_ax.set(
        xlim=tran_limits,
        ylim=tran_limits,
        xlabel='Benchmark Transient Delay [ns]',
        ylabel='CharLib Transient Delay [ns]',
        title='Transient Delay Correlation'
    )
    tran_ax.legend()

    plt.show()

    # Calculate absolute error
    rise_prop_ae = np.abs(np.asarray(charlib_rise_prop_data) - np.asarray(benchmark_rise_prop_data))
    fall_prop_ae = np.abs(np.asarray(charlib_fall_prop_data) - np.asarray(benchmark_fall_prop_data))
    rise_tran_ae = np.abs(np.asarray(charlib_rise_trans_data) - np.asarray(benchmark_rise_trans_data))
    fall_tran_ae = np.abs(np.asarray(charlib_fall_trans_data) - np.asarray(benchmark_fall_trans_data))
    # Calculate worst case absolute error
    rise_prop_max_ae = max(rise_prop_ae)
    fall_prop_max_ae = max(fall_prop_ae)
    rise_tran_max_ae = max(rise_tran_ae)
    fall_tran_max_ae = max(fall_tran_ae)
    # Calculate mean absolute error
    rise_prop_mae = np.mean(rise_prop_ae)
    fall_prop_mae = np.mean(fall_prop_ae)
    rise_tran_mae = np.mean(rise_tran_ae)
    fall_tran_mae = np.mean(fall_tran_ae)

    print('Rise prop', rise_prop_max_ae, rise_prop_mae)
    print('Fall prop', fall_prop_max_ae, fall_prop_mae)
    print('Rise tran', rise_tran_max_ae, rise_tran_mae)
    print('Fall tran', fall_tran_max_ae, fall_tran_mae)

if __name__ == '__main__':
    main()
