#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, os, yaml
from pathlib import Path

from PySpice.Logging import Logging

from characterizer.Characterizer import Characterizer

def main():
    """Run CharLib"""
    # Read in arguments
    parser = argparse.ArgumentParser(
            prog='CharLib',
            description='Characterize combinational and sequential standard cells.')
    parser.add_argument('library', type=str,
            help='Read in a library of standard cells from the specified directory and characterize')
    parser.add_argument('--multithreaded', action='store_true',
            help='Enable multithreaded execution')
    parser.add_argument('--debug', action='store_true',
            help='Display extra information useful for debugging')
    # TODO: consider adding a -v/--verbose argument and debug options
    args = parser.parse_args()
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

    # Read in library settings
    characterizer = Characterizer(**settings)
    logger = Logging.setup_logging(logging_level='ERROR')

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

    # Characterize
    library = characterizer.characterize()

    # Export
    results_dir = characterizer.settings.results_dir
    results_dir.mkdir(parents=True, exist_ok=True)
    libfile_name = results_dir / f'{library.name}.lib'
    with open(libfile_name, 'w') as libfile:
        libfile.write(str(library))
        print(f'Results written to {str(libfile_name.resolve())}')
    

if __name__ == '__main__':
    main()
