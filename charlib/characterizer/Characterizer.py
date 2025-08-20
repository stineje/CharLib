"""Dispatches characterization jobs and manages cell data"""

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from charlib.characterizer.cell import Cell, CellTestConfig
from charlib.liberty.UnitsSettings import UnitsSettings

class Characterizer:
    """Main object of Charlib. Keeps track of settings and cells, and schedules simulations."""

    def __init__(self, **kwargs) -> None:
        self.settings = CharacterizationSettings(**kwargs)
        self.cells = []

    def add_cell(self, name: str, properties: dict):
        """Add a cell to be characterized"""
        netlist = properties.pop('netlist')
        functions = properties.pop('functions')
        special_pins = {self.settings.primary_power.name: 'primary_power',
                        self.settings.primary_ground.name: 'primary_ground',
                        self.settings.pwell.name: 'pwell',
                        self.settings.nwell.name: 'nwell'}
        # TODO: Handle other special pins
        logic_pins = {}
        if 'inputs' in properties and 'outputs' in properties:
            logic_pins['inputs'] = properties.pop('inputs')
            logic_pins['outputs'] = properties.pop('outputs')
        cell = Cell(name, netlist, functions, logic_pins, special_pins)
        models = properties.pop('models')
        config = CellTestConfig(models, **properties)
        self.cells.append((cell, config))

    def characterize(self):
        """Characterize all cells"""
        # Consider using tqdm to display progress
        # TODO: Figure out how to optimize number of jobs here. For some reason -j2 is fastest on my Ryzen 7600 system, which doesn't make a ton of sense
        with ProcessPoolExecutor(self.settings.jobs) as executor:
            return [cell for cell in executor.map(self.characterize_cell, self.tests)]

    def schedule(self, simulation, key):
        """Schedule a simulation job that produces the results for key

        :param simulation: a callable which returns a liberty-compatible object.
        :param key: a string containing the dot-indexed location within the liberty library where
                    results should be saved.
        """
        self.executor.submit(simulation)


class CharacterizationSettings:
    """Container for characterization settings"""
    def __init__(self, **kwargs):
        """Create a new CharacterizationSettings instance"""
        # Behavioral settings
        self.simulator = kwargs.pop('simulator', 'ngspice-shared')
        self.jobs = None if kwargs.pop('multithreaded', True) else 1
        self.results_dir = Path(kwargs.pop('results_dir', 'results'))
        self.debug = kwargs.pop('debug', False)
        self.debug_dir = Path(kwargs.pop('debug_dir', 'debug'))
        self.quiet = kwargs.pop('quiet', False)
        self.cell_defaults = kwargs.get('cell_defaults', {})
        self.omit_on_failure = kwargs.get('omit_on_failure', False)

        # Units and important voltages
        self.units = UnitsSettings(**kwargs.get('units', {}))
        nodes = kwargs.pop('named_nodes', {})
        self.primary_power = NamedNode(**nodes.get('primary_power', {'name':'VDD', 'voltage': 3.3}))
        self.primary_ground = NamedNode(**nodes.get('primary_ground', {'name':'VSS', 'voltage': 0}))
        self.pwell = NamedNode(**nodes.get('pwell', {'name':'VPW', 'voltage': 0}))
        self.nwell = NamedNode(**nodes.get('nwell', {'name':'VNW', 'voltage': 3.3}))

        # Logic thresholds
        logic_thresholds = kwargs.get('logic_thresholds', {})
        self.logic_threshold_low = logic_thresholds.get('low', 0.2)
        self.logic_threshold_high = logic_thresholds.get('high', 0.8)
        self.logic_threshold_high_to_low = logic_thresholds.get('high_to_low', 0.5)
        self.logic_threshold_low_to_high = logic_thresholds.get('low_to_high', 0.5)

        # Operating conditions
        self.temperature = kwargs.get('temperature', 25)


class NamedNode:
    """Binds supply node names to voltages"""
    def __init__(self, name, voltage = 0):
        self.name = name
        self.voltage = voltage

    def __str__(self) -> str:
        return f'Name: {self.name}\nVoltage: {self.voltage}'

    def __repr__(self) -> str:
        return f'NamedNode({self.name}, {self.voltage})'
