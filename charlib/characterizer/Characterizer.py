"""Dispatches characterization jobs and manages cell data"""

from multiprocessing import Pool, cpu_count
from pathlib import Path

from charlib.liberty.UnitsSettings import UnitsSettings
from charlib.liberty.library import Library
from charlib.characterizer.TestManager import TestManager, CombinationalTestManager, SequentialTestManager

class Characterizer:
    """Main object of Charlib. Keeps track of settings and cells."""

    def __init__(self, **kwargs) -> None:
        self.settings = CharacterizationSettings(**kwargs)
        self.library = Library(kwargs.get('lib_name'), **kwargs)
        self.tests = []

    def add_cell(self, name, in_ports, out_ports, functions, **kwargs):
        """Create a new logic cell test"""
        self.tests.append(
            CombinationalTestManager(name, in_ports, out_ports, functions, **kwargs)
        )

    def add_flop(self, name, in_ports, out_ports, clock, flops, functions, **kwargs):
        """Create a new sequential cell test"""
        self.tests.append(
            SequentialTestManager(name, in_ports, out_ports, clock, flops, functions, **kwargs)
        )

    def characterize(self):
        """Characterize all cells"""

        # If no target cells were given, characterize all cells
        if self.settings.use_multithreaded:
            num_workers = max(len(self.tests), cpu_count())
            with Pool(num_workers) as pool:
                cells = pool.map(self.characterize_cell, [*self.tests])
        else:
            cells = [self.characterize_cell(cell) for cell in self.tests]

        # Add cells to the library
        [self.library.add_cell(cell) for cell in cells]

        return self.library

    def characterize_cell(self, cell):
        """Characterize a single cell. Helper for multiprocessing"""
        return cell.characterize(self.settings)


class CharacterizationSettings:
    """Container for characterization settings"""
    def __init__(self, **kwargs):
        """Create a new CharacterizationSettings instance"""
        # Behavioral settings
        self.simulator = kwargs.pop('simulator', 'ngspice-shared')
        self.use_multithreaded = kwargs.pop('multithreaded', True)
        self.results_dir = Path(kwargs.pop('results_dir', 'results'))
        self.debug = kwargs.pop('debug', False)
        self.debug_dir = Path(kwargs.pop('debug_dir', 'debug'))
        self.cell_defaults = kwargs.get('cell_defaults', {})

        # Units and important voltages
        self.units = UnitsSettings(**kwargs.get('units', {}))
        nodes = kwargs.pop('named_nodes', {})
        self.vdd = NamedNode(**nodes.get('vdd', {'name':'VDD'}))
        self.vss = NamedNode(**nodes.get('vss', {'name':'VSS'}))
        self.pwell = NamedNode(**nodes.get('pwell', {'name':'VPW'}))
        self.nwell = NamedNode(**nodes.get('nwell', {'name':'VNW'}))

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
