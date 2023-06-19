from pathlib import Path
from liberty.UnitsSettings import UnitsSettings

class NamedNode:
    def __init__(self, name, voltage = 0):
        # TODO: Use units for voltages
        self.name = name
        self.voltage = voltage

    def __str__(self) -> str:
        return f'Name: {self.name}\nVoltage: {self.voltage}'

    def __repr__(self) -> str:
        return f'NamedNode({self.name}, {self.voltage})'

def str_to_bool(value: str) -> bool:
    if value.lower() in ['true', 't', '1', 'yes']:
        return True
    elif value.lower() in ['false', 'f', '0', 'no']:
        return False
    else:
        raise ValueError(f'Unable to convert "{value}" to bool.')


class LibrarySettings:
    def __init__(self, **kwargs):
        # Behavioral settings
        self._lib_name = kwargs.get('lib_name', 'unnamed_lib')
        self._dotlib_name = kwargs.get('dotlib_name')
        self._verilog_name = kwargs.get('verilog_name')
        self._cell_name_suffix = kwargs.get('cell_name_suffix', '')
        self._cell_name_prefix = kwargs.get('cell_name_prefix', '')
        self._work_dir = Path(kwargs.get('work_dir', 'work'))
        self._results_dir = Path(kwargs.get('results_dir', 'results'))
        self._run_sim = kwargs.get('run_simulation', True)
        self._use_multithreaded = kwargs.get('multithreaded', True)
        self._is_exported = False

        # Simulation Settings
        self._simulator = kwargs.get('simulator', 'ngspice-subprocess')
        self.units = UnitsSettings(**kwargs.get('units', {}))

        named_nodes = kwargs.get('named_nodes', {})
        self.vdd = NamedNode(**named_nodes.get('vdd', {'name':'VDD'}))
        self.vss = NamedNode(**named_nodes.get('vss', {'name':'VSS'}))
        self.pwell = NamedNode(**named_nodes.get('pwell', {'name':'VPW'}))
        self.nwell = NamedNode(**named_nodes.get('nwell', {'name':'VNW'}))

        logic_thresholds = kwargs.get('logic_thresholds', {})
        self._logic_threshold_low = logic_thresholds.get('low', 0.2)
        self._logic_threshold_high = logic_thresholds.get('high', 0.8)
        self._logic_high_to_low_threshold = logic_thresholds.get('high_to_low', 0.5)
        self._logic_low_to_high_threshold = logic_thresholds.get('low_to_high', 0.5)

        energy_measurement = kwargs.get('energy_measurement', {})
        self._energy_meas_low_threshold = energy_measurement.get('low_threshold', 0.01)
        self._energy_meas_high_threshold = energy_measurement.get('high_threshold', 0.99)
        self._energy_meas_time_extent = energy_measurement.get('time_extent', 10)

        self._process = kwargs.get('process')
        self._temperature = kwargs.get('temperature', 25)
        self._operating_conditions = kwargs.get('operating_conditions')
        self._delay_model = kwargs.get('delay_model', 'table_lookup')
        self.cell_defaults = kwargs.get('cell_defaults', {})

        # TODO: Deprecate these settings
        self._suppress_msg = False
        self._suppress_sim_msg = False
        self._suppress_debug_msg = False

    def __str__(self) -> str:
        lines = []
        lines.append(f'Library name:         {self.lib_name}')
        lines.append(f'.lib name:            {self.dotlib_name}')
        lines.append(f'.v name:              {self.verilog_name}')
        lines.append(f'Cell suffix:          {self.cell_name_suffix}')
        lines.append(f'Cell prefix:          {self.cell_name_prefix}')
        lines.append(f'Units: ')
        for line in str(self.units).split('\n'):
            lines.append(f'    {line}')
        lines.append(f'Simulator:            {str(self.simulator)}')
        lines.append(f'Work directory:       {str(self.work_dir)}')
        lines.append(f'Process:              {self.process}')
        lines.append(f'Temperature:          {str(self.temperature)}')
        lines.append(f'vdd:')
        for line in str(self.vdd).split('\n'):
            line = line if not 'Voltage: ' in line else f'{line} {str(self.units.voltage)}'
            lines.append(line)
        for line in str(self.vss).split('\n'):
            line = line if not 'Voltage: ' in line else f'{line} {str(self.units.voltage)}'
            lines.append(line)
        for line in str(self.pwell).split('\n'):
            line = line if not 'Voltage: ' in line else f'{line} {str(self.units.voltage)}'
            lines.append(line)
        for line in str(self.nwell).split('\n'):
            line = line if not 'Voltage: ' in line else f'{line} {str(self.units.voltage)}'
            lines.append(line)
        lines.append(f'Logic thresholds:')
        lines.append(f'    Low:              {str(self.logic_threshold_low_voltage())} {str(self.units.voltage)}')
        lines.append(f'    High:             {str(self.logic_threshold_high_voltage())} {str(self.units.voltage)}')
        lines.append(f'    High to low:      {str(self.logic_high_to_low_threshold_voltage())} {str(self.units.voltage)}')
        lines.append(f'    Low to high:      {str(self.logic_low_to_high_threshold_voltage())} {str(self.units.voltage)}')
        lines.append(f'Energy measurement thresholds:')
        lines.append(f'    Low:              {str(self.energy_meas_low_threshold_voltage())} {str(self.units.voltage)}')
        lines.append(f'    High:             {str(self.energy_meas_high_threshold_voltage())} {str(self.units.voltage)}')
        lines.append(f'Operating conditions: {self.operating_conditions}')
        lines.append(f'Delay model:          {self.delay_model}')
        return '\n'.join(lines)

    @property
    def work_dir(self) -> Path:
        return self._work_dir

    @work_dir.setter
    def work_dir(self, value):
        if value is not None:
            if isinstance(value, Path):
                self._work_dir = value 
            elif isinstance(value, str):
                self._work_dir = Path(value)
            else:
                raise TypeError(f'Invalid type for work_dir: {type(value)}')
        else:
            raise ValueError(f'Invalid value for work_dir: {value}')

    @property
    def simulator(self) -> Path:
        return self._simulator

    @simulator.setter
    def simulator(self, value):
        if value is not None:
            if isinstance(value, str) and any([backend in value for backend in ['ngspice', 'xyce']]):
                self._simulator = value
            else:
                raise TypeError(f'Invalid type for simulator: {type(value)}')
        else:
            raise ValueError(f'Invalid value for simulator: {value}')

    @property
    def lib_name(self) -> str:
        return self._lib_name

    @lib_name.setter
    def lib_name(self, value: str):
        if value is not None and len(value) > 0:
            self._lib_name = value
        else:
            raise ValueError(f'Invalid value for lib_name: {value}')

    @property
    def dotlib_name(self) -> str:
        if self._dotlib_name is None:
            return self.lib_name + '.lib'
        else:
            return self._dotlib_name

    @dotlib_name.setter
    def dotlib_name(self, value: str):
        if value is not None and len(value) > 0:
            if not str(value).endswith('.lib'):
                raise ValueError(f'Dotlib name must end in .lib!')
            self._dotlib_name = str(value)
        else:
            raise ValueError(f'Invalid value for dotlib_name: {value}')

    @property
    def verilog_name(self) -> str:
        if self._verilog_name is None:
            return self.lib_name + '.v'
        else:
            return self._verilog_name

    @verilog_name.setter
    def verilog_name(self, value: str):
        if value is not None and len(value) > 0:
            if not str(value).endswith('.v'):
                raise ValueError(f'Verilog name must end in .v!')
            self._verilog_name = str(value)
        else:
            raise ValueError(f'Invalid value for verilog_name: {value}')

    @property
    def cell_name_suffix(self) -> str:
        return self._cell_name_suffix

    @cell_name_suffix.setter
    def cell_name_suffix(self, value: str):
        if value is not None and len(value) > 0:
            self._cell_name_suffix = value
        else:
            raise ValueError(f'Invalid value for cell_name_suffix: {value}')

    @property
    def cell_name_prefix(self) -> str:
        return self._cell_name_prefix

    @cell_name_prefix.setter
    def cell_name_prefix(self, value: str):
        if value is not None and len(value) > 0:
            self._cell_name_prefix = value
        else:
            raise ValueError(f'Invalid value for cell_name_suffix: {value}')

    @property
    def process(self) -> str:
        return self._process

    @process.setter
    def process(self, value: str):
        if value is not None and len(value) > 0:
            self._process = value
        else:
            raise ValueError(f'Invalid value for process: {value}')

    @property
    def temperature(self) -> float:
        return self._temperature

    @temperature.setter
    def temperature(self, value: float):
        if value is not None:
            self._temperature = value
        else:
            raise ValueError(f'Invalid value for temperature: {value}')

    @property
    def logic_threshold_high(self) -> float:
        return self._logic_threshold_high

    @logic_threshold_high.setter
    def logic_threshold_high(self, value: float):
        if value is not None and 0 < value < 1:
            self._logic_threshold_high = value
        else:
            raise ValueError(f'Invalid value for logic_threshold_high: {value}')

    def logic_threshold_high_voltage(self) -> float:
        return self.logic_threshold_high * self.vdd.voltage

    @property
    def logic_threshold_low(self) -> float:
        return self._logic_threshold_low

    @logic_threshold_low.setter
    def logic_threshold_low(self, value: float):
        if value is not None and 0 < value < 1:
            self._logic_threshold_low = value
        else:
            raise ValueError(f'Invalid value for logic_threshold_high: {value}')

    def logic_threshold_low_voltage(self) -> float:
        return self.logic_threshold_low * self.vdd.voltage

    @property
    def logic_high_to_low_threshold(self) -> float:
        return self._logic_high_to_low_threshold

    @logic_high_to_low_threshold.setter
    def logic_high_to_low_threshold(self, value: float):
        if value is not None and 0 < value < 1:
            self._logic_high_to_low_threshold = value
        else:
            raise ValueError(f'Invalid value for logic_high_to_low_threshold: {value}')

    def logic_high_to_low_threshold_voltage(self) -> float:
        return self.logic_high_to_low_threshold * self.vdd.voltage

    @property
    def logic_low_to_high_threshold(self) -> float:
        return self._logic_low_to_high_threshold

    @logic_low_to_high_threshold.setter
    def logic_low_to_high_threshold(self, value: float):
        if value is not None and 0 < value < 1:
            self._logic_low_to_high_threshold = value
        else:
            raise ValueError(f'Invalid value for logic_low_to_high_threshold: {value}')

    def logic_low_to_high_threshold_voltage(self) -> float:
        return self.logic_low_to_high_threshold * self.vdd.voltage

    @property
    def energy_meas_low_threshold(self) -> float:
        return self._energy_meas_low_threshold

    @energy_meas_low_threshold.setter
    def energy_meas_low_threshold(self, value: float):
        if value is not None and 0 < value < 1:
            self._energy_meas_low_threshold = value
        else:
            raise ValueError(f'Invalid value for energy_meas_low_threshold: {value}')

    def energy_meas_low_threshold_voltage(self) -> float:
        return self.energy_meas_low_threshold * self.vdd.voltage

    @property
    def energy_meas_high_threshold(self) -> float:
        return self._energy_meas_high_threshold
    
    @energy_meas_high_threshold.setter
    def energy_meas_high_threshold(self, value: float):
        if value is not None and 0 < value < 1:
            self._energy_meas_high_threshold = value
        else:
            raise ValueError(f'Invalid value for energy_meas_high_threshold: {value}')

    def energy_meas_high_threshold_voltage(self) -> float:
        return self.energy_meas_high_threshold * self.vdd.voltage

    @property
    def energy_meas_time_extent(self) -> float:
        return self._energy_meas_time_extent

    @energy_meas_time_extent.setter
    def energy_meas_time_extent(self, value: float):
        if value is not None and value > 0:
            self._energy_meas_time_extent = value
        else:
            raise ValueError(f'Invalid value for energy_meas_time_extent: {value}')

    @property
    def operating_conditions(self) -> str:
        return self._operating_conditions

    @operating_conditions.setter
    def operating_conditions(self, value: str):
        if value is not None and len(value) > 0:
            self._operating_conditions = value
        else:
            raise ValueError(f'Invalid value for operating_conditions: {value}')

    @property
    def delay_model(self) -> str:
        return self._delay_model
    
    @delay_model.setter
    def delay_model(self, value: str):
        if value is not None and len(value) > 0:
            self._delay_model = value
        else:
            raise ValueError(f'Invalid value for delay_model: {value}')

    @property
    def run_sim(self) -> bool:
        return self._run_sim

    @run_sim.setter
    def run_sim(self, value):
        if value is not None:
            if isinstance(value, str):
                self._run_sim = str_to_bool(value)
            elif isinstance(value, bool):
                self._run_sim = value
            else:
                raise TypeError(f'Invalid type for run_sim: {type(value)}')
        else:
            raise ValueError(f'Invalid value for run_sim: {value}')

    @property
    def use_multithreaded(self) -> bool:
        return self._use_multithreaded

    @use_multithreaded.setter
    def use_multithreaded(self, value):
        if value is not None:
            if isinstance(value, str):
                self._use_multithreaded = str_to_bool(value)
            elif isinstance(value, bool):
                self._use_multithreaded = value
            else:
                raise TypeError(f'Invalid type for use_multithreaded: {type(value)}')
        else:
            raise ValueError(f'Invalid value for use_multithreaded: {value}')
    
    @property
    def is_exported(self) -> bool:
        return self._is_exported

    def set_exported(self):
        self._is_exported = True

    @property
    def suppress_message(self) -> bool:
        return self._suppress_msg
    
    @suppress_message.setter
    def suppress_message(self, value: str):
        self._suppress_msg = str_to_bool(value)

    @property
    def suppress_sim_message(self) -> bool:
        return self._suppress_sim_msg

    @suppress_sim_message.setter
    def suppress_sim_message(self, value: str):
        self._suppress_sim_msg = str_to_bool(value)
    
    @property
    def suppress_debug_message(self) -> bool:
        return self._suppress_debug_msg

    @suppress_debug_message.setter
    def suppress_debug_message(self, value: str):
        self._suppress_debug_msg = str_to_bool(value)
