from charlib.characterizer.procedures import register, ProcedureFailedException
from charlib.characterizer import utils

import PySpice

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

@register
def sequential_delay(cell_settings, charlib_settings, data_pin, trigger_pin, state_pin):
    """Measure the delay between trigger activation and state change.

    For clock-edge-triggered devices, this is commonly called the clock-to-Q or C2Q delay. This
    value depends on the transition time of both the data pin and the trigger pin."""
    pass # TODO

@register
def sequential_min_pulse_width(cell_settings, charlib_settings, data_pin, trigger_pin, state_pin):
    """Find the minimum pulse width required for the trigger to activate the device.

    This is analagous to the min_pulse_width property of a set, reset, enable, or clock pin.

    For example, for a rising-edge DFF with an asynchronous reset, the minimum pulse width is the
    minimum time the clock signal must be active before the rising edge in order to reset the
    device state."""
    pass # TODO

@register
def sequential_setup_hold(cell, cell_settings, charlib_settings):
    """procedure for measuring setup and hold time
    This function returns (yield) jobs to be submitted to the PoolExecutor"""
    for variation in cell_settings.variations('data_slews', 'clock_slews'):
        for path in cell.paths():
            yield (sweep_setup_hold_skew_for_c2q, cell, cell_settings, charlib_settings, variation, path)

def sweep_setup_hold_skew_for_c2q(cell, config, settings, variation, path):
    """This function takes a range of setup skew and a range of hold skew,
    and runs every single combination of the two to find the C2Q delay.
    Giving us the 3D C2Q vs setup time (ts) vs hold time (th) surface.
    """
    t_c2q = get_c2q(cell, config, settings, variation['clock_slew'], variation['data_slew'], 1e-9, 1e-9, 40e-15, 2e-9)
    print(f"[sequential_delay] {cell.name} path={path} c2q={t_c2q}")
    return cell.liberty

def get_c2q(cell, config, settings, clk_slew, data_slew, t_setup_skew, t_hold_skew, c_load, t_stabilizing):
    """Build a SPICE testbench and run a transient simulation to get the clock-to-q delay
    for a given setup skew / hold skew, load capacitance and stabilizing time."""

    # Set up parameters
    t_clk_slew = clk_slew * settings.units.time
    t_data_slew = data_slew * settings.units.time
    vdd = settings.primary_power.voltage * settings.units.voltage
    vss = settings.primary_ground.voltage * settings.units.voltage

    # building waveform for data
    t = {}
    t['clk_edge_1_start'] = t_stabilizing
    t['clk_edge_1_end'] = t['clk_edge_1_start'] + t_clk_slew
    t['clk_edge_2_start'] = t['clk_edge_1_end'] + t_stabilizing
    t['clk_edge_2_end'] = t['clk_edge_2_start'] + t_clk_slew
    t['clk_edge_3_start'] = t['clk_edge_2_end'] + t_stabilizing + t_setup_skew - t_clk_slew / 2
    t['clk_edge_3_end'] = t['clk_edge_3_start'] + t_clk_slew

    t['data_edge_1_start'] = ( t['clk_edge_3_start'] + t_clk_slew / 2 ) - t_setup_skew
    t['data_edge_1_end'] = t['data_edge_1_start'] + t_data_slew
    t['data_edge_2_start'] = ( t['clk_edge_3_start'] + t_clk_slew / 2 ) + t_hold_skew 
    t['data_edge_2_end'] = t['data_edge_2_start'] + t_data_slew

    t['sim_end'] = t['data_edge_2_end'] + t_stabilizing # wait for the system to stabilize

    # Initialize circuit
    circuit = utils.init_circuit("sequential_setup_hold", cell.netlist, config.models)
    circuit.V('dd', 'vdd', circuit.gnd, vdd) # for input pins
    circuit.V('ss', 'vss', circuit.gnd, vss) # for input pins
    circuit.V('dd_dyn', 'vdd_dyn', circuit.gnd, vdd) # separate voltage sources for VDD / VSS pins of DUT for measuring dynamic power 
    circuit.V('ss_dyn', 'vss_dyn', circuit.gnd, vss) # separate voltage sources for VDD / VSS pins of DUT for measuring dynamic power 
    circuit.V('o_cap', 'vout', 'wout', 0) # 0 volt source in series with c_load is a trick to measure current through the load capacitor.
    circuit.C('c_load', 'wout', circuit.gnd, c_load)

    # Set up clock input
    (v0, v1) = (vdd, vss) if False else (vss, vdd)
    circuit.PieceWiseLinearVoltageSource('clk', 'vclk', circuit.gnd, values=[
        (0, v0),
        (t['clk_edge_1_start'], v0),
        (t['clk_edge_1_end'], v1),
        (t['clk_edge_2_start'], v1),
        (t['clk_edge_2_end'], v0),
        (t['clk_edge_3_start'], v0),
        (t['clk_edge_3_end'], v1),
        (t['sim_end'], v1)
    ])

    # Set up data input node
    (v0, v1) = (vss, vdd) if True else (vdd, vss)
    circuit.PieceWiseLinearVoltageSource('data', 'vdata', circuit.gnd, values=[
        (0, v0),
        (t['data_edge_1_start'], v0),
        (t['data_edge_1_end'], v1),
        (t['data_edge_2_start'], v1),
        (t['data_edge_2_end'], v0),
        (t['sim_end'], v0)
    ])

    # Initialize device under test subcircuit and wire up ports
    connections = []
    for port in cell.ports:
      if port.role == 'clock':
          connections.append('vclk')
      elif port.name == 'D':
          connections.append('vdata')         
      elif port.name == 'Q':
          connections.append('vout')          
      elif port.role == 'primary_power':
          connections.append('vdd')
      elif port.role == 'primary_ground':
          connections.append('vss')
      else:
          connections.append('wfloat0')       # float unrecognized
    circuit.X('dut', cell.name, *connections)

    # Build the simulation
    simulator = PySpice.Simulator.factory(simulator=settings.simulation.backend)
    simulation = simulator.simulation(
        circuit,
        temperature=settings.temperature,
        nominal_temperature=settings.temperature
    )
    simulation.options('autostop', 'nopage', 'nomod', post=1, ingold=2, trtol=1)

    # measure c2q
    simulation.measure('tran',
                     't_c2q',
                     f'trig v(vclk) val={float(vdd/2)} RISE=2',
                     f'targ v(vout) val={float(vdd/2)} RISE=1',
                     run=False)

    try:
        # hardcode the simulation step and time for now, to be reviewed
        analysis = simulation.transient(step_time=t_data_slew/8, end_time=t['sim_end'], run=True)
    except Exception as e:
        msg = f'Procedure get_c2q failed for cell {cell.name}, setup_skew = {t_setup_skew}, hold_skew = {t_hold_skew}'
        raise ProcedureFailedException(msg) from e

    if settings.debug:
        debug_path = settings.debug_dir / cell.name / __name__.split('.')[-1]
        debug_path.mkdir(parents=True, exist_ok=True)
        with open(debug_path / f'{cell.name}_setup_skew_{t_setup_skew}_hold_skew_{t_hold_skew}_c_load_{c_load}.spice', 'w') as f:
            f.write(str(simulation))

    t_c2q = analysis.measurements['t_c2q']

    return t_c2q

def sequential_setup_hold_search(cell, config, settings, variation, path):
    """The goal of this fucntion is to find the minimum setup and hold time of a sequential cell,
    give an input transition and output load.

    Terminology used here :
    - clock-to-q delay = C2Q = c2q
    - setup skew = the amount of D2C set in simulation, usually becomes setup time
    - hold skew = the amount of C2D set in simulation, usually becomes hold time

    The following few terminologies are used in this very important paper : https://ieeexplore.ieee.org/document/4167994
    - minimum hold pair = MHP 
    - minimum setup pair = MSP
    - minimum setup & hold pair = MSHP = the pair of setup and hold time where the sum of the two
                                         is the smallest out of the sum from all other pairs on the same contour   
                                         on the same contour (i.e. same C2Q)
    
    The big picture steps taken here, which does not completely reflect what the paper define is :
    1. Find the 3D C2Q vs setup time (ts) vs hold time (th) surface.
    2. Find a setup skew vs hold skew contour by selecting C2Q based on boundry conditions.
    3. Find one point on the contour (MSHP) for our LIBERTY library

    =======================
    = The steps in detail =
    =======================
    * assumption : smallest setup time always cooresponds to the largest hold time, vice versa
    * terminology : to the rigth means increase in time, to the left means decrease in time

    1. find min setup skew : infinite hold skew, binary search to the right for min setup time
    2. find max hold skew to run the cell : min setup skew, binary search to the left for max hold time 
    3. save pulse width (setup skew + hold skew) from the last run, keep moving the window to the left by 
       a binary search.
       During the binary search, if there is no transition on Q, double the setup skew (which also increase the pulse width).
       Algorithm stops when setup skew has been increased 5 times and there is still no transition on Q. 
       This means we have hit the smallest hold possible, the smallest hold time is hold skew from the second last run.
    4. take minimum min hold skew and increase setup skew to the left until the C2Q curve flattens out. 
       Check that the C2Q curve flattens out by checking the slope of the C2Q curve.
       
    After these few steps, we should have the boundries for 3D C2Q vs setup time (ts) vs hold time (th) surface.
    """
    pass
