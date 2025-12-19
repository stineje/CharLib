#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from pathlib import Path

from charlib.cli import run, compare, generate_functions

def main():
    """Run CharLib CLI"""
    # Set up charlib arguments
    parser = argparse.ArgumentParser(
        prog='charlib',
        description='Standard cell library characterizer')
    parser.add_argument(
        '--debug', action='store_true',
        help='Dump extra information to debug_dir')
    parser.add_argument(
        '-q', '--quiet', action='store_true',
        help='Reduce the amount of information displayed')

    # Set up run, compare, and generate_functions subcommands
    subparser = parser.add_subparsers(title='subcomamands', required=True)
    parser_characterize = subparser.add_parser('run', help='Characterize a standard cell library')
    parser_compare = subparser.add_parser(
        'compare',
        help='(experimental) Compare two liberty files')
    parser_genfunctions = subparser.add_parser(
        'generate_functions',
        help='(experimental) Generate YAML maps for registered functions')

    # Set up charlib run arguments
    parser_characterize.add_argument(
        'library', type=str,
        help='The directory containing the library characterization configuration file, or the full path to the file')
    parser_characterize.add_argument(
        '-o', '--output', type=str, default='',
        help='Place the characterization results in the specified file')
    parser_characterize.add_argument(
        '-j', '--jobs', type=int, default=0,
        help='Specify the number of concurrent jobs')
    parser_characterize.add_argument(
        '--comparewith', type=str, default='',
        help='(experimental) A liberty file to compare results with')
    parser_characterize.add_argument(
        '-f', '--filters', nargs='*',
        help='A list of one or more regex strings. charlib will only characterize cells matching one or more of the filters.')
    parser_characterize.set_defaults(func=run.run)

    # Set up charlib compare arguments
    def compare_helper(args):
        """Helper function for compare subcommand"""
        with open(Path(args.compared), 'r') as compared:
            compare.compare(args.benchmark, compared.read())
    parser_compare.add_argument(
        'benchmark',  type=str,
        help='A liberty file to use as a benchmark for comparison')
    parser_compare.add_argument(
        'compared', type=str,
        help='A liberty file to compare against the benchmark')
    parser_compare.set_defaults(func=compare_helper)

    # Set up charlib generate_functions arguments
    parser_genfunctions.add_argument(
        'expressions', type=str, nargs='*',
        help='One or more expressions to generate test vector mappings for')
    parser_genfunctions.set_defaults(func=generate_functions.generate_functions)

    # Parse args and execute
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
