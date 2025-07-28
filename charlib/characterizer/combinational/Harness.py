"""A Harness for combinational cells"""

import matplotlib.pyplot as plt

from charlib.characterizer.Harness import Harness

class CombinationalHarness (Harness):
    """A CombinationalHarness captures configuration for testing a combinational cell."""

    def __init__(self, target_cell, test_vector) -> None:
        """Create a new CombinationalHarness."""
        super().__init__(target_cell, test_vector)
        # Error if we don't have a target input port
        if not self._target_in_port:
            raise ValueError(f'Unable to parse target input port from test vector {test_vector}')

    def plot_energy(self, settings, slews, loads, cell_name):
        """Plot energy vs slew rate vs fanout"""
        # TODO: Consider moving this to Pin, as all the data is eventually stored there anyways
        figure = plt.figure()
        figure.suptitle(f'Cell {cell_name} | Arc: {self.arc_str()}')

        ax = figure.add_subplot(projection='3d')
        ax.set_proj_type('ortho')

        energy_data = []
        for slew in slews:
            energy_row = []
            for load in loads:
                energy = self._calc_internal_energy(slew, load, settings.energy_meas_high_threshold_voltage())
                energy_row.append(float(energy.convert(settings.units.energy.prefixed_unit).value))
            energy_data.append(energy_row)

        # Expand x and y vectors to 2d arrays
        x_data = np.repeat(np.expand_dims(slews, 1), len(loads), 1)
        y_data = np.swapaxes(np.repeat(np.expand_dims(loads, 1), len(slews), 1), 0, 1)

        # Plot energy data
        ax.plot_surface(x_data, y_data, np.asarray(energy_data), cmap='viridis', label='Energy')
        ax.set(xlabel=f'Slew Rate [{str(settings.units.time.prefixed_unit)}]',
               ylabel=f'Fanout [{str(settings.units.capacitance.prefixed_unit)}]',
               zlabel=f'Energy [{str(settings.units.energy.prefixed_unit)}]',
               title='Energy vs. Slew Rate vs. Fanout')
