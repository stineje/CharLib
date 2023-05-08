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

def runSequentialTrial(settings, cell, harness, load, slew, setup_time, hold_time, timestep, timestep_scale, spice_filename, *energy):
    # Create a spice file to run the simulation
    spice_file = spice_filename + '.lis'
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
        f".param _tsimend = '_tend2 + tunit * 50 *tsimendmag'",
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
        f".tran {cell.sim_timestep}{str(settings.units.time)} '_tsimend'\n"
    ]

    # Data input: VIN
    # TODO: Fix this so that we can actually handle multiple data inputs
    if harness.target_in_port in cell.in_ports:
        # If targeted, vary with timing defined above
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
            if harness.set_direction == 'rise':
                v0, v1 = "'_vdd'", "'_vss'"
            else:
                v0, v1 = "'_vss'", "'_vdd'"
            outlines.append(f"VSIN VSIN 0 PWL(0 {v0} '_tstart1' {v0} '_tstart2' {v1} '_tend1' {v1} '_tend2' {v0} '_tsimend' {v0})")
        else:
            # Reset is static
            outlines.append("VSIN VSIN 0 DC " + ("'_vdd'" if harness.reset_state == '1' else "'_vss'"))

    # TODO next: Measure d2q