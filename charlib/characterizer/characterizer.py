"""Dispatches characterization jobs and manages cell data"""

from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from tqdm import tqdm

import matplotlib.pyplot as plt

from charlib.characterizer import utils, plots
from charlib.characterizer.cell import Cell, CellTestConfig
from charlib.characterizer.units import UnitsSettings
from charlib.characterizer.procedures import registered_procedures, ProcedureFailedException
from charlib.liberty.library import Library

import charlib.characterizer.procedures.pin_capacitance.ac_sweep
import charlib.characterizer.procedures.combinational.delay
import charlib.characterizer.procedures.sequential.delay
import charlib.characterizer.procedures.sequential.constraint.metastability.binary_search
import charlib.characterizer.procedures.sequential.constraint.metastability.c2q_contour
import charlib.characterizer.procedures.sequential.constraint.recovery
import charlib.characterizer.procedures.sequential.constraint.removal
import charlib.characterizer.procedures.sequential.constraint.min_pulse_width

class Characterizer:
    """Main object of Charlib. Keeps track of settings and cells, and schedules simulations."""

    def __init__(self, **kwargs) -> None:
        self.settings = CharacterizationSettings(**kwargs)
        self.library = Library(kwargs.pop('lib_name'), **self.settings.liberty_attrs_as_dict())
        self.cells = []

    def add_cell(self, name: str, properties: dict):
        """Add a cell to be characterized"""
        # Get pg_pins from library settings, then construct the cell
        supply_pins = {self.settings.primary_power.name: 'primary_power',
                       self.settings.primary_ground.name: 'primary_ground',
                       self.settings.pwell.name: 'pwell',
                       self.settings.nwell.name: 'nwell'}
        cell = Cell(name, supply_pins, **properties)

        # Handle keywords for plots
        if properties.get('plots', []) == 'all':
            properties['plots'] = ['delay', 'io']
        config = CellTestConfig(properties.pop('models'), **properties)
        self.cells.append((cell, config))

    def analyse_cell(self, cell, config) -> list:
        """Return a list of callable characterization tasks required for this cell."""
        simulations = []

        # Measure input pin capacitances
        simulations += self.settings.simulation.input_capacitance(cell, config, self.settings)

        # Identify which delay and constraint procedures to run based on cell & config
        if cell.is_sequential:
            # Find setup & hold constraints (clock-to-q, en-to-q)
            simulations += self.settings.simulation.metastability_constraint(cell, config, self.settings)
            # TODO: Find minimum pulse width constraints (set, reset, enable, clock)
            # Find recovery & removal constraints (clk/en-to-set, clk/en-to-reset)
            simulations += self.settings.simulation.recovery_constraint(cell, config, self.settings)
            simulations += self.settings.simulation.removal_constraint(cell, config, self.settings)
            # Measure sequential propagation and transient delays
            simulations += self.settings.simulation.sequential_delay(cell, config, self.settings)
        else:
            # Measure combinational propagation and transient delays
            simulations += self.settings.simulation.combinational_delay(cell, config, self.settings)
        return simulations

    def characterize(self):
        """Execute scheduled simulation jobs in parallel"""
        # Setup: Prepare simulation jobs single-threadedly (is that a word?)
        simulation_tasks = []
        for (cell, config) in self.cells:
            simulation_tasks += self.analyse_cell(cell, config)

        # Run all simulation jobs and merge each resulting liberty cell group into the library
        with tqdm(bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
                  total=len(simulation_tasks), desc="Characterizing") as progress_bar:
            with ProcessPoolExecutor(max_workers=self.settings.jobs) as executor:
                futures = [executor.submit(task, *args) for (task, *args) in simulation_tasks]
                for future in as_completed(futures):
                    try:
                        cell_group = future.result()
                    except ProcedureFailedException:
                        if self.settings.omit_on_failure:
                            continue
                        else:
                            raise
                    self.library.add_group(cell_group)
                    progress_bar.update(1)

        # Post-processing: Fetch generated table templates and add them to the library
        lut_templates = []
        for timing_group in self.library.subgroups_with_name('timing'):
            lut_templates += [lut_group.template for lut_group in timing_group.groups.values()]
        [self.library.add_group(lut_template) for lut_template in lut_templates]

        # Plot delay surfaces (if desired)
        for (cell, config) in self.cells:
            cell_group = self.library.group('cell', cell.name)
            if 'delay' in config.plots:
                for pin_group in cell_group.subgroups_with_name('pin'):
                    pin = pin_group.identifier
                    for timing_group in pin_group.subgroups_with_name('timing'):
                        related_pin = timing_group.attributes['related_pin'].value
                        fig = plots.plot_delay_surfaces(list(timing_group.groups.values()),
                                                        title=f'Cell delays ({related_pin} to {pin})')
                        # FIXME: let user decide whether to show or save
                        fig_path = self.settings.plots_dir / cell.name
                        fig_path.mkdir(parents=True, exist_ok=True)
                        fig.savefig(fig_path / f'{related_pin} to {pin} delay.png') # FIXME: filetype should be configurable
                        plt.close()
        return self.library.to_liberty(precision=6)


class CharacterizationSettings:
    """Container for characterization settings"""
    def __init__(self, **kwargs):
        """Create a new CharacterizationSettings instance"""
        # Behavioral settings
        self.jobs = None if kwargs.pop('multithreaded', True) else 1
        self.results_dir = Path(kwargs.pop('results_dir', 'results'))
        self.plots_dir = self.results_dir / 'plots'
        self.debug = kwargs.pop('debug', False)
        self.debug_dir = Path(kwargs.pop('debug_dir', 'debug'))
        self.quiet = kwargs.pop('quiet', False)
        self.cell_defaults = kwargs.get('cell_defaults', {})
        self.omit_on_failure = kwargs.get('omit_on_failure', False)

        # Simulation procedures
        self.simulation = SimulationSettings(**kwargs.get('simulation', {}))

        # Units for simulation and results
        self.units = UnitsSettings(**kwargs.get('units', {}))

        # Library-wide named voltages
        nodes = kwargs.pop('named_nodes', {})
        self.primary_power = NamedNode(**nodes.get('primary_power', {'name':'VDD', 'voltage': 3.3}))
        self.primary_ground = NamedNode(**nodes.get('primary_ground', {'name':'VSS', 'voltage': 0}))
        self.pwell = NamedNode(**nodes.get('pwell', {'name':'VPW', 'voltage': 0}))
        self.nwell = NamedNode(**nodes.get('nwell', {'name':'VNW', 'voltage': 3.3}))

        # Logic thresholds
        self.logic_thresholds = LogicThresholds(**kwargs.get('logic_thresholds', {}))

        # Operating conditions
        self.temperature = kwargs.get('temperature', 25)

    @property
    def named_nodes(self):
        """Convenience accessor returning a tuple of all named nodes"""
        return (self.primary_power, self.primary_ground, self.nwell, self.pwell)

    def liberty_attrs_as_dict(self):
        """Return a dict of library-wide settings that should be written to the liberty file."""
        spice_unit = lambda unit: f'1{unit.prefixed_unit.str_spice()}'
        return {
            'nom_voltage': self.primary_power.voltage,
            'nom_temperature': self.temperature,
            'time_unit': spice_unit(self.units.time),
            'voltage_unit': spice_unit(self.units.voltage),
            'current_unit': spice_unit(self.units.current),
            'pulling_resistance_unit': spice_unit(self.units.current),
            'leakage_power_unit': spice_unit(self.units.power),
            'capacitive_load_unit': [1, self.units.capacitance.prefixed_unit.str_spice()],
            'slew_upper_threshold_pct_rise': self.logic_thresholds.high,
            'slew_lower_threshold_pct_rise': self.logic_thresholds.low,
            'slew_upper_threshold_pct_fall': self.logic_thresholds.high,
            'slew_lower_threshold_pct_fall': self.logic_thresholds.low,
            'input_threshold_pct_rise': self.logic_thresholds.rising,
            'input_threshold_pct_fall': self.logic_thresholds.falling,
            'output_threshold_pct_rise': self.logic_thresholds.rising,
            'output_threshold_pct_fall': self.logic_thresholds.falling,
        }

class SimulationSettings:
    """Container for simulation backend and procedures"""
    def __init__(self, **kwargs):
        self.backend = kwargs.get('backend', 'ngspice-shared')
        self.input_capacitance = registered_procedures[
            kwargs.get('input_capacitance_procedure', 'ac_sweep')
        ]
        self.combinational_delay = registered_procedures[
            kwargs.get('combinational_delay_procedure', 'combinational_worst_case')
        ]
        self.sequential_delay = registered_procedures[
            kwargs.get('sequential_delay_procedure', 'sequential_worst_case')
        ]
        self.metastability_constraint = registered_procedures[
            kwargs.get('setup_hold_constraint_procedure', 'measure_setup_hold_from_contour')
        ]
        self.recovery_constraint = registered_procedures[
            kwargs.get('recovery_constraint_procedure', 'recovery_constraint')
        ]
        self.removal_constraint = registered_procedures[
            kwargs.get('removal_constraint_procedure', 'removal_constraint')
        ]
        self.min_pulse_width_constraint = registered_procedures[
            kwargs.get('min_pulse_width_constraint_procedure', 'min_pulse_width_constraint')
        ]

class LogicThresholds:
    """Container for logic_thresholds settings"""
    def __init__(self, **kwargs):
        self.low = kwargs.get('low', 0.2)
        self.high = kwargs.get('high', 0.8)
        self.rising = kwargs.get('rising', 0.5)
        self.falling = kwargs.get('falling', 0.5)

class NamedNode:
    """Binds supply node names to voltages"""
    def __init__(self, name, voltage = 0):
        self.name = name
        self.voltage = voltage

    def __str__(self) -> str:
        return f'Name: {self.name}\nVoltage: {self.voltage}'

    def __repr__(self) -> str:
        return f'NamedNode({self.name}, {self.voltage})'

    @property
    def subscript(self) -> str:
        """Return the 'subscript' portion of the voltage name e.g. Vdd -> dd"""
        return self.name[1:] if self.name.lower().startswith('v') else self.name
