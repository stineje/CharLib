import PySpice

from charlib.characterizer import utils, plots
from charlib.characterizer.procedures import register, ProcedureFailedException
from charlib.liberty import liberty

@register
def sequential_worst_case(cell, config, settings):
    """Measure worst-case sequential transient and propagation delays"""
    for variation in config.variations('data_slews', 'loads'):
        for path in cell.paths():
            yield (measure_delays_for_path, cell, config, settings, variation, path)

def measure_delays_for_path(cell, config, settings, variation, path, criterion=max):
    return cell.liberty # TODO
