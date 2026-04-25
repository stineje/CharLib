import PySpice

from charlib.characterizer import utils, plots
from charlib.characterizer.cell import Port
from charlib.characterizer.procedures import register, ProcedureFailedException
from charlib.liberty import liberty

@register
def min_pulse_width_constraint(cell, config, settings):
    """Find the minimum pulse width required for the trigger to activate the device.

    This is analagous to the min_pulse_width property of a set, reset, enable, or clock pin.

    For example, for a rising-edge DFF with an asynchronous reset, the minimum pulse width is the
    minimum time the clock signal must be active before the rising edge in order to reset the
    device state."""
    for pin in cell.filter_pins(direction='input', trigger=Port.Trigger.EDGE):
        yield (find_min_pulse_width, cell, config, settings, pin)

def find_min_pulse_width(cell, config, settings, input_pin):
    """Find the minimum pulse width for input_pin across all combinations of test parameters.

    This method tests every test configuration variation and nonmasking condition to find the
    minimum pulse width for the target input_pin."""
    return cell.liberty # TODO
