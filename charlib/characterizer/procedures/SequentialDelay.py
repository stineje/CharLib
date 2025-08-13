

def measure_recovery_constraint(cell_settings, charlib_settings, control_pin, trigger_pin, state_pin):
    """Find the minimum time a control pin must be active before the trigger.

    This is analagous to setup time for an asynchronous control pin.

    For example, for a rising-edge DFF with an asynchronous reset, recovery time is the minimum
    time the reset signal must be active before the rising clock edge in order to reset the device
    state."""
    pass # TODO

def measure_removal_constraint(cell_settings, charlib_settings, control_pin, trigger_pin, state_pin):
    """Find the mimimum time a control pin must remain active after the trigger.

    This is analagous to hold time for an asynchronous control pin.

    For example, for a rising-edge DFF with an asynchronous reset, removal time is the minimum time
    that the reset signal must remain active after the rising clock edge in order to reset the
    device state."""
    pass # TODO

def binary_search_setup_hold_constraint(cell_settings, charlib_settings, data_pin, trigger_pin, state_pin):
    """Find the minimum time the data pin must be set preceding and following the trigger.

    The minimum time the data pin must be set before the trigger is the setup time. The minimum
    time the data pin must be set after the trigger is the hold time.

    This method measures both constraints using a binary search algorithm. Each delay is bisected
    repeatedly until the device fails to change state during simulation until minima are found for
    both constraints."""
    pass # TODO

def measure_delays(cell_settings, charlib_settings, data_pin, trigger_pin, state_pin):
    """Measure the delay between trigger activation and state change.

    For clock-edge-triggered devices, this is commonly called the clock-to-Q or C2Q delay. This
    value depends on the transition time of both the data pin and the trigger pin."""
