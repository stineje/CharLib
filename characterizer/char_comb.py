import re, subprocess, sys, threading 

from characterizer.LibrarySettings import LibrarySettings
from characterizer.LogicCell import LogicCell
from characterizer.Harness import CombinationalHarness
from characterizer.HarnessSettings import HarnessSettings

def runCombinational(target_lib: LibrarySettings, target_cell: LogicCell, expectationList, unate):
    """Run delay characterization for an N-input 1-output combinational cell"""
    harnesses = [] # One harness for each trial

    for test_vector in expectationList:
        # Generate harness
        harness = CombinationalHarness(target_cell, test_vector, unate)
        
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
        harnesses.append(harness)
        target_cell.harnesses.append(harnesses) #TODO: Try deindenting this

    # This should be calculated by the cell instead
    #target_cell.set_cin_avg(target_lib)

def runSpiceCombDelayMultiThread(targetLib, targetCell, targetHarness, spicef):
    # One trial for each input slope / output load combination
    thread_id = 0
    threadlist = []
    for tmp_slope in targetCell.in_slopes:
        for tmp_load in targetCell.out_loads:
            thread = threading.Thread(target=runSpiceCombDelaySingle,
                    args=([targetLib, targetCell, targetHarness, spicef, tmp_slope, tmp_load]),
                    name="%d" % thread_id)
            threadlist.append(thread)
            thread_id += 1
    for thread in threadlist:
        thread.start() 
    for thread in threadlist:
        thread.join() 

    # These calculations should be performed by Harness instead
    # thread_id = 0
    # for tmp_slope in targetCell.in_slopes:
    #     tmp_list_prop =   []
    #     tmp_list_tran =   []
    #     tmp_list_estart = []
    #     tmp_list_eend =   []
    #     tmp_list_eintl =   []
    #     tmp_list_ein =   []
    #     tmp_list_cin =   []
    #     tmp_list_pleak =   []
    #     for tmp_load in targetCell.out_loads:
    #         #print(str(thread_id))
    #         #print(str(results_prop_in_out))
    #         #print(str(results_prop_in_out[str(thread_id)]))
    #         tmp_list_prop.append(results_prop_in_out[str(thread_id)])
    #         tmp_list_tran.append(results_trans_out[str(thread_id)])

    #         ## intl. energy calculation
    #         ## intl. energy is the sum of short-circuit energy and drain-diffusion charge/discharge energy
    #         ## larger Ql: intl. Q, load Q 
    #         ## smaller Qs: intl. Q
    #         ## Eintl = QsV
    #         if abs(results_q_vdd_dyn[str(thread_id)]) < abs(results_q_vss_dyn[str(thread_id)]):
    #             res_q = results_q_vdd_dyn[str(thread_id)]
    #         else:
    #             res_q = results_q_vss_dyn[str(thread_id)]
    #         tmp_list_eintl.append(abs(res_q*targetLib.vdd.voltage*targetLib.energy_meas_high_threshold \
    #             - abs((results_energy_end[str(thread_id)] - results_energy_start[str(thread_id)])*(abs(results_i_vdd_leak[str(thread_id)]) \
    #             + abs(results_i_vdd_leak[str(thread_id)]))/2*(targetLib.vdd.voltage*targetLib.energy_meas_high_threshold))))

    #         ## input energy
    #         tmp_list_ein.append(abs(results_q_in_dyn[str(thread_id)])*targetLib.vdd.voltage)

    #         ## Cin = Qin / V
    #         tmp_list_cin.append(abs(results_q_in_dyn[str(thread_id)])/(targetLib.vdd.voltage))

    #         ## Pleak = average of Pleak_vdd and Pleak_vss
    #         ## P = I * V
    #         tmp_list_pleak.append((abs(results_i_vdd_leak[str(thread_id)])+abs(results_i_vdd_leak[str(thread_id)]))/2*(targetLib.vdd.voltage)) #
    #         thread_id += 1

    #     list2_prop.append(tmp_list_prop)
    #     list2_tran.append(tmp_list_tran)
    #     #list2_estart.append(tmp_list_estart)
    #     #list2_eend.append(tmp_list_eend)
    #     list2_eintl.append(tmp_list_eintl)
    #     list2_ein.append(tmp_list_ein)
    #     list2_cin.append(tmp_list_cin)
    #     list2_pleak.append(tmp_list_pleak)

def runSpiceCombDelaySingle(targetLib: LibrarySettings, targetCell: LogicCell, targetHarness: CombinationalHarness, spicef, tmp_slope, tmp_load):

    print("start thread :"+str(threading.current_thread().name))
    spicefo = str(spicef)+"_"+str(tmp_load)+"_"+str(tmp_slope)+".sp"

    ## 1st trial, extract energy_start and energy_end
    trial_results = genFileLogic_trial1(targetLib, targetCell, targetHarness, 0, tmp_slope, tmp_load, "none", "none", spicefo)
    energy_start = trial_results['energy_start']
    energy_end = trial_results['energy_end']
    estart_line = ".param ENERGY_START = "+str(energy_start)+"\n"
    eend_line = ".param ENERGY_END = "+str(energy_end)+"\n"

    ## 2nd trial
    trial_results = genFileLogic_trial1(targetLib, targetCell, targetHarness, 1, tmp_slope, tmp_load, estart_line, eend_line, spicefo)
    trial_results['energy_start'] = energy_start
    trial_results['energy_end'] = energy_end

    print("end thread :"+str(threading.current_thread().name))
    targetHarness.results.append(trial_results)

def runSpiceCombDelay(targetLib: LibrarySettings, targetCell: LogicCell, targetHarness: CombinationalHarness, spicef):
    # Test each input slope with each output load
    for tmp_slope in targetCell.in_slopes:
        for tmp_load in targetCell.out_loads:
            spicefo = str(spicef)+"_"+str(tmp_load)+"_"+str(tmp_slope)+".sp"

            ## 1st trial, extract energy_start and energy_end
            trial_results = genFileLogic_trial1(targetLib, targetCell, targetHarness, 0, tmp_slope, tmp_load, "none", "none", spicefo)
            energy_start = trial_results['energy_start']
            energy_end = trial_results['energy_end']
            estart_line = ".param ENERGY_START = "+str(energy_start)+"\n"
            eend_line = ".param ENERGY_END = "+str(energy_end)+"\n"

            ## 2nd trial
            trial_results = genFileLogic_trial1(targetLib, targetCell, targetHarness, 1, tmp_slope, tmp_load, estart_line, eend_line, spicefo)
            trial_results['energy_start'] = energy_start
            trial_results['energy_end'] = energy_end

            targetHarness.results.append(trial_results)

def genFileLogic_trial1(targetLib: LibrarySettings, targetCell: LogicCell, targetHarness: CombinationalHarness, meas_energy: bool, in_slope, out_load, estart_line, eend_line, spicef: str):
    outlines = []
    outlines.append("*title: delay meas.\n")
    outlines.append(".option brief nopage nomod post=1 ingold=2 autostop\n")
    outlines.append(f".inc '../{targetCell.model}'\n")
    outlines.append(f".inc '../{str(targetCell.netlist)}'\n")
    outlines.append(f".temp {str(targetLib.temperature)}\n")
    outlines.append(f".param _vdd = {str(targetLib.vdd.voltage)}\n")
    outlines.append(f".param _vss = {str(targetLib.vss.voltage)}\n")
    outlines.append(f".param _vnw = {str(targetLib.nwell.voltage)}\n")
    outlines.append(f".param _vpw = {str(targetLib.pwell.voltage)}\n")
    outlines.append(".param cap = 10f \n") # TODO: is this correct?
    outlines.append(".param slew = 100p \n") # TODO: is this correct?
    outlines.append(".param _tslew = slew\n")
    outlines.append(".param _tstart = slew\n")
    outlines.append(".param _tend = '_tstart + _tslew'\n")
    outlines.append(".param _tsimend = '_tslew * 10000' \n")
    outlines.append(f".param _Energy_meas_end_extent = {str(targetLib.energy_meas_time_extent)}\n")
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
    outlines.append(f".tran {str(targetCell.sim_timestep)}{str(targetLib.units.time)} '_tsimend'\n")
    outlines.append(" \n")

    if targetHarness.in_direction == 'rise':
        outlines.append("VIN VIN 0 PWL(1p '_vss' '_tstart' '_vss' '_tend' '_vdd' '_tsimend' '_vdd') \n")
    elif targetHarness.in_direction == 'fall':
        outlines.append("VIN VIN 0 PWL(1p '_vdd' '_tstart' '_vdd' '_tend' '_vss' '_tsimend' '_vss') \n")
    outlines.append("VHIGH VHIGH 0 DC '_vdd' \n")
    outlines.append("VLOW VLOW 0 DC '_vss' \n")

    ##
    ## delay measurement 
    outlines.append("** Delay \n")
    outlines.append("* Prop delay \n")
    outlines.append(f".measure Tran PROP_IN_OUT trig v(VIN) val='{str(targetLib.logic_low_to_high_threshold_voltage())}' {targetHarness.in_direction}=1\n")
    outlines.append(f"+ targ v(VOUT) val='{str(targetLib.logic_high_to_low_threshold_voltage())}' {targetHarness.out_direction}=1\n")
    outlines.append("* Trans delay \n")
    outlines.append(f".measure Tran TRANS_OUT trig v(VOUT) val='{str(targetLib.logic_threshold_high_voltage())}' {targetHarness.out_direction}=1\n")
    outlines.append(f"+ targ v(VOUT) val='{str(targetLib.logic_threshold_low_voltage())}' {targetHarness.out_direction}=1\n")

    # get ENERGY_START and ENERGY_END for energy calculation in 2nd round 
    if not meas_energy:
        outlines.append("* For energy calculation \n")
        outlines.append(f".measure Tran ENERGY_START when v(VIN)='{str(targetLib.energy_meas_low_threshold_voltage())}' {targetHarness.in_direction}=1\n")
        outlines.append(f".measure Tran ENERGY_END when v(VOUT)='{str(targetLib.energy_meas_high_threshold_voltage())}' {targetHarness.out_direction}=1\n")

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
    port_list = targetCell.instance.split()
    circuit_name = port_list.pop(-1)
    tmp_line = port_list.pop(0)
    for port in port_list:
        # match tmp_array and harness 
        # search target inport
        is_matched = 0
        if port == targetHarness.target_in_port:
            tmp_line += ' IN'
            is_matched += 1
        # search stable inport
        for stable_port, state in zip(targetHarness.stable_in_ports, targetHarness.stable_in_port_states):
            if port == stable_port:
                if state == 1:
                    tmp_line += ' HIGH'
                    is_matched += 1
                elif state == 0:
                    tmp_line += ' LOW'
                    is_matched += 1
                else:
                    raise ValueError(f'Invalid state for port {port}')
        # one target outport for one simulation
        if port == targetHarness.target_out_port:
            tmp_line += ' OUT'
            is_matched += 1
        # search non-target outport
        # TODO
        # for w2 in targetHarness.nontarget_out_ports:
        #     if port == w2:
        #         # this is non-target outport
        #         # search outdex for this port
        #         index_val = targetHarness.nontarget_out_port_states[targetHarness.nontarget_out_ports.index(w2)]
        #         tmp_line += f' WFLOAT{str(index_val)}'
        #         is_matched += 1
        if port.upper() == targetLib.vdd.name.upper():
                tmp_line += f' {port.upper()}'
                is_matched += 1
        if port.upper() == targetLib.vss.name.upper():
                tmp_line += f' {port.upper()}'
                is_matched += 1
        if port.upper() == targetLib.pwell.name.upper():
                tmp_line += f' {port.upper()}'
                is_matched += 1
        if port.upper() == targetLib.nwell.name.upper():
                tmp_line += f' {port.upper()}'
                is_matched += 1
        ## show error if this port has not matched
        if not is_matched:
            raise ValueError(f"Port {str(port)} not found in netlist")
    tmp_line += f" {circuit_name}\n"
    outlines.append(tmp_line)
    outlines.append(".ends \n")
    outlines.append(" \n")
    outlines.append(f".param cap ={str(out_load*targetLib.units.capacitance.magnitude)}\n")
    in_slope_mag = 1 / (targetLib.logic_threshold_high - targetLib.logic_threshold_low)
    outlines.append(f".param slew ={str(in_slope*in_slope_mag*targetLib.units.time.magnitude)}\n")
    outlines.append(".end \n")
    
    with open(spicef,'w') as f:
        f.writelines(outlines)
        f.close()

    spicelis = spicef + ".lis"
    spicerun = spicef + ".run"

    if 'ngspice' in str(targetLib.simulator):
        cmd = f'{str(targetLib.simulator.resolve())} -b {str(spicef)} 1> {str(spicelis)} 2> /dev/null \n'
    elif 'hspice' in str(targetLib.simulator):
        cmd = f'{str(targetLib.simulator.resolve())} {str(spicef)} -o {str(spicelis)} 2> /dev/null \n'
    with open(spicerun,'w') as f:
        outlines = []
        outlines.append(cmd) 
        f.writelines(outlines)
        f.close()

    # run spice simulation
    cmd = ['sh', spicerun]
    if targetLib.run_sim:
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
            if any([x in inline for x in ['failed', 'Error']]):
                pass # TODO: fail with error
            if 'hspice' in str(targetLib.simulator):
                inline = re.sub('\=',' ',inline)
            measurement = next((m for m in desired_measurements if m in inline), False)
            if measurement:
                results[measurement] = '{:e}'.format(float(inline.split()[2]))
        f.close()
    return results
