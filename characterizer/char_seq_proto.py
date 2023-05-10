import re, subprocess
import numpy as np
from characterizer.Harness import SequentialHarness

def runSequentialDelay():
    # TODO
    pass

def runSequentialRecoveryRemoval():
    # TODO
    pass

def findSetupTime(settings, cell, harness, load, slew, setup_range, min_hold_time, timestep, spice_filename):
    # TODO
    pass

def findHoldTime(settings, cell, harness, load, slew, setup_time, hold_range, timestep, spice_filename):
    # TODO
    pass

def runSequentialTrial(settings, cell, harness, output_filename, load, slew, setup_time, hold_time, tsimendmag, tranmag, timestep_scale, *energy):
    # Create a spice file to run the simulation
    outlines = [
        f'*title: flop delay meas.',
        f'.option brief nopage nomod post=1 ingold=2 autostop',
        f".inc '../{cell.model}'",
        f".inc '../{str(cell.netlist)}'",
        f'.temp {str(settings.temperature)}',
        f'.param _vdd = {str(settings.vdd.voltage)}',
        f'.param _vss = {str(settings.vss.voltage)}',
        f'.param _vnw = {str(settings.nwell.voltage)}',
        f'.param _vpw = {str(settings.pwell.voltage)}',
        f'.param cap = 10f', # TODO: is this correct?
        f'.param slew = 100p ', # TODO: is this correct?
        f'.param cslew = 100p',
        f'.param tunit = 100p',
        f'.param tsetup = 100p',
        f'.param thold = 100p',
        f'.param tsimendmag = 100 tranmag = 1',
        f'.param _tslew = slew',
        f'.param _tclk1 = slew',                                # First clock posedge
        f".param _tclk2 = '_tclk1 + cslew'",                    # 
        f".param _tclk3 = '_tclk2 + tunit'",                    #
        f".param _tclk4 = '_tclk3 + cslew'",                    # First clock negedge / Recovery
        f".param _tclk5 = '_tclk4 + tunit'",                    # Removal
        f".param _tstart1 = '_tclk5 + tunit * 10 + tsetup'",    # Data input start
        f".param _tstart2 = '_tstart1 + slew'",                 # Varied with D edge
        f".param _tend1 = '_tstart2 + tunit + thold'",          # Data input end
        f".param _tend2 = '_tend1 + slew'",                     # Varied with D edge
        f".param _tclk6 = '_tclk4 + tunit * 10'",               # Second clock posedge
        f".param _tclk7 = '_tclk6 + cslew'",                    # Second clock negedge
        f".param _tsimend = '_tend2 + tunit * 50 * tsimendmag'",
        f'.param _Energy_meas_end_extent = {str(settings.energy_meas_time_extent)}\n',
        f".measure Tran tstart2_to_tend1 param='_tend1 - _tstart2'",
        f"VDD_DYN VDD_DYN 0 DC '_vdd'",
        f"VSS_DYN VSS_DYN 0 DC '_vss'",
        f"VNW_DYN VNW_DYN 0 DC '_vnw'",
        f"VPW_DYN VPW_DYN 0 DC '_vpw'",
        f"VDD_LEAK VDD_LEAK 0 DC '_vdd'",
        f"VSS_LEAK VSS_LEAK 0 DC '_vss'",
        f"VNW_LEAK VNW_LEAK 0 DC '_vnw'",
        f"VPW_LEAK VPW_LEAK 0 DC '_vpw'",
        f'* output load calculation',
        f'VOCAP VOUT WOUT DC 0\n',
        f".tran {cell.sim_timestep*timestep_scale}{str(settings.units.time)} '_tsimend'\n"
    ]

    # Data input: VIN
    if harness.target_in_port in cell.in_ports:
        # If the input port is targeted, vary with timing defined above
        # TODO: Fix this so that we can actually handle multiple data inputs
        target_vname = 'VIN'
        if harness.in_direction == 'rise':
            v0, v1 = "'_vss'", "'_vdd'" # Rise from vss to vdd
        else:
            v0, v1 = "'_vdd'", "'_vss'" # Fall from vdd to vss
        outlines.append(f"VIN VIN 0 PWL(0 {v0} '_tstart1' {v0} '_tstart2' {v1} '_tend1' {v1} '_tend2' {v0} '_tsimend' {v0})")
    else:
        # If not targeted, hold stable
        for port, value in zip(harness.stable_in_ports, harness.stable_in_port_values):
            outlines.append("VIN VIN 0 DC " + ("'_vdd'" if value == '1' else "'_vss'"))
    
    # Clock input: VCIN
    # The original code also includes provisions for single clock pulses e.g. 010, but they are never used
    # TODO: Evaluate whether we need to include logic for single clock pulse ops
    if harness.timing_type_clock == 'falling_edge':
        v0, v1 = "'_vss'", "'_vdd'"
    else:
        v0, v1 = "'_vdd'", "'_vss'"
    outlines.append(f"VCIN VCIN 0 PWL(0 {v0} '_tclk1' {v0} '_tclk2' {v1} '_tclk3' {v1} '_tclk4' {v0} '_tclk6' {v0} '_tclk7' {v1} '_tsimend' {v1})")

    # Reset
    # Note that this assumes active low reset, so rise = high-to-low
    if harness.reset:
        if harness.reset_direction:
            # Reset is rising or falling
            target_vname = 'VRIN'
            if harness.reset_direction == 'rise':
                v0, v1 = "'_vdd'", "'_vss'"
            else:
                v0, v1 = "'_vss'", "'_vdd'"
            outlines.append(f"VRIN VRIN 0 PWL(0 {v0} '_tstart1' {v0} '_tstart2' {v1} '_tend1' {v1} '_tend2' {v0} '_tsimend' {v0})")
        else:
            # Reset is static
            outlines.append("VRIN VRIN 0 DC " + ("'_vdd'" if harness.reset_state == '1' else "'_vss'"))

    # Set
    # Note that this assumes active low set, so rise = high-to-low
    if harness.set:
        if harness.set_direction:
            # Set is rising or falling
            target_vname = 'VSIN'
            if harness.set_direction == 'rise':
                v0, v1 = "'_vdd'", "'_vss'"
            else:
                v0, v1 = "'_vss'", "'_vdd'"
            outlines.append(f"VSIN VSIN 0 PWL(0 {v0} '_tstart1' {v0} '_tstart2' {v1} '_tend1' {v1} '_tend2' {v0} '_tsimend' {v0})")
        else:
            # Set is static
            outlines.append("VSIN VSIN 0 DC " + ("'_vdd'" if harness.set_state == '1' else "'_vss'"))

    # Measure propagation delays
    outlines.append('** Delay')

    # D to Q propagation delay
    outlines.append('* Propagation delay (D to Q)')
    if harness.in_direction == 'rise':
        v_in_start = settings.logic_threshold_low_voltage()
        v_in_end = settings.logic_threshold_high_voltage()
        vt_in = settings.logic_low_to_high_threshold_voltage()
        vt_in_inv = settings.logic_high_to_low_threshold_voltage()
    elif harness.in_direction == 'fall':
        v_in_start = settings.logic_threshold_high_voltage()
        v_in_end = settings.logic_threshold_low_voltage()
        vt_in = settings.logic_high_to_low_threshold_voltage()
        vt_in_inv = settings.logic_low_to_high_threshold_voltage()
    else:
        raise ValueError(f'Unable to configure simulation: no target input pin')
    if harness.out_direction == 'rise':
        v_out_start = settings.logic_threshold_low_voltage()
        v_out_end = settings.logic_threshold_high_voltage()
        vt_out = settings.logic_low_to_high_threshold_voltage()
    elif harness.out_direction == 'fall':
        v_out_start = settings.logic_threshold_high_voltage()
        v_out_end = settings.logic_threshold_low_voltage()
        vt_out = settings.logic_high_to_low_threshold_voltage()
    else:
        raise ValueError(f'Unable to configure simulation: no target output pin')
    outlines.extend([
        f'.measure Tran PROP_IN_OUT trig v("{target_vname}") val=\'{vt_in}\' td=\'_tclk5\' {harness.in_direction}=1',
        f'+ targ v(VOUT) val=\'{vt_out}\' {harness.out_direction}=1',
        f'.measure TRAN TRANS_OUT trig v(VOUT) val=\'{v_out_start}\' {harness.out_direction}=1',
        f'+ targ v(VOUT) val=\'{v_out_end}\' {harness.out_direction}=1'
    ])

    # C to Q propagation delay
    outlines.append('* Propagation delay (C to Q)')
    if harness.timing_sense_clock == 'risiing_edge':
        clk_direction = 'rise'
        v_clk_start = settings.logic_threshold_low_voltage()
        v_clk_end = settings.logic_threshold_high_voltage()
        vt_clk = settings.logic_low_to_high_threshold_voltage()
    else:
        clk_direction = 'fall'
        v_clk_start = settings.logic_threshold_high_voltage()
        v_clk_end = settings.logic_threshold_low_voltage()
        vt_clk = settings.logic_high_to_low_threshold_voltage()
    outlines.extend([
        f'.measure Tran PROP_CIN_OUT trig v(VCIN) val=\'{vt_clk}\' td=\'_tclk5\' {clk_direction}=1',
        f'+ targ v(VOUT) val=\'{vt_in}\' {harness.in_direction}=1'
    ])

    # D to C setup delay
    outlines.append('* Setup delay (D to C)')
    outlines.extend([
        f'.measure Tran PROP_IN_D2C trig v({target_vname}) val=\'{vt_in}\' td=\'_tclk5\' {harness.in_direction}=1',
        f'+ targ v(VCIN) val=\'{vt_clk}\' {clk_direction}=1'
    ])

    # C to D hold delay
    outlines.append('* Hold delay (C to D)')
    outlines.extend([
        f'.measure Tran PROP_IN_C2D trig v(VCIN) val=\'{vt_clk}\' td=\'_tclk5\' {clk_direction}=1',
        f'+ targ v({target_vname}) val=\'{vt_in_inv} {"rise" if harness.in_direction == "fall" else "fall"}=1'
    ])

    # Measure energy
    if not energy:
        # Measure energy results
        outlines.extend([
            f'.measure Tran ENERGY_START when v({target_vname})=\'{v_in_start}\' {harness.in_direction}=1',
            f'.measure Tran ENERGY_END when v(VOUT)=\'{v_out_end}\' {harness.out_direction}=1',
            f'.measure Tran ENERGY_CLK_START when v(VCIN)=\'{v_clk_start}\' {clk_direction}=1',
            f'.measure Tran ENERGY_CLK_START when v(VCIN)=\'{v_clk_end}\' {clk_direction}=1'
        ])
    else:
        # Fetch energy results from previous trial, then measure charge and capacitance
        outlines.extend([
            f'.param ENERGY_START = {harness.results[slew][load]["energy_start"]}',
            f'.param ENERGY_END = {harness.results[slew][load]["energy_end"]}',
            f'.param ENERGY_CLK_START = {harness.results[slew][load]["energy_clk_start"]}',
            f'.param ENERGY_CLK_END = {harness.results[slew][load]["energy_clk_end"]}',
            f'*',
            f'** In/Out Q, Capacitance',
            f'*',
            f'.measure Tran Q_IN_DYN integ i({target_vname}) from=\'ENERGY_START\' to=\'ENERGY_END\'',
            f'.measure Tran Q_OUT_DYN integ i(VOCAP) from=\'ENERGY_START\' to=\'ENERGY_END*_Energy_meas_end_extent\'',
            f'.measure Tran Q_CLK_DYN integ i(VCIN) from=\'ENERGY_CLK_START\' to=\'ENERGY_CLK_END\'\n',
            f'*',
            f'** Energy',
            f'*  (Total charge, short-circuit charge)',
            f'.measure Tran Q_VDD_DYN integ i(VDD_DYN) from=\'ENERGY_START\' to=\'ENERGY_END*_Energy_meas_end_extend\'',
            f'.measure Tran Q_VSS_DYN integ i(VSS_DYN) from=\'ENERGY_START\' to=\'ENERGY_END*_Energy_meas_end_extent\'\n',
            f'* Leakage current',
            f'.measure Tran I_VDD_LEAK avg i(VDD_DYN) from=\'_tstart1*0.1\' to=\'_tstart1\'',
            f'.measure Tran I_VSS_LEAK avg i(VSS_DYN) from=\'_tstart1*0.1\' to=\'_tstart1\'\n',
            f'* Gate leak current',
            f'.measure Tran I_IN_LEAK avg i(VIN) from==\'_tstart1*0.1\' to=\'_tstart1\''
        ])

    outlines.extend([
        "XDFF VIN VCIN VRIN VSIN VOUT VHIGH VLOW VDD_DYN VSS_DYN VNW_DYN VPW_DYN DUT",
        "C0 WOUT VSS_DYN 'cap'",
        ".SUBCKT DUT IN CIN RIN SIN OUT HIGH LOW VDD VSS VNW VPW"
    ])

    # Parse subcircuit definition
    port_list = cell.instance.split()
    circuit_name = port_list.pop(-1)
    tmp_line = port_list.pop(0)
    for port in port_list:
        # Check target inport
        is_matched = 0
        if port == harness.target_in_port:
            tmp_line += ' IN'
            is_matched += 1
        # Check stable inports
        for stable_port, state in zip(harness.stable_in_ports, harness.stable_in_port_states):
            if port == stable_port:
                if state == '1':
                    tmp_line += ' HIGH'
                    is_matched += 1
                elif state == '0':
                    tmp_line += ' LOW'
                    is_matched += 1
                else:
                    raise ValueError(f'Invalid state for port {port}: {state}')
        # Check clock
        if port == harness.clock:
            tmp_line += ' CIN'
            is_matched += 1
        # Check reset
        if cell.reset and port == harness.reset:
            tmp_line += ' RIN'
            is_matched += 1
        # Check set
        if cell.set and port == harness.set:
            tmp_line += ' SIN'
            is_matched += 1
        # Check target outport
        if port == harness.target_out_port:
            tmp_line += ' OUT'
            is_matched += 1
        # Check non-target outports
        for nontarget_port, state in zip(harness.nontarget_out_ports, harness.nontarget_out_port_states):
            if port == nontarget_port:
                tmp_line += f' WFLOAT{str(state)}'
                is_matched += 1
        # Check VDD, VSS, VNW, and VPW
        if port.upper() == settings.vdd.name.upper():
                tmp_line += f' {port.upper()}'
                is_matched += 1
        if port.upper() == settings.vss.name.upper():
                tmp_line += f' {port.upper()}'
                is_matched += 1
        if port.upper() == settings.pwell.name.upper():
                tmp_line += f' {port.upper()}'
                is_matched += 1
        if port.upper() == settings.nwell.name.upper():
                tmp_line += f' {port.upper()}'
                is_matched += 1
        ## show error if this port has not matched
        if not is_matched:
            raise ValueError(f"Port {port} not found in netlist")
    tmp_line += f" {circuit_name}\n"
    outlines.append(tmp_line)
    outlines.append(".ends")

    # Handle remaining parameters
    outlines.extend([
        f'.param cap = {load}{settings.units.capacitance.symbol}',
        f'.param slew = {slew/(settings.logic_threshold_high-settings.logic_threshold_low)}{str(settings.units.time)}',
        f'.param cslew = {cell.clock_slope}{str(settings.units.time)}',
        f'.param tunit = {cell.in_slews[-1]}{str(settings.units.time)}',
        f'.param tsetup = {setup_time}{str(settings.units.time)}',
        f'.param thold = {hold_time}{str(settings.units.time)}',
        f'.param tsimendmag = {tsimendmag} tranmag = {tranmag}'
    ])

    # Write to spice file
    with open(f'{output_filename}.sp', 'w') as f:
        f.writelines('\n'.join(outlines))
        f.close()

    # Run spice simulation
    if 'ngspice' in str(settings.simulator):
        cmd = f'{str(settings.simulator.resolve())} -b {output_filename}.sp 1> {output_filename}.lis 2> /dev/null\n'
    elif 'hspice' in str(settings.simulator):
        cmd = f'{str(settings.simulator.resolve())} {output_filename}.sp -o {output_filename}.lis 2> /dev/null\n'
    else:
        raise ValueError(f'Unrecognized simulator "{str(settings.simulator)}"')
    with open(f'{output_filename}.run', 'w') as f:
        f.writelines([cmd])
        f.close
    if settings.run_sim:
        subprocess.run(['sh', f'{output_filename}.run'])

    # Read results from file
    results = {}
    desired_measurements = ['prop_in_out', 'prop_cin_out', 'trans_out', 'prop_in_d2c', 'tstart2_to_tend1']
    if not energy:
        desired_measurements += ['energy_start', 'energy_end', 'energy_clk_start', 'energy_clk_end']
    else:
        desired_measurements += ['q_in_dyn', 'q_out_dyn', 'q_clk_dyn', 'q_vdd_dyn', 'q_vss_dyn', 'i_vdd_leak', 'i_vss_leak', 'i_in_leak']
    with open(f'{output_filename}.lis', 'r') as f:
        for inline in f:
            if any([f in inline for f in ['failed', 'Error']]):
                raise NameError(f'An error occurred while running simulation. See {output_filename}.lis')
            if 'hspice' in str(settings.simulator):
                inline = re.sub('\=',' ',inline)
            measurement = next((m for m in desired_measurements if m in inline), False)
            if measurement:
                results[measurement] = float(inline.split()[2])
        f.close()

    return results