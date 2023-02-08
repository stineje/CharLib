import re
from pathlib import Path

from characterizer.HarnessSettings import HarnessSettings

RECOGNIZED_LOGIC = [
    'INV',
    'BUF',
    'AND2',  'AND3',  'AND4',
    'OR2',   'OR3',   'OR4',
    'NAND2', 'NAND3', 'NAND4',
    'NOR2',  'NOR3',  'NOR4',
    'AO21',  'AO22',
    'OA21',  'OA22',
    'AOI21', 'AOI22',
    'OAI21', 'OAI22',
    'XOR2',
    'XNOR2',
    'SEL2',
    #'HA',
    #'FA',
    'DFF_PCPU',
    'DFF_PCNU',
    'DFF_NCPU',
    'DFF_NCNU',
    'DFF_PCPU_NR',
    'DFF_PCPU_NRNS',
]
 
class LogicCell:
    def __init__ (self, name: str, logic: str, in_ports: list, out_ports: list, function: str, area: float = 0):
        self.name = name            # cell name
        self.logic = logic          # logic implemented by this cell
        self.in_ports = in_ports    # input pin names
        self.out_ports = out_ports  # output pin names
        self.functions = function   # cell function

        # Documentation
        self.area = area        # cell area

        # Characterization settings
        self._netlist = None    # cell netlist
        self._definition = None # cell definition (from netlist)
        self._instance = None   # TODO: figure out what this represents, and briefly document here
        self._in_slopes = []    # input pin slopes
        self._out_loads = []    # output pin loads
        self.sim_timestep = 0   # simulation timestep

        # From characterization results
        self.harnesses = []     # list of harnessSettings
        self.cins = []          # input pin capacitances
        self.leakage_power = [] # cell leakage power

        # Behavioral settings
        self._is_exported = False   # whether the cell has been exported

    def __repr__(self):
        # TODO
        return self.name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if value is not None and len(value) > 0:
            self._name = str(value)
        else:
            raise ValueError(f'Invalid value for cell name: {value}')

    @property
    def logic(self) -> str:
        return self._logic
    
    @logic.setter
    def logic(self, value: str):
        if value is not None:
            if value in RECOGNIZED_LOGIC:
                self._logic = str(value)
            else:
                raise ValueError(f'Unrecognized logic: {value}')
        else:
            raise ValueError(f'Invalid value for cell logic: {value}')

    @property
    def in_ports(self) -> list:
        return self._in_ports

    @in_ports.setter
    def in_ports(self, value):
        if value is not None:
            if isinstance(value, str):
                # Should be in the format "A B C"
                # TODO: add parsing for comma separated as well
                self._in_ports = value.split()
            elif isinstance(value, list):
                self._in_ports = value
            else:
                raise TypeError(f'Invalid type for in_ports: {type(value)}')
        else:
            raise ValueError(f'Invalid value for in_ports: {value}')

    @property
    def out_ports(self) -> list:
        return self._out_ports

    @out_ports.setter
    def out_ports(self, value):
        if value is not None:
            if isinstance(value, str):
                # Should be in the format "Y Z"
                # TODO: add parsing for comma separated as well
                self._out_ports = value.split()
            elif isinstance(value, list):
                self._out_ports = value
            else:
                raise TypeError(f'Invalid type for out_ports: {type(value)}')
        else:
            raise ValueError(f'Invalid value for out_ports: {value}')

    @property
    def functions(self) -> list:
        return self._functions

    @functions.setter
    def functions(self, value):
        if value is not None:
            if isinstance(value, list):
                self._functions = value
            elif isinstance(value, str) and '=' in value:
                # Should be in the format "Y=stuff"
                self._functions = value.split('=')[1:] # Discard lefthand side of equation
            else:
                raise TypeError(f'Invalid type for cell functions: {type(value)}')
        else:
            raise ValueError(f'Invalid value for cell functions: {value}')

    @property
    def area(self) -> float:
        return self._area

    @area.setter
    def area(self, value: float):
        if value is not None:
            self._area = float(value)
        else:
            raise ValueError(f'Invalid value for cell area: {value}')

    @property
    def netlist(self) -> str:
        return self._netlist

    @netlist.setter
    def netlist(self, value):
        if value is not None:
            if isinstance(value, Path):
                if not value.is_file():
                    raise ValueError(f'Invalid value for netlist: {value} is not a file')
                self._netlist = value
            elif isinstance(value, str):
                if not Path(value).is_file():
                    raise ValueError(f'Invalid value for netlist: {value} is not a file')
                self._netlist = Path(value)
            else:
                raise TypeError(f'Invalid type for netlist: {type(value)}')
            # netlist is now set - update definition
            with open(self.netlist, 'r') as netfile:
                for line in netfile:
                    if self.name.lower() in line.lower() and '.subckt' in line.lower():
                        self.definition = line
                netfile.close()
            if self.definition is None:
                raise ValueError(f'No cell definition found in netlist {value}')
        else:
            raise ValueError(f'Invalid value for netlist: {value}')

    @property
    def definition(self) -> str:
        return self._definition

    @definition.setter
    def definition(self, value: str):
        if value is not None:
            if self.name.lower() not in value.lower():
                raise ValueError(f'Cell name not found in cell definition: {value}')
            elif '.subckt' not in value.lower():
                raise ValueError(f'".subckt" not found in cell definition: {value}')
            else:
                self._definition = value
            # definition is now set - update instance
            circuit_call = re.sub('\$.*$', '', value).split()[1:]   # Delete .subckt
            circuit_call.append(circuit_call.pop(0))                # Move circuit name to last element
            circuit_call.insert(0,'XDUT')                           # Insert instance name
            self.instance = ' '.join(circuit_call)
        else:
            raise ValueError(f'Invalid value for cell definiton: {value}')

    @property
    def instance(self) -> str:
        return self._instance

    @instance.setter
    def instance(self, value: str):
        if value is not None:
            self._instance = value
        else:
            raise ValueError(f'Invalid value for instance: {value}')

    @property
    def in_slopes(self) -> list:
        return self._in_slopes

    def add_in_slope(self, value: float):
        if value is not None:
            self._in_slopes.append(float(value))
        else:
            raise ValueError(f'Invalid value for input pin slope: {value}')

    @property
    def out_loads(self) -> list:
        return self._out_loads

    def add_out_load(self, value: float):
        if value is not None:
            self._out_loads.append(float(value))
        else:
            raise ValueError(f'Invalid value for output pin load: {value}')

    # TODO: def add_harness(self, port, )

    @property
    def is_exported(self) -> bool:
        return self._is_exported

    def set_exported(self):
        self._is_exported = True


    def add_model(self, line="tmp"):
        tmp_array = line.split()
        self.model = tmp_array[1] 

    def add_simulation_timestep(self, line="tmp"):
        tmp_array = line.split()
        ## if auto, amd slope is defined, use 1/10 of min slope
        if ((tmp_array[1] == 'auto') and (self.in_slopes[0] != None)):
            self.sim_timestep = float(self.in_slopes[0])/10 
            print ("auto set simulation timestep")
        else:
            self.sim_timestep = float(tmp_array[1])

    def set_inport_cap_pleak(self, index, harness):
        ## average leak power of all harness
        self.leakage_power += harness.pleak 

    ## calculate ave of cin for each inports
    ## cin is measured two times and stored into 
    ## neighborhood harness, so cin of (2n)th and 
    ## (2n+1)th harness are averaged out
    def set_cin_avg(self, targetLib, port="data"):
        tmp_cin = 0
        tmp_index = 0
        for targetHarness in self.harnesses[-1]:
            if((port.lower() == 'clock')or(port.lower() == 'clk')):
                tmp_cin += float(targetHarness.cclk)
                ## if this is (2n+1) then store averaged 
                ## cin into targetCell.cins
                if((tmp_index % 2) == 1):
                    self.cclks.append(str((tmp_cin / 2)/targetLib.units.capacitance.magnitude))
                    tmp_cin = 0
                tmp_index += 1
                #print("stored cins:"+str(tmp_index)+" for clk")
            elif((port.lower() == 'reset')or(port.lower() == 'rst')):
                tmp_cin += float(targetHarness.cin) # .cin stores rst cap. 
                ## if this is (2n+1) then store averaged 
                ## cin into targetCell.cins
                if((tmp_index % 2) == 1):
                    self.crsts.append(str((tmp_cin / 2)/targetLib.units.capacitance.magnitude))
                    tmp_cin = 0
                tmp_index += 1
                #print("stored cins:"+str(tmp_index)+" for rst")
            elif(port.lower() == 'set'):
                tmp_cin += float(targetHarness.cin) # .cin stores set cap.
                ## if this is (2n+1) then store averaged 
                ## cin into targetCell.cins
                if((tmp_index % 2) == 1):
                    self.csets.append(str((tmp_cin / 2)/targetLib.units.capacitance.magnitude))
                    tmp_cin = 0
                tmp_index += 1
                #print("stored cins:"+str(tmp_index)+" for set")
            else:	
                tmp_cin += float(targetHarness.cin) # else, .cin stores inport cap.
                ## if this is (2n+1) then store averaged 
                ## cin into targetCell.cins
                if((tmp_index % 2) == 1):
                    self.cins.append(str((tmp_cin / 2)/targetLib.units.capacitance.magnitude))
                    tmp_cin = 0
                tmp_index += 1
                #print("stored cins:"+str(tmp_index)+" for data")
            #print("stored cins:"+str(tmp_index))

class SequentialCell(LogicCell):
    def __init__(self, name: str, logic: str, in_ports: list, out_ports: list, clock_pin: str, set_pin: str, reset_pin: str, flops: str, function: str, area: float = 0):
        super().__init__(name, logic, in_ports, out_ports, function, area)
        self.clock = clock_pin  # clock pin name
        self.set = set_pin      # set pin name
        self.reset = reset_pin  # reset pin name
        self._flops = flops     # registers
        self._clock_slope = 0   # input pin clock slope

        # Characterization settings
        self._sim_setup_lowest = 0   ## fastest simulation edge (pos. val.) 
        self._sim_setup_highest = 0  ## lowest simulation edge (pos. val.) 
        self._sim_setup_timestep = 0 ## timestep for setup search (pos. val.) 
        self._sim_hold_lowest = 0    ## fastest simulation edge (pos. val.) 
        self._sim_hold_highest = 0   ## lowest simulation edge (pos. val.) 
        self._sim_hold_timestep = 0  ## timestep for hold search (pos. val.) 

        # From characterization results
        self.cclks = []     # clock pin capacitance
        self.csets = []     # set pin capacitance
        self.crsts = []     # reset pin capacitance

    @property
    def clock_slope(self) -> float:
        return self._clock_slope

    @clock_slope.setter
    def clock_slope(self, value):
        if value is not None:
            if isinstance(value, (int, float)):
                if value > 0:
                    self._clock_slope = float(value)
                else:
                    raise ValueError('Clock slope must be greater than zero')
            elif value == 'auto':
                if not self.in_slopes:
                    raise ValueError('Cannot use auto clock slope unless in_slopes is set first!')
                self._clock_slope = float(self._in_slopes[0])
            else:
                raise TypeError(f'Invalid type for clock slope: {type(value)}')
        else:
            raise ValueError(f'Invalid value for clock slope: {value}')

    @property
    def sim_setup_lowest(self) -> float:
        return self._sim_setup_lowest

    @sim_setup_lowest.setter
    def sim_setup_lowest(self, value):
        if value is not None:
            if isinstance(value, (int, float)):
                if value > 0:
                    self._sim_setup_lowest = float(value)
                else:
                    raise ValueError('Value must be greater than zero')
            elif value == 'auto':
                if not self.in_slopes:
                    raise ValueError('Cannot use auto for sim_setup_lowest unless in_slopes is set first!')
                # Use -10 * max input pin slope
                self._sim_setup_lowest = float(self._in_slopes[-1]) * -10
            else:
                raise TypeError(f'Invalid type for sim_setup_lowest: {type(value)}')
        else:
            raise ValueError(f'Invalid value for sim_setup_lowest: {value}')
            
    ## this defines highest limit of setup edge
    def add_simulation_setup_highest(self, line="tmp"):
        tmp_array = line.split()
        ## if auto, amd slope is defined, use 10x of max slope 
        if ((tmp_array[1] == 'auto') and (self.in_slopes[-1] != None)):
            self.sim_setup_highest = float(self.in_slopes[-1]) * 10 
            print ("auto set setup simulation time highest limit")
        else:
            self.sim_setup_highest = float(tmp_array[1])
            
    def add_simulation_setup_timestep(self, line="tmp"):
        tmp_array = line.split()
        ## if auto, amd slope is defined, use 1/10x min slope
        if ((tmp_array[1] == 'auto') and (self.in_slopes[0] != None)):
            self.sim_setup_timestep = float(self.in_slopes[0])/10
            print ("auto set setup simulation timestep")
        else:
            self.sim_setup_timestep = float(tmp_array[1])
            
    ## this defines lowest limit of hold edge
    def add_simulation_hold_lowest(self, line="tmp"):
        tmp_array = line.split()
        ## if auto, amd slope is defined, use very small val. 
        #remove# if hold is less than zero, pwl time point does not be incremental
        #remove# and simulation failed
        if ((tmp_array[1] == 'auto') and (self.in_slopes[-1] != None)):
            #self.sim_hold_lowest = float(self.in_slopes[-1]) * -5 
            self.sim_hold_lowest = float(self.in_slopes[-1]) * -10 
            #self.sim_hold_lowest = float(self.in_slopes[-1]) * 0.001 
            print ("auto set hold simulation time lowest limit")
        else:
            self.sim_hold_lowest = float(tmp_array[1])
            
    ## this defines highest limit of hold edge
    def add_simulation_hold_highest(self, line="tmp"):
        tmp_array = line.split()
        ## if auto, amd slope is defined, use 5x of max slope 
        ## value should be smaller than "tmp_max_val_loop" in holdSearchFlop
        if ((tmp_array[1] == 'auto') and (self.in_slopes[-1] != None)):
            #self.sim_hold_highest = float(self.in_slopes[-1]) * 5 
            self.sim_hold_highest = float(self.in_slopes[-1]) * 10 
            print ("auto set hold simulation time highest limit")
        else:
            self.sim_hold_highest = float(tmp_array[1])
            
    def add_simulation_hold_timestep(self, line="tmp"):
        tmp_array = line.split()
        ## if auto, amd slope is defined, use 1/10x min slope
        if ((tmp_array[1] == 'auto') and (self.in_slopes[0] != None)):
            self.sim_hold_timestep = float(self.in_slopes[0])/10 
            print ("auto set hold simulation timestep")
        else:
            self.sim_hold_timestep = float(tmp_array[1])
