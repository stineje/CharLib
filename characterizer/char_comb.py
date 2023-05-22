import re, subprocess

def runCombinationalDelay(target_lib, target_cell, target_harness, spice_filename, in_slew, out_load):
    spice_results_filename = str(spice_filename)+"_"+str(out_load)+"_"+str(in_slew)

    ## 1st trial, extract energy_start and energy_end
    trial_results = runCombinationalTrial(target_lib, target_cell, target_harness, in_slew, out_load, spice_results_filename)
    energy_start = trial_results['energy_start']
    energy_end = trial_results['energy_end']

    ## 2nd trial
    trial_results = runCombinationalTrial(target_lib, target_cell, target_harness, in_slew, out_load, spice_results_filename, energy_start, energy_end)
    trial_results['energy_start'] = energy_start
    trial_results['energy_end'] = energy_end

    if not target_harness.results.get(str(in_slew)):
        target_harness.results[str(in_slew)] = {}
    target_harness.results[str(in_slew)][str(out_load)] = trial_results

def runCombinationalTrial(target_lib, target_cell, target_harness, in_slew, out_load, output_filename: str, *energy):
    print(f'Running {output_filename}')
    outlines = [
        f'*title: delay meas.\n',
        f'.option brief nopage nomod post=1 ingold=2 autostop\n',
        f".inc '../{target_cell.model}'\n",
        f".inc '../{str(target_cell.netlist)}'\n",
        f'.temp {str(target_lib.temperature)}\n',
        f'.param _vdd = {str(target_lib.vdd.voltage)}\n',
        f'.param _vss = {str(target_lib.vss.voltage)}\n',
        f'.param _vnw = {str(target_lib.nwell.voltage)}\n',
        f'.param _vpw = {str(target_lib.pwell.voltage)}\n',
        f'.param cap = 10f\n', # TODO: is this correct?
        f'.param slew = 100p \n', # TODO: is this correct?
        f'.param _tslew = slew\n',
        f'.param _tstart = slew\n',
        f".param _tend = '_tstart + _tslew'\n",
        f".param _tsimend = '_tslew * 10000'\n",
        f'.param _Energy_meas_end_extent = {str(target_lib.energy_meas_time_extent)}\n\n',
        f"VDD_DYN VDD_DYN 0 DC '_vdd'\n",
        f"VSS_DYN VSS_DYN 0 DC '_vss'\n",
        f"VNW_DYN VNW_DYN 0 DC '_vnw'\n",
        f"VPW_DYN VPW_DYN 0 DC '_vpw'\n",
        f'* output load calculation\n',
        f'VOCAP VOUT WOUT DC 0\n',
        f"VDD_LEAK VDD_LEAK 0 DC '_vdd'\n",
        f"VSS_LEAK VSS_LEAK 0 DC '_vss'\n",
        f"VNW_LEAK VNW_LEAK 0 DC '_vnw'\n",
        f"VPW_LEAK VPW_LEAK 0 DC '_vpw'\n\n",
    ]
    ## in auto mode, simulation timestep is 1/10 of min. input slew
    ## simulation runs 1000x of input slew time
    outlines.append(f".tran {target_cell.sim_timestep}{str(target_lib.units.time)} '_tsimend' \n\n")

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
    if not energy:
        outlines.append("* For energy calculation \n")
        outlines.append(f".measure Tran ENERGY_START when v(VIN)='{str(target_lib.energy_meas_low_threshold_voltage())}' {target_harness.in_direction}=1\n")
        outlines.append(f".measure Tran ENERGY_END when v(VOUT)='{str(target_lib.energy_meas_high_threshold_voltage())}' {target_harness.out_direction}=1\n")

    ## energy measurement 
    elif energy:
        outlines.append(f'.param ENERGY_START = {energy[0]}\n')
        outlines.append(f'.param ENERGY_END = {energy[1]}\n')
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

    outlines.append("XINV VIN VOUT VHIGH VLOW VDD_DYN VSS_DYN VNW_DYN VPW_DYN DUT \n")
    outlines.append("C0 WOUT VSS_DYN 'cap'\n")
    outlines.append(" \n")
    outlines.append(".SUBCKT DUT IN OUT HIGH LOW VDD VSS VNW VPW \n")

    # parse subckt definition
    port_list = target_cell.instance.split()
    circuit_name = port_list.pop(-1)
    tmp_line = port_list.pop(0)
    for port in port_list:
        # Check target inport
        is_matched = 0
        if port == target_harness.target_in_port:
            tmp_line += ' IN'
            is_matched += 1
        # Check stable inport
        for stable_port, state in zip(target_harness.stable_in_ports, target_harness.stable_in_port_states):
            if port == stable_port:
                if state == '1':
                    tmp_line += ' HIGH'
                    is_matched += 1
                elif state == '0':
                    tmp_line += ' LOW'
                    is_matched += 1
                else:
                    raise ValueError(f'Invalid state for port {port}: {state}')
        # Check target outport
        if port == target_harness.target_out_port:
            tmp_line += ' OUT'
            is_matched += 1
        # Check non-target outports
        for nontarget_port, state in zip(target_harness.nontarget_out_ports, target_harness.nontarget_out_port_states):
            if port == nontarget_port:
                tmp_line += f' WFLOAT{str(state)}'
                is_matched += 1
        # Check VDD, VSS, VNW, and VPW
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
            raise ValueError(f"Port {port} not found in netlist")
    tmp_line += f" {circuit_name}\n"
    outlines.append(tmp_line)
    outlines.append(".ends \n")
    outlines.append(" \n")
    outlines.append(f".param cap ={out_load}{target_lib.units.capacitance.get_metric_prefix()}\n")
    in_slew_mag = 1 / (target_lib.logic_threshold_high - target_lib.logic_threshold_low)
    outlines.append(f".param slew ={in_slew*in_slew_mag}{target_lib.units.time.get_metric_prefix()}\n")
    outlines.append(".end \n")
    
    with open(f'{output_filename}.sp', 'w') as f:
        f.writelines(outlines)
        f.close()

    if 'ngspice' in str(target_lib.simulator):
        cmd = f'{str(target_lib.simulator.resolve())} -b {output_filename}.sp 1> {output_filename}.lis 2> /dev/null \n'
    elif 'hspice' in str(target_lib.simulator):
        cmd = f'{str(target_lib.simulator.resolve())} {output_filename}.sp -o {output_filename}.lis 2> /dev/null \n'

    with open(f'{output_filename}.run', 'w') as f:
        outlines = []
        outlines.append(cmd)
        f.writelines(outlines)
        f.close()

    # run spice simulation
    cmd = ['sh', f'{output_filename}.run']
    if target_lib.run_sim:
        subprocess.run(cmd)

    # read results from lis file
    results = {}
    desired_measurements = ['prop_in_out', 'trans_out']
    if energy:
        desired_measurements += ['q_in_dyn', 'q_out_dyn', 'q_vdd_dyn', 'q_vss_dyn', 'i_vdd_leak', 'i_vss_leak', 'i_in_leak']
    else:
        desired_measurements += ['energy_start', 'energy_end']
    with open(f'{output_filename}.lis', 'r') as f:
        for inline in f:
            if any([f in inline for f in ['failed', 'Error']]):
                raise NameError(f'An error occurred while running simulation. See {output_filename}.lis')
            if 'hspice' in str(target_lib.simulator):
                inline = re.sub('\=',' ',inline)
            measurement = next((m for m in desired_measurements if m in inline), False)
            if measurement:
                results[measurement] = float(inline.split()[2])
        f.close()

    return results
