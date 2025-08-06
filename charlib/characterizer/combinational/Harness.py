"""A Harness for combinational cells"""

import matplotlib.pyplot as plt

from PySpice.Unit import *

from charlib.characterizer.Harness import Harness
from charlib.liberty.cell import TimingData, TableTemplate

class CombinationalHarness (Harness):
    """A CombinationalHarness captures configuration for testing a combinational cell."""

    def __init__(self, target_cell, test_vector) -> None:
        """Create a new CombinationalHarness."""
        super().__init__(target_cell, test_vector)
        # Error if we don't have a target input port
        if not self.target_in_port:
            raise ValueError(f'Unable to parse target input port from test vector {test_vector}')

    def to_timingdata(self, time_unit) -> TimingData:
        """Convert results to liberty.TimingData objects"""
        slews = list(self.results.keys())
        loads = list(self.results[slews[0]].keys())
        delay_data = TimingData(self.target_in_port.pin.name)
        delay_template = TableTemplate(
            f'delay_template_{len(slews)}x{len(loads)}',
            ['input_net_transition', 'total_output_net_capacitance']
        )
        prop_delays = []
        tran_delays = []
        for slew in slews:
            for load in loads:
                result = self.results[slew][load]
                prop_delays.append(f'{(result["prop_in_out"] @ u_s).convert(time_unit).value:7f}')
                tran_delays.append(f'{(result["trans_out"] @ u_s).convert(time_unit).value:7f}')
        delay_data.add_table(f'cell_{self.out_direction}', delay_template, prop_delays, slews, loads)
        delay_data.add_table(f'{self.out_direction}_transition', delay_template, tran_delays, slews, loads)
        return delay_data
