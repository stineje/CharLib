import re, subprocess, sys, threading 

from characterizer.LibrarySettings import LibrarySettings
from characterizer.LogicCell import LogicCell
from characterizer.Harness import CombinationalHarness

def runCombinational(target_lib: LibrarySettings, target_cell: LogicCell, expectation_list):
    """Run delay characterization for an N-input 1-output combinational cell"""
    for test_vector in expectation_list:
        # Generate harness
        harness = CombinationalHarness(target_cell, test_vector)
        
        # Generate spice file name
        spice_filename = f'delay1_{target_cell.name}'
        spice_filename += f'_{harness.target_in_port}{harness.target_inport_val}'
        for input, state in zip(harness.stable_in_ports, harness.stable_in_port_states):
            spice_filename += f'_{input}{state}'
        spice_filename += f'_{harness.target_out_port}{harness.target_outport_val}'

        # Run delay characterization
        if target_lib.use_multithreaded:
            runSpiceCombDelayMultiThread(target_lib, target_cell, harness, spice_filename)
        else:
            runSpiceCombDelay(target_lib, target_cell, harness, spice_filename)

        # Save harness to the cell
        target_cell.harnesses.append(harness)

def runSpiceCombDelayMultiThread(target_lib, target_cell, target_harness, spicef):
    # One trial for each input slope / output load combination
    thread_id = 0
    threadlist = []
    for tmp_slope in target_cell.in_slopes:
        for tmp_load in target_cell.out_loads:
            thread = threading.Thread(target=runSpiceCombDelaySingle,
                    args=([target_lib, target_cell, target_harness, spicef, tmp_slope, tmp_load]),
                    name="%d" % thread_id)
            threadlist.append(thread)
            thread_id += 1
    for thread in threadlist:
        thread.start()
    for thread in threadlist:
        thread.join()

def runSpiceCombDelaySingle(target_lib: LibrarySettings, target_cell: LogicCell, target_harness: CombinationalHarness, spicef, in_slope, out_load):
    print("start thread :"+str(threading.current_thread().name))
    spicefo = str(spicef)+"_"+str(out_load)+"_"+str(in_slope)+".sp"

    ## 1st trial, extract energy_start and energy_end
    trial_results = genFileLogic_trial1(target_lib, target_cell, target_harness, 0, in_slope, out_load, "none", "none", spicefo)
    energy_start = trial_results['energy_start']
    energy_end = trial_results['energy_end']
    estart_line = ".param ENERGY_START = "+str(energy_start)+"\n"
    eend_line = ".param ENERGY_END = "+str(energy_end)+"\n"

    ## 2nd trial
    trial_results = genFileLogic_trial1(target_lib, target_cell, target_harness, 1, in_slope, out_load, estart_line, eend_line, spicefo)
    trial_results['energy_start'] = energy_start
    trial_results['energy_end'] = energy_end

    if not target_harness.results.get(str(in_slope)):
        target_harness.results[str(in_slope)] = {}
    target_harness.results[str(in_slope)][str(out_load)] = trial_results
    print("end thread :"+str(threading.current_thread().name))

def runSpiceCombDelay(target_lib: LibrarySettings, target_cell: LogicCell, target_harness: CombinationalHarness, spicef):
    # Test each input slope with each output load
    for tmp_slope in target_cell.in_slopes:
        for tmp_load in target_cell.out_loads:
            spicefo = str(spicef)+"_"+str(tmp_load)+"_"+str(tmp_slope)+".sp"

            ## 1st trial, extract energy_start and energy_end
            trial_results = genFileLogic_trial1(target_lib, target_cell, target_harness, 0, tmp_slope, tmp_load, "none", "none", spicefo)
            energy_start = trial_results['energy_start']
            energy_end = trial_results['energy_end']
            estart_line = ".param ENERGY_START = "+str(energy_start)+"\n"
            eend_line = ".param ENERGY_END = "+str(energy_end)+"\n"

            ## 2nd trial
            trial_results = genFileLogic_trial1(target_lib, target_cell, target_harness, 1, tmp_slope, tmp_load, estart_line, eend_line, spicefo)
            trial_results['energy_start'] = energy_start
            trial_results['energy_end'] = energy_end

            if not target_harness.results.get(str(tmp_slope)):
                target_harness.results[str(tmp_slope)] = {}
            target_harness.results[str(tmp_slope)][str(tmp_load)] = trial_results

def genFileLogic_trial1(target_lib: LibrarySettings, target_cell: LogicCell, target_harness: CombinationalHarness, meas_energy: bool, in_slope, out_load, estart_line, eend_line, spicef: str):
    outlines = []
    outlines.append("*title: delay meas.\n")
    outlines.append(".option brief nopage nomod post=1 ingold=2 autostop\n")
    outlines.append(f".inc '../{target_cell.model}'\n")
    outlines.append(f".inc '../{str(target_cell.netlist)}'\n")
    outlines.append(f".temp {str(target_lib.temperature)}\n")
    outlines.append(f".param _vdd = {str(target_lib.vdd.voltage)}\n")
    outlines.append(f".param _vss = {str(target_lib.vss.voltage)}\n")
    outlines.append(f".param _vnw = {str(target_lib.nwell.voltage)}\n")
    outlines.append(f".param _vpw = {str(target_lib.pwell.voltage)}\n")
    outlines.append(".param cap = 10f \n") # TODO: is this correct?
    outlines.append(".param slew = 100p \n") # TODO: is this correct?
    outlines.append(".param _tslew = slew\n")
    outlines.append(".param _tstart = slew\n")
    outlines.append(".param _tend = '_tstart + _tslew'\n")
    outlines.append(".param _tsimend = '_tslew * 10000' \n")
    outlines.append(f".param _Energy_meas_end_extent = {str(target_lib.energy_meas_time_extent)}\n")
    outlines.append(" \n")
    outlines.append("VDD_DYN VDD_DYN 0 DC '_vdd' \n")
    outlines.append("VSS_DYN VSS_DYN 0 DC '_vss' \n")
    outlines.append("VNW_DYN VNW_DYN 0 DC '_vnw' \n")
    outlines.append("VPW_DYN VPW_DYN 0 DC '_vpw' \n")
    outlines.append("* output load calculation\n")
    outlines.append("VOCAP VOUT WOUT DC 0\n")
    #outlines.append("VDD_LEAK VDD_LEAK 0 DC '_vdd' \n")
    #outlines.append("VSS_LEAK VSS_LEAK 0 DC '_vss' \n")
    #outlines.append("VNW_LEAK VNW_LEAK 0 DC '_vnw' \n")
    #outlines.append("VPW_LEAK VPW_LEAK 0 DC '_vpw' \n")
    outlines.append(" \n")
    ## in auto mode, simulation timestep is 1/10 of min. input slew
    ## simulation runs 1000x of input slew time
    outlines.append(f".tran {str(target_cell.sim_timestep)}{str(target_lib.units.time)} '_tsimend'\n")
    outlines.append(" \n")

    if target_harness.in_direction == 'rise':
        outlines.append("VIN VIN 0 PWL(1p '_vss' '_tstart' '_vss' '_tend' '_vdd' '_tsimend' '_vdd') \n")
    elif target_harness.in_direction == 'fall':
        outlines.append("VIN VIN 0 PWL(1p '_vdd' '_tstart' '_vdd' '_tend' '_vss' '_tsimend' '_vss') \n")
    outlines.append("VHIGH VHIGH 0 DC '_vdd' \n")
    outlines.append("VLOW VLOW 0 DC '_vss' \n")

    ##
    ## delay measurement 
    outlines.append("** Delay \n")
    if target_harness.in_direction == 'rise':
        prop_start_v = target_lib.logic_low_to_high_threshold_voltage()
    else:
        prop_start_v = target_lib.logic_high_to_low_threshold_voltage()
    if target_harness.out_direction == 'rise':
        prop_end_v = target_lib.logic_low_to_high_threshold_voltage()
        trans_start_v = target_lib.logic_threshold_low_voltage()
        trans_end_v = target_lib.logic_threshold_high_voltage()
    else:
        prop_end_v = target_lib.logic_low_to_high_threshold_voltage()
        trans_start_v = target_lib.logic_threshold_high_voltage()
        trans_end_v = target_lib.logic_threshold_low_voltage()
    outlines.append("* Prop delay \n")
    outlines.append(f".measure Tran PROP_IN_OUT trig v(VIN) val='{str(prop_start_v)}' {target_harness.in_direction}=1\n")
    outlines.append(f"+ targ v(VOUT) val='{str(prop_end_v)}' {target_harness.out_direction}=1\n")
    outlines.append("* Trans delay \n")
    outlines.append(f".measure Tran TRANS_OUT trig v(VOUT) val='{str(trans_start_v)}' {target_harness.out_direction}=1\n")
    outlines.append(f"+ targ v(VOUT) val='{str(trans_end_v)}' {target_harness.out_direction}=1\n")

    # get ENERGY_START and ENERGY_END for energy calculation in 2nd round 
    if not meas_energy:
        outlines.append("* For energy calculation \n")
        outlines.append(f".measure Tran ENERGY_START when v(VIN)='{str(target_lib.energy_meas_low_threshold_voltage())}' {target_harness.in_direction}=1\n")
        outlines.append(f".measure Tran ENERGY_END when v(VOUT)='{str(target_lib.energy_meas_high_threshold_voltage())}' {target_harness.out_direction}=1\n")

    ## energy measurement 
    elif meas_energy:
        outlines.append(estart_line)
        outlines.append(eend_line)
        outlines.append("* \n")
        outlines.append("** In/Out Q, Capacitance \n")
        outlines.append("* \n")
        outlines.append(".measure Tran Q_IN_DYN integ i(VIN) from='ENERGY_START' to='ENERGY_END'  \n")
        outlines.append(".measure Tran Q_OUT_DYN integ i(VOCAP) from='ENERGY_START' to='ENERGY_END*_Energy_meas_end_extent' \n")
        outlines.append(" \n")
        outlines.append("* \n")
        outlines.append("** Energy \n")
        outlines.append("*  (Total charge, Short-Circuit Charge) \n")
        outlines.append(".measure Tran Q_VDD_DYN integ i(VDD_DYN) from='ENERGY_START' to='ENERGY_END*_Energy_meas_end_extent'  \n")
        outlines.append(".measure Tran Q_VSS_DYN integ i(VSS_DYN) from='ENERGY_START' to='ENERGY_END*_Energy_meas_end_extent'  \n")
        outlines.append(" \n")
        outlines.append("* Leakage current \n")
        outlines.append(".measure Tran I_VDD_LEAK avg i(VDD_DYN) from='_tstart*0.1' to='_tstart'  \n")
        outlines.append(".measure Tran I_VSS_LEAK avg i(VSS_DYN) from='_tstart*0.1' to='_tstart'  \n")
        outlines.append(" \n")
        outlines.append("* Gate leak current \n")
        outlines.append(".measure Tran I_IN_LEAK avg i(VIN) from='_tstart*0.1' to='_tstart'  \n")
    else:
        print("Error, meas_energy should 0 (disable) or 1 (enable)")
        exit()

    ## for ngspice batch mode 
    outlines.append("*comment out .control for ngspice batch mode \n")
    outlines.append("*.control \n")
    outlines.append("*run \n")
    outlines.append("*plot V(VIN) V(VOUT) \n")
    outlines.append("*.endc \n")

    outlines.append("XINV VIN VOUT VHIGH VLOW VDD_DYN VSS_DYN VNW_DYN VPW_DYN DUT \n")
    outlines.append("C0 WOUT VSS_DYN 'cap'\n")
    outlines.append(" \n")
    outlines.append(".SUBCKT DUT IN OUT HIGH LOW VDD VSS VNW VPW \n")

    # parse subckt definition
    port_list = target_cell.instance.split()
    circuit_name = port_list.pop(-1)
    tmp_line = port_list.pop(0)
    for port in port_list:
        # match tmp_array and harness 
        # check target inport
        is_matched = 0
        if port == target_harness.target_in_port:
            tmp_line += ' IN'
            is_matched += 1
        # search stable inport
        for stable_port, state in zip(target_harness.stable_in_ports, target_harness.stable_in_port_states):
            if port == stable_port:
                if state == 1:
                    tmp_line += ' HIGH'
                    is_matched += 1
                elif state == 0:
                    tmp_line += ' LOW'
                    is_matched += 1
                else:
                    raise ValueError(f'Invalid state for port {port}')
        # check target outport
        if port == target_harness.target_out_port:
            tmp_line += ' OUT'
            is_matched += 1
        # search non-target outports
        for nontarget_port, state in zip(target_harness.nontarget_out_ports, target_harness.nontarget_out_port_states):
            if port == nontarget_port:
                tmp_line += f' WFLOAT{str(state)}'
                is_matched += 1
        if port.upper() == target_lib.vdd.name.upper():
                tmp_line += f' {port.upper()}'
                is_matched += 1
        if port.upper() == target_lib.vss.name.upper():
                tmp_line += f' {port.upper()}'
                is_matched += 1
        if port.upper() == target_lib.pwell.name.upper():
                tmp_line += f' {port.upper()}'
                is_matched += 1
        if port.upper() == target_lib.nwell.name.upper():
                tmp_line += f' {port.upper()}'
                is_matched += 1
        ## show error if this port has not matched
        if not is_matched:
            raise ValueError(f"Port {str(port)} not found in netlist")
    tmp_line += f" {circuit_name}\n"
    outlines.append(tmp_line)
    outlines.append(".ends \n")
    outlines.append(" \n")
    outlines.append(f".param cap ={str(out_load*target_lib.units.capacitance.magnitude)}\n")
    in_slope_mag = 1 / (target_lib.logic_threshold_high - target_lib.logic_threshold_low)
    outlines.append(f".param slew ={str(in_slope*in_slope_mag*target_lib.units.time.magnitude)}\n")
    outlines.append(".end \n")
    
    with open(spicef,'w') as f:
        f.writelines(outlines)
        f.close()

    spicelis = spicef + ".lis"
    spicerun = spicef + ".run"

    if 'ngspice' in str(target_lib.simulator):
        cmd = f'{str(target_lib.simulator.resolve())} -b {str(spicef)} 1> {str(spicelis)} 2> /dev/null \n'
    elif 'hspice' in str(target_lib.simulator):
        cmd = f'{str(target_lib.simulator.resolve())} {str(spicef)} -o {str(spicelis)} 2> /dev/null \n'

    with open(spicerun,'w') as f:
        outlines = []
        outlines.append(cmd) 
        f.writelines(outlines)
        f.close()

    # run spice simulation
    cmd = ['sh', spicerun]
    if target_lib.run_sim:
        try:
            subprocess.run(cmd)
        except:
            print ("Failed to launch spice")

    # read results from lis file
    results = {}
    desired_measurements = [
        'prop_in_out',
        'trans_out',
    ]
    if meas_energy:
        desired_measurements += ['q_in_dyn', 'q_out_dyn', 'q_vdd_dyn', 'q_vss_dyn', 'i_vdd_leak', 'i_vss_leak', 'i_in_leak']
    else:
        desired_measurements += ['energy_start', 'energy_end']
    with open(spicelis,'r') as f:
        for inline in f:
            if any([f in inline for f in ['failed', 'Error']]):
                raise NameError(f'An error occurred while running simulation. See {spicelis}.')
            if 'hspice' in str(target_lib.simulator):
                inline = re.sub('\=',' ',inline)
            measurement = next((m for m in desired_measurements if m in inline), False)
            if measurement:
                results[measurement] = float(inline.split()[2])
        f.close()

    return results
