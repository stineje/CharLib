import matplotlib.pyplot as plt
import numpy as np
from liberty.parser import parse_liberty
from pathlib import Path

def compare(benchmark, characterized): # FIXME: no longer works with recent rework
    """Compare prop delay and trans delay for each cell and make scatter plots"""
    charlib_rise_prop_data = []
    benchmark_rise_prop_data = []
    charlib_fall_prop_data = []
    benchmark_fall_prop_data = []
    charlib_rise_trans_data = []
    benchmark_rise_trans_data = []
    charlib_fall_trans_data = []
    benchmark_fall_trans_data = []

    benchmark_lib = parse_liberty(open(Path(benchmark), 'r').read())
    characterized_lib = parse_liberty(str(characterized))

    # Iterate over cells
    for charlib_cell in characterized_lib.get_groups('cell'):
        # Find this cell in the benchmark lib
        benchmark_cell = None
        for cell in benchmark_lib.get_groups('cell'):
            if cell.args[0] == charlib_cell.args[0]:
                benchmark_cell = cell
                break
        if benchmark_cell is None:
            print(f'Skipping cell "{charlib_cell.args[0]}": not found in {str(benchmark)}.')
            continue # Skip to next cell

        # Iterate over pins
        for charlib_pin in charlib_cell.get_groups('pin'):
            # Find the pin on the benchmark cell
            benchmark_pin = None
            for pin in benchmark_cell.get_groups('pin'):
                if pin.args[0] == charlib_pin.args[0]:
                    benchmark_pin = pin
                    break
            if benchmark_pin is None:
                print(f'Skipping pin "{charlib_cell.args[0]}.{charlib_pin.args[0]}": not found in {str(benchmark)}')
                continue # Skip to next pin

            # Iterate over timings
            for charlib_timing in charlib_pin.get_groups('timing'):
                # Find the timing on the benchmark pin
                benchmark_timing = None
                for timing in benchmark_pin.get_groups('timing'):
                    if timing['related_pin'] == charlib_timing['related_pin']:
                        benchmark_timing = timing
                        break
                if benchmark_timing is None:
                    print(f'Skipping timing for {charlib_cell.args[0]}.{charlib_pin.args[0]}.{charlib_timing["related_pin"]}')
                    continue

                # Average propagation delay
                charlib_rise_prop_data.append(np.mean(charlib_timing.get_groups('cell_rise')[0].get_array('values')))
                benchmark_rise_prop_data.append(np.mean(benchmark_timing.get_groups('cell_rise')[0].get_array('values')))
                charlib_fall_prop_data.append(np.mean(charlib_timing.get_groups('cell_fall')[0].get_array('values')))
                benchmark_fall_prop_data.append(np.mean(benchmark_timing.get_groups('cell_fall')[0].get_array('values')))

                # Average transient delay
                charlib_rise_trans_data.append(np.mean(charlib_timing.get_groups('rise_transition')[0].get_array('values')))
                benchmark_rise_trans_data.append(np.mean(benchmark_timing.get_groups('rise_transition')[0].get_array('values')))
                charlib_fall_trans_data.append(np.mean(charlib_timing.get_groups('fall_transition')[0].get_array('values')))
                benchmark_fall_trans_data.append(np.mean(benchmark_timing.get_groups('fall_transition')[0].get_array('values')))

    # Plot propagation delay data
    prop_figure, prop_ax = plt.subplots()
    prop_ax.grid()
    print(benchmark_rise_prop_data, charlib_rise_prop_data)
    prop_ax.scatter(benchmark_rise_prop_data, charlib_rise_prop_data, label='Rising')
    prop_ax.scatter(benchmark_fall_prop_data, charlib_fall_prop_data, label='Falling')
    prop_limits = [0, 1.1*max(max(benchmark_rise_prop_data), max(charlib_rise_prop_data))]
    prop_ax.plot(prop_limits, prop_limits, color='black', alpha=0.2, label='Ideal')
    prop_ax.set(
        xlim=prop_limits,
        ylim=prop_limits,
        xlabel='Benchmark Propagation Delay [ns]',
        ylabel='CharLib Propagation Delay [ns]',
        title='Propagation Delay Correlation'
    )
    prop_ax.legend()

    # Plot transient delay data
    tran_figure, tran_ax = plt.subplots()
    tran_ax.grid()
    tran_ax.scatter(benchmark_rise_trans_data, charlib_rise_trans_data, label='Rising')
    tran_ax.scatter(benchmark_fall_trans_data, charlib_fall_trans_data, label='Falling')
    tran_limits = [0, 1.1*max(max(benchmark_rise_trans_data), max(charlib_rise_trans_data))]
    tran_ax.plot(tran_limits, tran_limits, color='black', alpha=0.2, label='Ideal')
    tran_ax.set(
        xlim=tran_limits,
        ylim=tran_limits,
        xlabel='Benchmark Transient Delay [ns]',
        ylabel='CharLib Transient Delay [ns]',
        title='Transient Delay Correlation'
    )
    tran_ax.legend()

    plt.show()

    # Calculate absolute error
    rise_prop_ae = np.abs(np.asarray(charlib_rise_prop_data) - np.asarray(benchmark_rise_prop_data))
    fall_prop_ae = np.abs(np.asarray(charlib_fall_prop_data) - np.asarray(benchmark_fall_prop_data))
    rise_tran_ae = np.abs(np.asarray(charlib_rise_trans_data) - np.asarray(benchmark_rise_trans_data))
    fall_tran_ae = np.abs(np.asarray(charlib_fall_trans_data) - np.asarray(benchmark_fall_trans_data))
    # Calculate worst case absolute error
    rise_prop_max_ae = max(rise_prop_ae)
    fall_prop_max_ae = max(fall_prop_ae)
    rise_tran_max_ae = max(rise_tran_ae)
    fall_tran_max_ae = max(fall_tran_ae)
    # Calculate mean absolute error
    rise_prop_mae = np.mean(rise_prop_ae)
    fall_prop_mae = np.mean(fall_prop_ae)
    rise_tran_mae = np.mean(rise_tran_ae)
    fall_tran_mae = np.mean(fall_tran_ae)

    print('Rise prop', rise_prop_max_ae, rise_prop_mae)
    print('Fall prop', fall_prop_max_ae, fall_prop_mae)
    print('Rise tran', rise_tran_max_ae, rise_tran_mae)
    print('Fall tran', fall_tran_max_ae, fall_tran_mae)
