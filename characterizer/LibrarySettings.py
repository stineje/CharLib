from characterizer.myFunc import my_exit
from characterizer.UnitsSettings import UnitsSettings

class LibrarySettings:
	def __init__ (self):
		# Key Library settings
		self._lib_name = None
		self._dotlib_name = None
		self._verilog_name = None
		self._cell_name_suffix = None
		self._cell_name_prefix = None
		self.units = UnitsSettings() # This is unprotected for easy access to members
		
		# Behavioral settings
		self._is_export = 0
		self._delay_model = "table_lookup"
		self._runsim = True
		self._suppress_msg = False
		self._suppress_sim_msg = False
		self._suppress_debug_msg = False

	@property
	def lib_name(self):
		return self._lib_name

	@lib_name.setter
	def lib_name(self, value: str):
		if value is not None and len(value) < 0:
			self._lib_name = value

	@property
	def dotlib_name(self):
		return self._dotlib_name

	@dotlib_name.setter
	def dotlib_name(self, value: str):
		if value is not None and len(value) < 0:
			self._dotlib_name = value

	@property
	def verilog_name(self):
		return self._verilog_name

	@verilog_name.setter
	def verilog_name(self, value: str):
		if value is not None and len(value) < 0:
			self._verilog_name = value

	@property
	def cell_name_suffix(self):
		return self._cell_name_suffix

	@cell_name_suffix.setter
	def cell_name_suffix(self, value: str):
		if value is not None and len(value) < 0:
			self._cell_name_suffix = value

	@property
	def cell_name_prefix(self):
		return self._cell_name_prefix

	@cell_name_prefix.setter
	def cell_name_prefix(self, value: str):
		if value is not None and len(value) < 0:
			self._cell_name_prefix = value


	def set_vdd_name(self, line="tmp"):
		tmp_array = line.split()
		self.vdd_name = tmp_array[1] 
		#print(tmp_array[1])

	def set_vss_name(self, line="tmp"):
		tmp_array = line.split()
		self.vss_name = tmp_array[1] 
		#print(tmp_array[1])

	def set_pwell_name(self, line="tmp"):
		tmp_array = line.split()
		self.pwell_name = tmp_array[1] 
		#print(tmp_array[1])

	def set_nwell_name(self, line="tmp"):
		tmp_array = line.split()
		self.nwell_name = tmp_array[1] 
		#print(tmp_array[1])

	def set_process(self, line="tmp"):
		tmp_array = line.split()
		self.process = tmp_array[1] 
		#print(tmp_array[1])

	def set_temperature(self, line="tmp"):
		tmp_array = line.split()
		self.temperature = float(tmp_array[1]) 
		#print(tmp_array[1])

	def set_vdd_voltage(self, line="tmp"):
		tmp_array = line.split()
		self.vdd_voltage = float(tmp_array[1]) 
		#print(self.vdd_voltage)

	def set_vss_voltage(self, line="tmp"):
		tmp_array = line.split()
		self.vss_voltage = float(tmp_array[1]) 
		#print(tmp_array[1])

	def set_nwell_voltage(self, line="tmp"):
		tmp_array = line.split()
		self.nwell_voltage = float(tmp_array[1]) 
		#print(tmp_array[1])

	def set_pwell_voltage(self, line="tmp"):
		tmp_array = line.split()
		self.pwell_voltage = float(tmp_array[1]) 
		#print(tmp_array[1])

	def set_logic_threshold_high(self, line="tmp"):
		tmp_array = line.split()
		self.logic_threshold_high = float(tmp_array[1])
		self.logic_threshold_high_voltage = float(tmp_array[1])*self.vdd_voltage*self.voltage_mag
		#print(tmp_array[1])

	def set_logic_threshold_low(self, line="tmp"):
		tmp_array = line.split()
		self.logic_threshold_low = float(tmp_array[1])
		self.logic_threshold_low_voltage = float(tmp_array[1])*self.vdd_voltage*self.voltage_mag
		#print(tmp_array[1])

	def set_logic_high_to_low_threshold(self, line="tmp"):
		tmp_array = line.split()
		self.logic_high_to_low_threshold = float(tmp_array[1])
		self.logic_high_to_low_threshold_voltage = float(tmp_array[1])*self.vdd_voltage*self.voltage_mag
		#print(tmp_array[1])

	def set_logic_low_to_high_threshold(self, line="tmp"):
		tmp_array = line.split()
		self.logic_low_to_high_threshold = float(tmp_array[1])
		self.logic_low_to_high_threshold_voltage = float(tmp_array[1])*self.vdd_voltage*self.voltage_mag
		#print(tmp_array[1])

	def set_work_dir(self, line="tmp"):
		tmp_array = line.split()
		self.work_dir = tmp_array[1] 
		#print(tmp_array[1])

	def set_simulator(self, line="tmp"):
		tmp_array = line.split()
		self.simulator = tmp_array[1] 
		#print(tmp_array[1])

	def set_energy_meas_low_threshold(self, line="tmp"):
		tmp_array = line.split()
		self.energy_meas_low_threshold = float(tmp_array[1]) 
		self.energy_meas_low_threshold_voltage = float(tmp_array[1]) *self.vdd_voltage*self.voltage_mag
		#print(tmp_array[1])

	def set_energy_meas_high_threshold(self, line="tmp"):
		tmp_array = line.split()
		self.energy_meas_high_threshold = float(tmp_array[1]) 
		self.energy_meas_high_threshold_voltage = float(tmp_array[1]) *self.vdd_voltage*self.voltage_mag
		#print(tmp_array[1])

	def set_energy_meas_time_extent(self, line="tmp"):
		tmp_array = line.split()
		self.energy_meas_time_extent = float(tmp_array[1])
		#print(tmp_array[1])
	
	def set_operating_conditions(self, line="tmp"):
		tmp_array = line.split()
		self.operating_conditions = tmp_array[1] 
		#print(tmp_array[1])
	
	def set_exported(self):
		self.is_export = 1 

	def set_run_sim(self, line="true"):
		tmp_array = line.split()
		self.runsim = tmp_array[1] 
		print(tmp_array[1])

	def set_mt_sim(self, line="true"):
		tmp_array = line.split()
		self.mtsim = tmp_array[1] 
		print(line)

	def set_suppress_message(self, line="false"):
		tmp_array = line.split()
		self.suppress_msg = tmp_array[1] 
		print(line)

	def set_suppress_sim_message(self, line="false"):
		tmp_array = line.split()
		self.suppress_sim_msg = tmp_array[1] 
		print(line)

	def set_suppress_debug_message(self, line="false"):
		tmp_array = line.split()
		self.suppress_debug_msg = tmp_array[1] 
		print(line)

	def print_error(self, message=""):
		print(message)
		my_exit()

	def print_msg(self, message=""):
		if not self.suppress_msg:
			print(message)
	
	def print_msg_sim(self, message=""):
		if (self.suppress_sim_msg.lower() == "false") or (self.suppress_sim_msg.lower() == "f"):
			print(message)
	
	def print_msg_dbg(self,  message=""):
		if (self.suppress_debug_msg.lower() == "false") or (self.supress_debug_msglower() == "f"):
			print(message)
