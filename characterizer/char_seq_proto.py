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
        f'.param _tclk1 = slew',
        f".param _tclk2 = '_tclk1 + cslew'",
        f".param _tclk3 = '_tclk2 + tunit'",
        f".param _tclk4 = '_tclk3 + cslew'",
        f".param _tclk5 = '_tclk4 + tunit'",
        f".param _tstart1 = '_tclk5 + tunit * 10 + tsetup'",
        f".param _tstart2 = '_tstart1 + slew'",
        f".param _tend1 = '_tstart2 + tunit + thold'",
        f".param _tend2 = '_tend1 + slew'",
        f".param _tclk6 = '_tclk4 + tunit * 10'",
        f".param _tclk7 = '_tclk6 + cslew'",
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

    