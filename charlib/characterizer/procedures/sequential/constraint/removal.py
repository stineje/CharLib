import PySpice

from charlib.characterizer import utils, plots
from charlib.characterizer.cell import Port
from charlib.characterizer.procedures import register, ProcedureFailedException
from charlib.liberty import liberty

@register
def removal_constraint(cell, config, settings):
    """Find the mimimum time a control pin must remain active after the trigger.

    This is analagous to hold time for an asynchronous control pin.

    For example, for a rising-edge DFF with an asynchronous reset, removal time is the minimum time
    that the reset signal must remain active after the rising clock edge in order to reset the
    device state."""
    for variation in config.variations('clock_slews', 'data_slews'):
        for path in cell.paths():
            yield (find_min_removal_time_for_path, cell, config, settings, variation, path)

def find_min_removal_time_for_path(cell, config, settings, variation, path):
    """Find the minimum time a control pin must remain active in order to affect device state.

    This method tests all nonmasking conditions for the path through the cell and finds the minumum
    removal constraint for each. Nonmasking conditions are annotated in the 'when' and 'sdf_cond'
    fields of the timing tables on the returned liberty cell groups.

    Removal timing tables are indexed by the transition time of a related trigger pin (usually a
    clock) and the transition time of the constrained control pin (usually set or reset)."""
    return cell.liberty # TODO
