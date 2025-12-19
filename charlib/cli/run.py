#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from pathlib import Path
from PySpice.Logging import Logging

from charlib.characterizer.characterizer import Characterizer
from charlib.cli import utils
from charlib.cli.compare import compare

def run(args):
    """Run characterization"""
    library_dir = args.library
    config = utils.find_config(library_dir)
    if not config:
        raise ValueError(f'Unable to locate a YAML file containing configuration settings in' \
                         f'{library_dir} or its subdirectories.')

    # Read in library settings
    settings = config['settings']
    cells = config['cells']
    characterizer = Characterizer(**settings)
    logger = Logging.setup_logging(logging_level='ERROR') # FIXME: logging level should be configurable

    # Override settings with command line flags
    characterizer.settings.debug = characterizer.settings.debug or args.debug
    characterizer.settings.quiet = characterizer.settings.quiet or args.quiet
    characterizer.settings.jobs = args.jobs if args.jobs else characterizer.settings.jobs

    # Filter and add cells
    if args.filters:
        cells = utils.filter_cells(cells, filters)
    [characterizer.add_cell(n, p) for (n, p) in utils.read_cell_configs(cells)]

    # Characterize
    liberty = characterizer.characterize()

    # Write to file
    if args.output:
        libfile = Path(args.output)
        if libfile.is_dir():
            libfile = libfile / characterizer.library.file_name
    else:
        libfile = characterizer.settings.results_dir / characterizer.library.file_name
    libfile.parent.mkdir(parents=True, exist_ok=True)
    with open(libfile, 'w') as f:
        f.write(str(liberty))
        if not characterizer.settings.quiet:
             print(f'Results written to {str(libfile.resolve())}')

    # Run any post-characterization analysis
    if args.comparewith:
        compare(args.comparewith, library)
