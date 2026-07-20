import re, yaml
from pathlib import Path

from charlib.config.syntax import ConfigFile
from schema import SchemaError

def find_yaml_files(path) -> list:
    """Return a list of Paths containing all YAML files in the directory specified by `path`."""
    path = Path(path)
    if path.is_file():
        return [path]
    elif path.is_dir():
        return list(path.rglob('*.yaml')) + list(path.rglob('*.yml'))
    else:
        return []


def resolve_subkey(value, base_dir):
    """If a config value ends in .yml or .yaml, resolve it to the YAML contents."""
    if isinstance(value, str):
        if not value.lower().endswith(('.yml', '.yaml')):
            return value
        possible_yamls = find_yaml_files(Path(base_dir) / value)
        if len(possible_yamls) != 1:
            raise ValueError(f'Unable to resolve {value} to a unique existing file')
        with open(possible_yamls[0]) as file:
            return yaml.safe_load(file)
    return value


def find_config(config_path, quiet=True):
    """Find an appropriately-formatted YAML file in `config_path`"""

    if not quiet:
        print(f'Searching for YAML files at {str(config_path)}')
    config = None
    for file in find_yaml_files(config_path):
        # Load the file
        try:
            with open(file) as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            if not quiet:
                print(e)
                print(f'Skipping "{str(file)}": file contains invalid YAML')
            continue
        # Ensure the file contains a config dictionary
        if not isinstance(config, dict):
            if not quiet:
                print(f'Skipping "{str(file)}": file does not contain a config dict')
            continue
        # Substitute in config keys which point to other YAML files or directories
        config = {k: resolve_subkey(v, file.parent) for k, v in config.items()}
        # Validate the schema
        try:
            config = ConfigFile.validate(config)
            break # Exit on success
        except SchemaError:
            if not quiet:
                print(f'Skipping "{str(file)}": file does not contain a valid CharLib config')
            config = None
    if not isinstance(config, dict):
        raise FileNotFoundError(f'No valid configuration found in {config_path}')
    return config


def filter_cells(cells: dict, filters: list) -> dict:
    """Filter the dict of cells by name against a list of regex filter patterns."""
    filtered_cells = {}
    filters = [re.compile(f) for f in filters]
    for name in cells: # Check each cell name against each filter pattern until we get a match
        for pattern in filters:
            if pattern.search(name):
                filtered_cells[name] = cells[name]
                break # We've already matched this cell, quit searching
    return filtered_cells


def read_cell_configs(cells):
    """Yield cell names and property dicts from a dict of cells.

    This function also handles the case where cell properties are stored in another file. In this
    case it reads the file and makes sure the properties are in dict format."""
    for name, properties in cells.items():
        # If properties is a (name, filepath) pair, fetch cell config from YAML at filepath
        if isinstance(properties, str):
            # Search the directory for valid YAML
            for file in find_yaml_files(properties):
                try:
                    with open(file, 'r') as f:
                        properties = yaml.safe_load(f)
                    break # Quit searching after successfully reading a match
                except yaml.YAMLError as e:
                    if not quiet:
                        print(e)
                        print(f'Skipping "{str(file)}": file contains invalid YAML')
                    continue
        yield (name, properties)
