import PySpice

from charlib.characterizer import utils, plots
from charlib.characterizer.cell import Port
from charlib.characterizer.procedures import register, ProcedureFailedException
from charlib.liberty import liberty

@register
def recovery_constraint(cell, config, settings):
    """Find the minimum time a control pin must be active before the trigger.

    This is analagous to setup time for an asynchronous control pin.

    For example, for a rising-edge DFF with an asynchronous reset, recovery time is the minimum
    time the reset signal must be active before the rising clock edge in order to reset the device
    state."""
    for variation in config.variations('clock_slews', 'data_slews'):
        for path in cell.paths():
            yield (find_min_recovery_time_for_path, cell, config, settings, variation, path)

def find_min_recovery_time_for_path(cell, config, settings, variation, path):
    """Find the minimum time a control pin must be active in order to affect device state.

    This method tests all nonmasking conditions for the path through the cell and finds the minumum
    recovery constraint for each. Nonmasking conditions are annotated in the 'when' and 'sdf_cond'
    fields of the timing tables on the returned liberty cell groups.

    Recovery timing tables are indexed by the transition time of a related trigger pin (usually a
    clock) and the transition time of the constrained control pin (usually set or reset)."""
    return cell.liberty # TODO
