import re, os, subprocess

import numpy as np
from characterizer.CharacterizerSettings import CharacterizerSettings
from characterizer.myFunc import my_exit

def runFlop(targetLib, targetCell, expectationList2):
    harnessList = []   # harness for each trial
    harnessList2 = []  # list of harnessList

    D_val = None
    CLK_val = None
    SET_val = None
    RST_val = None
    Q_val = None

    for trial in range(len(expectationList2)):
        tmp_Harness = CharacterizerSettings() 
        if(targetCell.logic == 'DFF_PCPU_NRNS'):
            D_val, CLK_val, SET_val, RST_val, Q_val = expectationList2[trial]
        elif(targetCell.logic == 'DFF_PCPU_NR'):
            D_val, CLK_val, RST_val, Q_val = expectationList2[trial]
        elif(targetCell.logic == 'DFF_PCPU'):
            D_val, CLK_val, Q_val = expectationList2[trial]
        else:
            targetLib.print_error("Error! target cell "+str(targetCell.logic)+" is not defined!")

        ## 
        ## replace Q_val for recovery/removal
        ##
        if((SET_val == '01') or (SET_val == '10') or (RST_val == '01') or (RST_val == '10')):
            if(Q_val == '01'):
                Q_val = '10'
            elif(Q_val == '10'):
                Q_val = '01'
            

        tmp_Harness.set_target_inport (targetCell.inports[0], D_val)
        tmp_Harness.set_target_outport (targetCell.outports[0], targetCell.functions[0], Q_val)
        tmp_Harness.set_direction(Q_val)
        tmp_Harness.set_target_clock (targetCell.clock, CLK_val)
        #tmp_Harness.set_nontarget_outport (targetCell.outports[1])
        #tmp_Harness.set_timing_flop_clock(CLK_val)


        # activate RST and SET if defined
        #targetLib.print_msg("RST:"+str(RST_val))
        #targetLib.print_msg("SET:"+str(SET_val))
        if((RST_val != None)and(SET_val != None)):
            tmp_Harness.set_target_set (targetCell.set, SET_val)
            tmp_Harness.set_target_reset (targetCell.reset, RST_val)
            spicef = "c2q1_"+str(targetCell.cell)+"_"\
                    +str(targetCell.inports[0])+str(D_val)+"_"\
                    +str(targetCell.clock)+str(CLK_val)+"_"\
                    +str(targetCell.set)+str(SET_val)+"_"\
                    +str(targetCell.reset)+str(RST_val)+"_"\
                    +str(targetCell.outports[0])+str(Q_val)
        elif(SET_val != None):
            tmp_Harness.set_target_set (targetCell.set, SET_val)
            spicef = "c2q1_"+str(targetCell.cell)+"_"\
                    +str(targetCell.inports[0])+str(D_val)+"_"\
                    +str(targetCell.clock)+str(CLK_val)+"_"\
                    +str(targetCell.set)+str(SET_val)+"_"\
                    +str(targetCell.outports[0])+str(Q_val)
        elif(RST_val != None):
            tmp_Harness.set_target_reset (targetCell.reset, RST_val)
            spicef = "c2q1_"+str(targetCell.cell)+"_"\
                    +str(targetCell.inports[0])+str(D_val)+"_"\
                    +str(targetCell.clock)+str(CLK_val)+"_"\
                    +str(targetCell.reset)+str(RST_val)+"_"\
                    +str(targetCell.outports[0])+str(Q_val)
        else:	
            spicef = "c2q1_"+str(targetCell.cell)+"_"\
                    +str(targetCell.inports[0])+str(D_val)+"_"\
                    +str(targetCell.clock)+str(CLK_val)+"_"\
                    +str(targetCell.outports[0])+str(Q_val)

        # select simulation type: clock(D2Q, D2C, C2Q, C2D), reset, set
        # normal operation (clock edge)
        if((D_val == '01') or (D_val == '10')):
            tmp_Harness.set_timing_flop_inout(D_val, CLK_val, Q_val)
            targetLib.print_msg_sim("D2Q simualtion mode!\n")
            # run spice and store result
            if(targetLib.mtsim == "true"):
                runSpiceFlopDelayMT(targetLib, targetCell, tmp_Harness, spicef)
            else:
                runSpiceFlopDelay(targetLib, targetCell, tmp_Harness, spicef)
        # reset operation (reset edge)
        elif((RST_val == '01') or (RST_val == '10')):
            tmp_Harness.set_timing_flop_reset(targetCell, RST_val, Q_val)
            targetLib.print_msg_sim("R2Q simualtion mode!\n")
            # run spice and store result
            runSpiceFlopRecoveryRemoval(targetLib, targetCell, tmp_Harness, spicef)
        # set operation (set edge)
        elif((SET_val == '01') or (SET_val == '10')):
            tmp_Harness.set_timing_flop_set(targetCell, SET_val, Q_val)
            targetLib.print_msg_sim("S2Q simualtion mode!\n")
            # run spice and store result
            runSpiceFlopRecoveryRemoval(targetLib, targetCell, tmp_Harness, spicef)
        else:
            print("no suported input vector is inputted! error\n")
            print("CLK: "+CLK_val+"\n")
            print("D: "+D_val+"\n")
            print("SET: "+SET_val+"\n")
            print("RST: "+RST_val+"\n")
            my_exit()
        harnessList.append(tmp_Harness)
        harnessList2.append(harnessList)

        ## select cin in simulation: clock(D2Q, D2C, C2Q, C2D), reset, set
        ## normal operation (clock edge)
        if((D_val == '01') or (D_val == '10')):
            ## set cin for clock
            targetCell.set_cin_avg(targetLib, harnessList, "clk")
            ## set cin for data
            targetCell.set_cin_avg(targetLib, harnessList) 
        ## reset operation (reset edge)
        elif((RST_val == '01') or (RST_val == '10')):
            targetCell.set_cin_avg(targetLib, harnessList, "rst")
        ## set operation (set edge)
        elif((SET_val == '01') or (SET_val == '10')):
            targetCell.set_cin_avg(targetLib, harnessList, "set")
        else:
            targetLib.print_error("any input vector is inputted! error\n")

    return harnessList2

def runSpiceFlopDelay(targetLib, targetCell, targetHarness, spicef):
    list2_prop =   []
    list2_setup =   []
    list2_hold =   []
    list2_tran =   []
    list2_estart = []
    list2_eend =   []
    list2_eintl =   []
    list2_ein =   []
    list2_cin =   []
    list2_eclk =   []
    list2_cclk =   []
    list2_pleak =   []
    for tmp_slope in targetCell.slope:
        res_list_prop =   []  # C2Q
        res_list_setup =  []  # D2C(setup)
        res_list_hold =   []  # C2D(hold)
        res_list_tran =   []
        res_list_estart = []
        res_list_eend =   []
        res_list_eintl =   []
        res_list_ein =   []
        res_list_cin =   []
        res_list_eclk =   []
        res_list_cclk =   []
        res_list_pleak =   []

        for tmp_load in targetCell.load:
            tmp_max_val_loop = float(targetCell.slope[-1]) * 10 # use x10 of max. slope for max val.
            tmp_min_setup = tmp_max_val_loop # temporal value for setup 
            tmp_tsetup1 = tmp_max_val_loop # temporal value for setup 
            tmp_tsetup2 = tmp_max_val_loop # temporal value for setup 
            tmp_tsetup3 = tmp_max_val_loop # temporal value for setup 
            tmp_thold1 = tmp_max_val_loop # temporal value for setup 
            tmp_thold2 = tmp_max_val_loop # temporal value for setup 
            tmp_min_hold  = tmp_max_val_loop # temporal value for setup 

            # C2Q and setup search (sparce)
            # perform two-stage simulation
            # 1st stage: sim w/  10-% output swing
            # 2nd stage: sim w/ 100-% output swing
            tsimendmag = [1, 10]; # magnify parameter of _tsimend
            tranmag = [float(targetLib.logic_threshold_low)*1.1, 1];         # magnify parameter of transient simulation
            tmp_min_prop_in_out   = tmp_max_val_loop # temporal value for D2Qmin search
            tmp_min_prop_cin_out  = tmp_max_val_loop # temporal value for D2Qmin search
            tmp_min_trans_out     = tmp_max_val_loop # temporal value for D2Qmin search
            tmp_energy_start  = tmp_max_val_loop # temporal value for D2Qmin search
            tmp_energy_end    = tmp_max_val_loop # temporal value for D2Qmin search
            tmp_energy_clk_start  = tmp_max_val_loop # temporal value for D2Qmin search
            tmp_energy_clk_end    = tmp_max_val_loop # temporal value for D2Qmin search

            tmp_tstep_mag = 20
            tmp_tstep_mag1 = float(targetCell.slope[-1])/float(targetCell.slope[0])* tmp_tstep_mag
            targetLib.print_msg_sim("First stage sparse setup search, timestep: "\
                +str(targetCell.sim_setup_timestep*tmp_tstep_mag1))
            ( tmp_tsetup1, tmp_min_prop_in_out, _, _, _, tmp_min_trans_out, \
                tmp_energy_start, tmp_energy_end, _, _, _, _, _, _, _, _, _, _) \
             = setupSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    targetCell.sim_setup_lowest, targetCell.sim_setup_highest, \
                                                                    targetCell.sim_setup_timestep*tmp_tstep_mag1, tmp_min_hold, 5, spicef)

            tmp_tstep_mag = 2
            tmp_tstep_mag2 = tmp_tstep_mag1 
            tmp_tstep_mag1 = tmp_tstep_mag1 / tmp_tstep_mag
            targetLib.print_msg_sim("First stage sparse setup search, timestep: "\
                +str(targetCell.sim_setup_timestep*tmp_tstep_mag1))
            ( tmp_tsetup1, tmp_min_prop_in_out, _, _, _, tmp_min_trans_out, \
                tmp_energy_start, tmp_energy_end, _, _, _, _, _, _, _, _, _, _) \
             = setupSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    tmp_tsetup1 - targetCell.sim_setup_timestep * tmp_tstep_mag2 *1,\
                                                                    tmp_tsetup1 + targetCell.sim_setup_timestep * tmp_tstep_mag2 *2,\
                                                                    targetCell.sim_setup_timestep * tmp_tstep_mag1, tmp_min_hold, 3, spicef)

            while(tmp_tstep_mag1 > tmp_tstep_mag ):
                tmp_tstep_mag2 = tmp_tstep_mag1 
                tmp_tstep_mag1 = tmp_tstep_mag1 / tmp_tstep_mag
                targetLib.print_msg_sim("Mid. stage precise setup search, timestep: "\
                    +str(targetCell.sim_setup_timestep*tmp_tstep_mag1))
                ( tmp_tsetup1, tmp_min_prop_in_out, _, _, _, tmp_min_trans_out, \
                    tmp_energy_start, tmp_energy_end, _, _, _, _, _, _, _, _, _, _) \
                 = setupSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                        tmp_tsetup1 - targetCell.sim_setup_timestep * tmp_tstep_mag2  *1,\
                                                                        tmp_tsetup1 + targetCell.sim_setup_timestep * tmp_tstep_mag2  *3,\
                                                                        targetCell.sim_setup_timestep * tmp_tstep_mag1, tmp_min_hold, 3, spicef)

            targetLib.print_msg_sim("Last stage precise setup search, timestep: "\
                +str(targetCell.sim_setup_timestep))
            ( tmp_tsetup3, tmp_min_prop_in_out, _, _, _, tmp_min_trans_out, \
                tmp_energy_start, tmp_energy_end, _, _, _, _, _, _, _, _, _, _) \
             = setupSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    tmp_tsetup1 - targetCell.sim_setup_timestep * tmp_tstep_mag2 *1,\
                                                                    tmp_tsetup1 + targetCell.sim_setup_timestep * tmp_tstep_mag2 *3,\
                                                                    targetCell.sim_setup_timestep, tmp_min_hold, 2, spicef)
            
            ## if target is D2Q, do standard setup/hold search
            #if((targetHarness.target_inport_val == "01")or(targetHarness.target_inport_val == "10")):
            tmp_tstep_mag = 20
            tmp_tstep_mag1 = float(targetCell.slope[-1])/float(targetCell.slope[0])* tmp_tstep_mag
            targetLib.print_msg_sim("First stage sparse hold search, timestep: "\
                +str(targetCell.sim_hold_timestep*tmp_tstep_mag1))
            ( tmp_thold1, tmp_min_prop_in_out,tmp_min_prop_cin_out, tmp_min_setup, tmp_min_hold, tmp_min_trans_out, \
                tmp_energy_start, tmp_energy_end, tmp_energy_clk_start, tmp_energy_clk_end, \
                tmp_q_in_dyn, tmp_q_out_dyn, tmp_q_clk_dyn, tmp_q_vdd_dyn, tmp_q_vss_dyn, \
                tmp_i_in_leak, tmp_i_vdd_leak, tmp_i_vss_leak) \
            = holdSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    targetCell.sim_hold_lowest, targetCell.sim_hold_highest, \
                                                                    targetCell.sim_hold_timestep*tmp_tstep_mag1, tmp_tsetup3, \
                                                                    3, spicef)

            tmp_tstep_mag = 2
            tmp_tstep_mag2 = tmp_tstep_mag1
            tmp_tstep_mag1 = tmp_tstep_mag1 /  tmp_tstep_mag
            targetLib.print_msg_sim("First stage sparse hold search, timestep: "\
                +str(targetCell.sim_setup_timestep*tmp_tstep_mag1))
            ( tmp_thold1, tmp_min_prop_in_out,tmp_min_prop_cin_out, tmp_min_setup, tmp_min_hold, tmp_min_trans_out, \
                tmp_energy_start, tmp_energy_end, tmp_energy_clk_start, tmp_energy_clk_end, \
                tmp_q_in_dyn, tmp_q_out_dyn, tmp_q_clk_dyn, tmp_q_vdd_dyn, tmp_q_vss_dyn, \
                tmp_i_in_leak, tmp_i_vdd_leak, tmp_i_vss_leak) \
             = holdSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    tmp_thold1 - targetCell.sim_hold_timestep * tmp_tstep_mag2 *2,\
                                                                    tmp_thold1 + targetCell.sim_hold_timestep * tmp_tstep_mag2 *1,\
                                                                    targetCell.sim_hold_timestep * tmp_tstep_mag1, tmp_tsetup3, 3, spicef)

            while(tmp_tstep_mag1 > tmp_tstep_mag ):
                tmp_tstep_mag2 = tmp_tstep_mag1
                tmp_tstep_mag1 = tmp_tstep_mag1 /  tmp_tstep_mag
                targetLib.print_msg_sim("Mid. stage precise hold search, timestep: "\
                    +str(targetCell.sim_setup_timestep*tmp_tstep_mag1))
                ( tmp_thold1, tmp_min_prop_in_out,tmp_min_prop_cin_out, tmp_min_setup, tmp_min_hold, tmp_min_trans_out, \
                    tmp_energy_start, tmp_energy_end, tmp_energy_clk_start, tmp_energy_clk_end, \
                    tmp_q_in_dyn, tmp_q_out_dyn, tmp_q_clk_dyn, tmp_q_vdd_dyn, tmp_q_vss_dyn, \
                    tmp_i_in_leak, tmp_i_vdd_leak, tmp_i_vss_leak) \
                 = holdSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                        tmp_thold1 - targetCell.sim_hold_timestep * tmp_tstep_mag2 *3 ,\
                                                                        tmp_thold1 + targetCell.sim_hold_timestep * tmp_tstep_mag2 *1 ,\
                                                                        targetCell.sim_hold_timestep * tmp_tstep_mag1, tmp_tsetup3, 3, spicef)

            targetLib.print_msg_sim("Last stage precise hold search, timestep: "\
                +str(targetCell.sim_hold_timestep))
            ( res_thold3, res_min_prop_in_out, res_min_prop_cin_out, res_min_setup, res_min_hold, res_min_trans_out, \
                res_energy_start, res_energy_end, tmp_energy_clk_start, tmp_energy_clk_end, \
                res_q_in_dyn, res_q_out_dyn, res_q_clk_dyn, res_q_vdd_dyn, res_q_vss_dyn, \
                res_i_in_leak, res_i_vdd_leak, res_i_vss_leak) \
             = holdSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    tmp_thold1 - targetCell.sim_hold_timestep * tmp_tstep_mag2 *3,\
                                                                    tmp_thold1 + targetCell.sim_hold_timestep * tmp_tstep_mag2 *1 ,\
                                                                    targetCell.sim_hold_timestep, tmp_tsetup3, 2, spicef)
            ## if target is not D2Q (= set or reset), clip lowest hold time to almost zero
            ## this is because removal simulation sometimes very small 

            # end setup/hold search
            #res_list_prop.append(res_min_prop_in_out) # store D2Q 
            res_list_prop.append(res_min_prop_cin_out) # store C2Q (not D2Q)
            res_list_tran.append(res_min_trans_out)
            res_list_setup.append(res_min_setup)
            res_list_hold.append(res_min_hold)
            print("Final C2Q: "+str(res_min_prop_cin_out)+",setup: "+str(res_min_setup)+", hold: "+str(res_min_hold))

            ## intl. energy calculation
            ## intl. energy is the sum of short-circuit energy and drain-diffusion charge/discharge energy
            ## larger Ql: intl. Q, load Q 
            ## smaller Qs: intl. Q
            ## Eintl = QsV
            if(abs(res_q_vdd_dyn) < abs(res_q_vss_dyn)):
                res_list_eintl.append(abs(res_q_vdd_dyn*targetLib.vdd_voltage*targetLib.energy_meas_high_threshold-\
                    abs((res_energy_end - res_energy_start)*(abs(res_i_vdd_leak)+abs(res_i_vdd_leak))/2* \
                    (targetLib.vdd_voltage*targetLib.energy_meas_high_threshold))))
            else:
                res_list_eintl.append(abs(res_q_vss_dyn*targetLib.vdd_voltage*targetLib.energy_meas_high_threshold-\
                    abs((res_energy_end - res_energy_start)*(abs(res_i_vdd_leak)+abs(res_i_vdd_leak))/2* \
                    (targetLib.vdd_voltage*targetLib.energy_meas_high_threshold))))

            ## input energy
            res_list_ein.append(abs(res_q_in_dyn)*targetLib.vdd_voltage)
            res_list_eclk.append(abs(res_q_clk_dyn)*targetLib.vdd_voltage)

            ## Cin = Qin / V
            res_list_cin.append(abs(res_q_in_dyn)/(targetLib.vdd_voltage))
            res_list_cclk.append(abs(res_q_clk_dyn)/(targetLib.vdd_voltage))

            ## Pleak = average of Pleak_vdd and Pleak_vss
            ## P = I * V
            res_list_pleak.append((abs(res_i_vdd_leak)+abs(res_i_vdd_leak))/2*(targetLib.vdd_voltage)) #

        list2_prop.append(res_list_prop)
        list2_tran.append(res_list_tran)
        list2_setup.append(res_list_setup)
        list2_hold.append(res_list_hold)
        #list2_estart.append(res_list_estart)
        #list2_eend.append(res_list_eend)
        list2_eintl.append(res_list_eintl)
        list2_ein.append(res_list_ein)
        list2_cin.append(res_list_cin)
        list2_eclk.append(res_list_eclk)
        list2_cclk.append(res_list_cclk)
        list2_pleak.append(res_list_pleak)

    targetHarness.set_list2_prop(list2_prop)
    #targetHarness.print_list2_prop(targetCell.load, targetCell.slope)
    targetHarness.write_list2_prop(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_prop()
    targetHarness.set_list2_tran(list2_tran)
    #targetHarness.print_list2_tran(targetCell.load, targetCell.slope)
    targetHarness.write_list2_tran(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_tran()
    targetHarness.set_list2_setup(list2_setup)
    #targetHarness.print_list2_setup(targetCell.load, targetCell.slope)
    targetHarness.write_list2_setup(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_setup()
    targetHarness.set_list2_hold(list2_hold)
    #targetHarness.print_list2_hold(targetCell.load, targetCell.slope)
    targetHarness.write_list2_hold(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_hold()
    targetHarness.set_list2_eintl(list2_eintl)
    #targetHarness.print_list2_eintl(targetCell.load, targetCell.slope)
    targetHarness.write_list2_eintl(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_eintl()
    targetHarness.set_list2_ein(list2_ein)
    #targetHarness.print_list2_ein(targetCell.load, targetCell.slope)
    targetHarness.write_list2_ein(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_ein()
    targetHarness.set_list2_cin(list2_cin)
    #targetHarness.print_list2_cin(targetCell.load, targetCell.slope)
    targetHarness.average_list2_cin(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_cin()
    targetHarness.set_list2_eclk(list2_eclk)
    #targetHarness.print_list2_eclk(targetCell.load, targetCell.slope)
    targetHarness.write_list2_eclk(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_eclk()
    targetHarness.set_list2_cclk(list2_cclk)
    #targetHarness.print_list2_cclk(targetCell.load, targetCell.slope)
    targetHarness.average_list2_cclk(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_cclk()
    targetHarness.set_list2_pleak(list2_pleak)
    #targetHarness.print_list2_pleak(targetCell.load, targetCell.slope)
    targetHarness.write_list2_pleak(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_pleak()


def runSpiceFlopDelayMT(targetLib, targetCell, targetHarness, spicef):
    list2_prop =   []
    list2_setup =   []
    list2_hold =   []
    list2_tran =   []
    list2_estart = []
    list2_eend =   []
    list2_eintl =   []
    list2_ein =   []
    list2_cin =   []
    list2_eclk =   []
    list2_cclk =   []
    list2_pleak =   []
    for tmp_slope in targetCell.slope:
        res_list_prop =   []  # C2Q
        res_list_setup =  []  # D2C(setup)
        res_list_hold =   []  # C2D(hold)
        res_list_tran =   []
        res_list_estart = []
        res_list_eend =   []
        res_list_eintl =   []
        res_list_ein =   []
        res_list_cin =   []
        res_list_eclk =   []
        res_list_cclk =   []
        res_list_pleak =   []

        for tmp_load in targetCell.load:
            tmp_max_val_loop = float(targetCell.slope[-1]) * 10 # use x10 of max. slope for max val.
            tmp_min_setup = tmp_max_val_loop # temporal value for setup 
            tmp_tsetup1 = tmp_max_val_loop # temporal value for setup 
            tmp_tsetup2 = tmp_max_val_loop # temporal value for setup 
            tmp_tsetup3 = tmp_max_val_loop # temporal value for setup 
            tmp_thold1 = tmp_max_val_loop # temporal value for setup 
            tmp_thold2 = tmp_max_val_loop # temporal value for setup 
            tmp_min_hold  = tmp_max_val_loop # temporal value for setup 

            # C2Q and setup search (sparce)
            # perform two-stage simulation
            # 1st stage: sim w/  10-% output swing
            # 2nd stage: sim w/ 100-% output swing
            tsimendmag = [1, 10]; # magnify parameter of _tsimend
            tranmag = [float(targetLib.logic_threshold_low)*1.1, 1];         # magnify parameter of transient simulation
            tmp_min_prop_in_out   = tmp_max_val_loop # temporal value for D2Qmin search
            tmp_min_prop_cin_out  = tmp_max_val_loop # temporal value for D2Qmin search
            tmp_min_trans_out     = tmp_max_val_loop # temporal value for D2Qmin search
            tmp_energy_start  = tmp_max_val_loop # temporal value for D2Qmin search
            tmp_energy_end    = tmp_max_val_loop # temporal value for D2Qmin search
            tmp_energy_clk_start  = tmp_max_val_loop # temporal value for D2Qmin search
            tmp_energy_clk_end    = tmp_max_val_loop # temporal value for D2Qmin search

            tmp_tstep_mag = 20
            tmp_tstep_mag1 = float(targetCell.slope[-1])/float(targetCell.slope[0])* tmp_tstep_mag
            targetLib.print_msg_sim("First stage sparse setup search, timestep: "\
                +str(targetCell.sim_setup_timestep*tmp_tstep_mag1))
            ( tmp_tsetup1, tmp_min_prop_in_out, _, _, _, tmp_min_trans_out, \
                tmp_energy_start, tmp_energy_end, _, _, _, _, _, _, _, _, _, _) \
             = setupSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    targetCell.sim_setup_lowest, targetCell.sim_setup_highest, \
                                                                    targetCell.sim_setup_timestep*tmp_tstep_mag1, tmp_min_hold, 5, spicef)

            tmp_tstep_mag = 2
            tmp_tstep_mag2 = tmp_tstep_mag1 
            tmp_tstep_mag1 = tmp_tstep_mag1 / tmp_tstep_mag
            targetLib.print_msg_sim("First stage sparse setup search, timestep: "\
                +str(targetCell.sim_setup_timestep*tmp_tstep_mag1))
            ( tmp_tsetup1, tmp_min_prop_in_out, _, _, _, tmp_min_trans_out, \
                tmp_energy_start, tmp_energy_end, _, _, _, _, _, _, _, _, _, _) \
             = setupSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    tmp_tsetup1 - targetCell.sim_setup_timestep * tmp_tstep_mag2 *1,\
                                                                    tmp_tsetup1 + targetCell.sim_setup_timestep * tmp_tstep_mag2 *2,\
                                                                    targetCell.sim_setup_timestep * tmp_tstep_mag1, tmp_min_hold, 3, spicef)

            while(tmp_tstep_mag1 > tmp_tstep_mag ):
                tmp_tstep_mag2 = tmp_tstep_mag1 
                tmp_tstep_mag1 = tmp_tstep_mag1 / tmp_tstep_mag
                targetLib.print_msg_sim("Mid. stage precise setup search, timestep: "\
                    +str(targetCell.sim_setup_timestep*tmp_tstep_mag1))
                ( tmp_tsetup1, tmp_min_prop_in_out, _, _, _, tmp_min_trans_out, \
                    tmp_energy_start, tmp_energy_end, _, _, _, _, _, _, _, _, _, _) \
                 = setupSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                        tmp_tsetup1 - targetCell.sim_setup_timestep * tmp_tstep_mag2  *1,\
                                                                        tmp_tsetup1 + targetCell.sim_setup_timestep * tmp_tstep_mag2  *3,\
                                                                        targetCell.sim_setup_timestep * tmp_tstep_mag1, tmp_min_hold, 3, spicef)

            targetLib.print_msg_sim("Last stage precise setup search, timestep: "\
                +str(targetCell.sim_setup_timestep))
            ( tmp_tsetup3, tmp_min_prop_in_out, _, _, _, tmp_min_trans_out, \
                tmp_energy_start, tmp_energy_end, _, _, _, _, _, _, _, _, _, _) \
             = setupSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    tmp_tsetup1 - targetCell.sim_setup_timestep * tmp_tstep_mag2 *1,\
                                                                    tmp_tsetup1 + targetCell.sim_setup_timestep * tmp_tstep_mag2 *3,\
                                                                    targetCell.sim_setup_timestep, tmp_min_hold, 2, spicef)
    
            ## if target is D2Q, do standard setup/hold search
            #if((targetHarness.target_inport_val == "01")or(targetHarness.target_inport_val == "10")):
            tmp_tstep_mag = 20
            tmp_tstep_mag1 = float(targetCell.slope[-1])/float(targetCell.slope[0])* tmp_tstep_mag
            targetLib.print_msg_sim("First stage sparse hold search, timestep: "\
                +str(targetCell.sim_hold_timestep*tmp_tstep_mag1))
            ( tmp_thold1, tmp_min_prop_in_out,tmp_min_prop_cin_out, tmp_min_setup, tmp_min_hold, tmp_min_trans_out, \
                tmp_energy_start, tmp_energy_end, tmp_energy_clk_start, tmp_energy_clk_end, \
                tmp_q_in_dyn, tmp_q_out_dyn, tmp_q_clk_dyn, tmp_q_vdd_dyn, tmp_q_vss_dyn, \
                tmp_i_in_leak, tmp_i_vdd_leak, tmp_i_vss_leak) \
            = holdSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    targetCell.sim_hold_lowest, targetCell.sim_hold_highest, \
                                                                    targetCell.sim_hold_timestep*tmp_tstep_mag1, tmp_tsetup3, \
                                                                    3, spicef)

            tmp_tstep_mag = 2
            tmp_tstep_mag2 = tmp_tstep_mag1
            tmp_tstep_mag1 = tmp_tstep_mag1 /  tmp_tstep_mag
            targetLib.print_msg_sim("First stage sparse hold search, timestep: "\
                +str(targetCell.sim_setup_timestep*tmp_tstep_mag1))
            ( tmp_thold1, tmp_min_prop_in_out,tmp_min_prop_cin_out, tmp_min_setup, tmp_min_hold, tmp_min_trans_out, \
                tmp_energy_start, tmp_energy_end, tmp_energy_clk_start, tmp_energy_clk_end, \
                tmp_q_in_dyn, tmp_q_out_dyn, tmp_q_clk_dyn, tmp_q_vdd_dyn, tmp_q_vss_dyn, \
                tmp_i_in_leak, tmp_i_vdd_leak, tmp_i_vss_leak) \
             = holdSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    tmp_thold1 - targetCell.sim_hold_timestep * tmp_tstep_mag2 *2,\
                                                                    tmp_thold1 + targetCell.sim_hold_timestep * tmp_tstep_mag2 *1,\
                                                                    targetCell.sim_hold_timestep * tmp_tstep_mag1, tmp_tsetup3, 3, spicef)

            while(tmp_tstep_mag1 > tmp_tstep_mag ):
                tmp_tstep_mag2 = tmp_tstep_mag1
                tmp_tstep_mag1 = tmp_tstep_mag1 /  tmp_tstep_mag
                targetLib.print_msg_sim("Mid. stage precise hold search, timestep: "\
                    +str(targetCell.sim_setup_timestep*tmp_tstep_mag1))
                ( tmp_thold1, tmp_min_prop_in_out,tmp_min_prop_cin_out, tmp_min_setup, tmp_min_hold, tmp_min_trans_out, \
                    tmp_energy_start, tmp_energy_end, tmp_energy_clk_start, tmp_energy_clk_end, \
                    tmp_q_in_dyn, tmp_q_out_dyn, tmp_q_clk_dyn, tmp_q_vdd_dyn, tmp_q_vss_dyn, \
                    tmp_i_in_leak, tmp_i_vdd_leak, tmp_i_vss_leak) \
                 = holdSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                        tmp_thold1 - targetCell.sim_hold_timestep * tmp_tstep_mag2 *3 ,\
                                                                        tmp_thold1 + targetCell.sim_hold_timestep * tmp_tstep_mag2 *1 ,\
                                                                        targetCell.sim_hold_timestep * tmp_tstep_mag1, tmp_tsetup3, 3, spicef)

            targetLib.print_msg_sim("Last stage precise hold search, timestep: "\
                +str(targetCell.sim_hold_timestep))
            ( res_thold3, res_min_prop_in_out, res_min_prop_cin_out, res_min_setup, res_min_hold, res_min_trans_out, \
                res_energy_start, res_energy_end, tmp_energy_clk_start, tmp_energy_clk_end, \
                res_q_in_dyn, res_q_out_dyn, res_q_clk_dyn, res_q_vdd_dyn, res_q_vss_dyn, \
                res_i_in_leak, res_i_vdd_leak, res_i_vss_leak) \
             = holdSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    tmp_thold1 - targetCell.sim_hold_timestep * tmp_tstep_mag2 *3,\
                                                                    tmp_thold1 + targetCell.sim_hold_timestep * tmp_tstep_mag2 *1 ,\
                                                                    targetCell.sim_hold_timestep, tmp_tsetup3, 2, spicef)
            ## if target is not D2Q (= set or reset), clip lowest hold time to almost zero
            ## this is because removal simulation sometimes very small 

            # end setup/hold search
            #res_list_prop.append(res_min_prop_in_out) # store D2Q 
            res_list_prop.append(res_min_prop_cin_out) # store C2Q (not D2Q)
            res_list_tran.append(res_min_trans_out)
            res_list_setup.append(res_min_setup)
            res_list_hold.append(res_min_hold)
            print("Final C2Q: "+str(res_min_prop_cin_out)+",setup: "+str(res_min_setup)+", hold: "+str(res_min_hold))

            ## intl. energy calculation
            ## intl. energy is the sum of short-circuit energy and drain-diffusion charge/discharge energy
            ## larger Ql: intl. Q, load Q 
            ## smaller Qs: intl. Q
            ## Eintl = QsV
            if(abs(res_q_vdd_dyn) < abs(res_q_vss_dyn)):
                res_list_eintl.append(abs(res_q_vdd_dyn*targetLib.vdd_voltage*targetLib.energy_meas_high_threshold-\
                    abs((res_energy_end - res_energy_start)*(abs(res_i_vdd_leak)+abs(res_i_vdd_leak))/2* \
                    (targetLib.vdd_voltage*targetLib.energy_meas_high_threshold))))
            else:
                res_list_eintl.append(abs(res_q_vss_dyn*targetLib.vdd_voltage*targetLib.energy_meas_high_threshold-\
                    abs((res_energy_end - res_energy_start)*(abs(res_i_vdd_leak)+abs(res_i_vdd_leak))/2* \
                    (targetLib.vdd_voltage*targetLib.energy_meas_high_threshold))))

            ## input energy
            res_list_ein.append(abs(res_q_in_dyn)*targetLib.vdd_voltage)
            res_list_eclk.append(abs(res_q_clk_dyn)*targetLib.vdd_voltage)

            ## Cin = Qin / V
            res_list_cin.append(abs(res_q_in_dyn)/(targetLib.vdd_voltage))
            res_list_cclk.append(abs(res_q_clk_dyn)/(targetLib.vdd_voltage))

            ## Pleak = average of Pleak_vdd and Pleak_vss
            ## P = I * V
            res_list_pleak.append((abs(res_i_vdd_leak)+abs(res_i_vdd_leak))/2*(targetLib.vdd_voltage)) #

        list2_prop.append(res_list_prop)
        list2_tran.append(res_list_tran)
        list2_setup.append(res_list_setup)
        list2_hold.append(res_list_hold)
        #list2_estart.append(res_list_estart)
        #list2_eend.append(res_list_eend)
        list2_eintl.append(res_list_eintl)
        list2_ein.append(res_list_ein)
        list2_cin.append(res_list_cin)
        list2_eclk.append(res_list_eclk)
        list2_cclk.append(res_list_cclk)
        list2_pleak.append(res_list_pleak)

    targetHarness.set_list2_prop(list2_prop)
    #targetHarness.print_list2_prop(targetCell.load, targetCell.slope)
    targetHarness.write_list2_prop(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_prop()
    targetHarness.set_list2_tran(list2_tran)
    #targetHarness.print_list2_tran(targetCell.load, targetCell.slope)
    targetHarness.write_list2_tran(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_tran()
    targetHarness.set_list2_setup(list2_setup)
    #targetHarness.print_list2_setup(targetCell.load, targetCell.slope)
    targetHarness.write_list2_setup(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_setup()
    targetHarness.set_list2_hold(list2_hold)
    #targetHarness.print_list2_hold(targetCell.load, targetCell.slope)
    targetHarness.write_list2_hold(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_hold()
    targetHarness.set_list2_eintl(list2_eintl)
    #targetHarness.print_list2_eintl(targetCell.load, targetCell.slope)
    targetHarness.write_list2_eintl(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_eintl()
    targetHarness.set_list2_ein(list2_ein)
    #targetHarness.print_list2_ein(targetCell.load, targetCell.slope)
    targetHarness.write_list2_ein(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_ein()
    targetHarness.set_list2_cin(list2_cin)
    #targetHarness.print_list2_cin(targetCell.load, targetCell.slope)
    targetHarness.average_list2_cin(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_cin()
    targetHarness.set_list2_eclk(list2_eclk)
    #targetHarness.print_list2_eclk(targetCell.load, targetCell.slope)
    targetHarness.write_list2_eclk(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_eclk()
    targetHarness.set_list2_cclk(list2_cclk)
    #targetHarness.print_list2_cclk(targetCell.load, targetCell.slope)
    targetHarness.average_list2_cclk(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_cclk()
    targetHarness.set_list2_pleak(list2_pleak)
    #targetHarness.print_list2_pleak(targetCell.load, targetCell.slope)
    targetHarness.write_list2_pleak(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_pleak()
        

def runSpiceFlopRecoveryRemoval(targetLib, targetCell, targetHarness, spicef):
    ## Note! In recovery/removal simulation, recovaly is treated as setup,
    ## and removal is treated as hold. Set/reset to Q delay is treated 
    ## as D2Q delay.
    ## VIN in spice is connected to set/reset, and fixed wave is applied
    ## into d-input of Flip-Flop
    list2_prop =   []
    list2_setup =   []
    list2_hold =   []
    list2_tran =   []
    list2_estart = []
    list2_eend =   []
    list2_eintl =   []
    list2_ein =   []
    list2_cin =   []
    list2_eclk =   []
    list2_cclk =   []
    list2_pleak =   []
    for tmp_slope in targetCell.slope:
        res_list_prop =   []  # C2Q
        res_list_setup =  []  # D2C(setup)
        res_list_hold =   []  # C2D(hold)
        res_list_tran =   []
        res_list_estart = []
        res_list_eend =   []
        res_list_eintl =   []
        res_list_ein =   []
        res_list_cin =   []
        res_list_eclk =   []
        res_list_cclk =   []
        res_list_pleak =   []

        for tmp_load in targetCell.load:
            tmp_max_val_loop = float(targetCell.slope[-1]) * 10 # use x10 of max. slope for max val.
            tmp_min_setup = tmp_max_val_loop # temporal value for setup 
            tmp_tsetup1 = tmp_max_val_loop   # temporal value for setup 
            tmp_tsetup2 = tmp_max_val_loop   # temporal value for setup 
            tmp_tsetup3 = tmp_max_val_loop   # temporal value for setup 
            tmp_thold1 = tmp_max_val_loop    # temporal value for setup 
            tmp_thold2 = tmp_max_val_loop    # temporal value for setup 
            tmp_min_hold  = tmp_max_val_loop # temporal value for setup 

            # C2Q and recovery search (sparce)
            # perform two-stage simulation
            # 1st stage: sim w/  10-% output swing
            # 2nd stage: sim w/ 100-% output swing
            tsimendmag = [1, 10]; # magnify parameter of _tsimend
            tranmag = [float(targetLib.logic_threshold_low)*1.1, 1];         # magnify parameter of transient simulation
            tmp_min_prop_in_out   = tmp_max_val_loop # temporal value for D2Qmin search
            tmp_min_prop_cin_out  = tmp_max_val_loop # temporal value for D2Qmin search
            tmp_min_trans_out     = tmp_max_val_loop # temporal value for D2Qmin search
            tmp_energy_start  = tmp_max_val_loop     # temporal value for D2Qmin search
            tmp_energy_end    = tmp_max_val_loop     # temporal value for D2Qmin search
            tmp_energy_clk_start  = tmp_max_val_loop # temporal value for D2Qmin search
            tmp_energy_clk_end    = tmp_max_val_loop # temporal value for D2Qmin search
            spicefrr = spicef + "_rr"

            ## for recovery search, invert reset/set signal 
            targetHarness.invert_set_reset_val()

            tmp_tstep_mag = 20
            tmp_tstep_mag1 = float(targetCell.slope[-1])/float(targetCell.slope[0])* tmp_tstep_mag
            targetLib.print_msg_sim("First stage sparse recovery search, timestep: "\
                +str(targetCell.sim_setup_timestep*tmp_tstep_mag1))
            ( tmp_tsetup1, tmp_min_prop_in_out, _, _, _, tmp_min_trans_out, \
                tmp_energy_start, tmp_energy_end, _, _, _, _, _, _, _, _, _, _) \
             = setupSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    targetCell.sim_setup_lowest, targetCell.sim_setup_highest*2, \
                                                                    targetCell.sim_setup_timestep*tmp_tstep_mag1, tmp_min_hold, 3, spicefrr)

            tmp_tstep_mag = 2
            tmp_tstep_mag2 = tmp_tstep_mag1 
            tmp_tstep_mag1 = tmp_tstep_mag1 /  tmp_tstep_mag
            targetLib.print_msg_sim("First stage sparse recovery search, timestep: "\
                +str(targetCell.sim_setup_timestep*tmp_tstep_mag2))
            ( tmp_tsetup1, tmp_min_prop_in_out, _, _, _, tmp_min_trans_out, \
                tmp_energy_start, tmp_energy_end, _, _, _, _, _, _, _, _, _, _) \
             = setupSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    tmp_tsetup1 - targetCell.sim_setup_timestep * tmp_tstep_mag2 *1,\
                                                                    tmp_tsetup1 + targetCell.sim_setup_timestep * tmp_tstep_mag2 *3,\
                                                                    targetCell.sim_setup_timestep * tmp_tstep_mag2, tmp_min_hold, 3, spicefrr)

            while(tmp_tstep_mag1 > tmp_tstep_mag ):
                tmp_tstep_mag2 = tmp_tstep_mag1 
                tmp_tstep_mag1 = tmp_tstep_mag1 /  tmp_tstep_mag
                targetLib.print_msg_sim("Mid. stage precise recovery search, timestep: "\
                    +str(targetCell.sim_setup_timestep*tmp_tstep_mag2))
                ( tmp_tsetup1, tmp_min_prop_in_out, _, _, _, tmp_min_trans_out, \
                    tmp_energy_start, tmp_energy_end, _, _, _, _, _, _, _, _, _, _) \
                 = setupSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                        tmp_tsetup1 - targetCell.sim_setup_timestep * tmp_tstep_mag2 *1,\
                                                                        tmp_tsetup1 + targetCell.sim_setup_timestep * tmp_tstep_mag2 *3,\
                                                                        targetCell.sim_setup_timestep * tmp_tstep_mag2, tmp_min_hold, 3, spicefrr)

            targetLib.print_msg_sim("Last stage precise recovery search, timestep: "+str(targetCell.sim_setup_timestep))
            ( res_tsetup3, res_min_prop_in_out, res_min_prop_cin_out, res_min_setup, res_min_hold, res_min_trans_out, \
                tmp_energy_start, tmp_energy_end, _, _, _, _, _, _, _, _, _, _) \
             = setupSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    tmp_tsetup1 - targetCell.sim_setup_timestep * tmp_tstep_mag2 *1,\
                                                                    tmp_tsetup1 + targetCell.sim_setup_timestep * tmp_tstep_mag2 *3,\
                                                                    targetCell.sim_setup_timestep, tmp_min_hold, 2, spicefrr)
    
            ## Note! min_setup (min R2C) is recovery.
            ## It is stored into setup object, and 
            ## stored into recovery LUT 
            res_list_setup.append(res_min_setup) # recovery

            ## for removal search, restore reset/set signal 
            targetHarness.invert_set_reset_val()

            tmp_tstep_mag = 20
            tmp_tstep_mag1 = float(targetCell.slope[-1])/float(targetCell.slope[0])* tmp_tstep_mag
            targetLib.print_msg_sim("First stage sparse removal search, timestep: "\
                +str(targetCell.sim_hold_timestep*tmp_tstep_mag1))
            ( tmp_thold1, tmp_min_prop_in_out,tmp_min_prop_cin_out, tmp_min_setup, tmp_min_hold, tmp_min_trans_out, \
                tmp_energy_start, tmp_energy_end, tmp_energy_clk_start, tmp_energy_clk_end, \
                tmp_q_in_dyn, tmp_q_out_dyn, tmp_q_clk_dyn, tmp_q_vdd_dyn, tmp_q_vss_dyn, \
                tmp_i_in_leak, tmp_i_vdd_leak, tmp_i_vss_leak) \
            = holdSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    targetCell.sim_hold_highest * 4, 0 , \
                                                                    -targetCell.sim_hold_timestep*tmp_tstep_mag1, -tmp_tsetup3, \
                                                                    3, spicefrr)

            tmp_tstep_mag = 2
            tmp_tstep_mag2 = tmp_tstep_mag1 
            tmp_tstep_mag1 = tmp_tstep_mag1 /  tmp_tstep_mag
            targetLib.print_msg_sim("Mid. stage precise removal search, timestep: "\
                +str(targetCell.sim_hold_timestep*tmp_tstep_mag2))
            ( tmp_thold1, tmp_min_prop_in_out,tmp_min_prop_cin_out, tmp_min_setup, tmp_min_hold, tmp_min_trans_out, \
                tmp_energy_start, tmp_energy_end, tmp_energy_clk_start, tmp_energy_clk_end, \
                tmp_q_in_dyn, tmp_q_out_dyn, tmp_q_clk_dyn, tmp_q_vdd_dyn, tmp_q_vss_dyn, \
                tmp_i_in_leak, tmp_i_vdd_leak, tmp_i_vss_leak) \
             = holdSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    tmp_thold1 + targetCell.sim_hold_timestep * tmp_tstep_mag2 *2,\
                                                                    tmp_thold1 - targetCell.sim_hold_timestep * tmp_tstep_mag2 *2,\
                                                                    -targetCell.sim_hold_timestep * tmp_tstep_mag2, -tmp_tsetup3, 3, spicefrr)

            while(tmp_tstep_mag1 > tmp_tstep_mag ):
                tmp_tstep_mag2 = tmp_tstep_mag1 
                tmp_tstep_mag1 = tmp_tstep_mag1 /  tmp_tstep_mag
                targetLib.print_msg_sim("Mid. stage precise removal search, timestep: "\
                    +str(targetCell.sim_hold_timestep*tmp_tstep_mag2))
                #print("tmp_thold1: "+str(tmp_thold1))
                #print("from: "+str(tmp_thold1 + targetCell.sim_hold_timestep * tmp_tstep_mag2 *3)+" to: "+str(tmp_thold1 - targetCell.sim_hold_timestep * tmp_tstep_mag2 *2))
                ( tmp_thold1, tmp_min_prop_in_out,tmp_min_prop_cin_out, tmp_min_setup, tmp_min_hold, tmp_min_trans_out, \
                    tmp_energy_start, tmp_energy_end, tmp_energy_clk_start, tmp_energy_clk_end, \
                    tmp_q_in_dyn, tmp_q_out_dyn, tmp_q_clk_dyn, tmp_q_vdd_dyn, tmp_q_vss_dyn, \
                    tmp_i_in_leak, tmp_i_vdd_leak, tmp_i_vss_leak) \
                 = holdSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                        tmp_thold1 + targetCell.sim_hold_timestep * tmp_tstep_mag2 *3,\
                                                                        tmp_thold1 - targetCell.sim_hold_timestep * tmp_tstep_mag2 *2,\
                                                                        -targetCell.sim_hold_timestep * tmp_tstep_mag2, -tmp_tsetup3, 3, spicefrr)

            targetLib.print_msg_sim("Last stage precise removal search, timestep: "\
                +str(targetCell.sim_hold_timestep))
            ( res_thold3, res_min_prop_in_out, res_min_prop_cin_out, res_min_setup, res_min_hold, res_min_trans_out, \
                res_energy_start, res_energy_end, tmp_energy_clk_start, tmp_energy_clk_end, \
                res_q_in_dyn, res_q_out_dyn, res_q_clk_dyn, res_q_vdd_dyn, res_q_vss_dyn, \
                res_i_in_leak, res_i_vdd_leak, res_i_vss_leak) \
             = holdSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
                                                                    tmp_thold1 + targetCell.sim_hold_timestep * tmp_tstep_mag2 *3,\
                                                                    tmp_thold1 - targetCell.sim_hold_timestep * tmp_tstep_mag2 *1,\
                                                                    -targetCell.sim_hold_timestep, -tmp_tsetup3, 2, spicefrr)
    

            # end recov/remov search
            #res_list_prop.append(res_min_prop_in_out) # store D2Q 
            res_list_prop.append(res_min_prop_cin_out) # store C2Q (cause Q is activated by set/reset)
            res_list_tran.append(res_min_trans_out)
            ## Note! min_backside_setup = hold (min minus R2Q) is removal.
            ## It is stored into hold object, and 
            ## stored into removal LUT 
            res_list_hold.append(-res_min_setup)   # removal

            ## intl. energy calculation
            ## intl. energy is the sum of short-circuit energy and drain-diffusion charge/discharge energy
            ## larger Ql: intl. Q, load Q 
            ## smaller Qs: intl. Q
            ## Eintl = QsV
            if(abs(res_q_vdd_dyn) < abs(res_q_vss_dyn)):
                res_list_eintl.append(abs(res_q_vdd_dyn*targetLib.vdd_voltage*targetLib.energy_meas_high_threshold-\
                    abs((res_energy_end - res_energy_start)*(abs(res_i_vdd_leak)+abs(res_i_vdd_leak))/2* \
                    (targetLib.vdd_voltage*targetLib.energy_meas_high_threshold))))
            else:
                res_list_eintl.append(abs(res_q_vss_dyn*targetLib.vdd_voltage*targetLib.energy_meas_high_threshold-\
                    abs((res_energy_end - res_energy_start)*(abs(res_i_vdd_leak)+abs(res_i_vdd_leak))/2* \
                    (targetLib.vdd_voltage*targetLib.energy_meas_high_threshold))))

            ## input energy
            res_list_ein.append(abs(res_q_in_dyn)*targetLib.vdd_voltage)
            res_list_eclk.append(abs(res_q_clk_dyn)*targetLib.vdd_voltage)

            ## Cin = Qin / V
            res_list_cin.append(abs(res_q_in_dyn)/(targetLib.vdd_voltage))
            res_list_cclk.append(abs(res_q_clk_dyn)/(targetLib.vdd_voltage))

            ## Pleak = average of Pleak_vdd and Pleak_vss
            ## P = I * V
            res_list_pleak.append((abs(res_i_vdd_leak)+abs(res_i_vdd_leak))/2*(targetLib.vdd_voltage)) #

        list2_prop.append(res_list_prop)
        list2_tran.append(res_list_tran)
        list2_setup.append(res_list_setup)
        list2_hold.append(res_list_hold)
        #list2_estart.append(res_list_estart)
        #list2_eend.append(res_list_eend)
        list2_eintl.append(res_list_eintl)
        list2_ein.append(res_list_ein)
        list2_cin.append(res_list_cin)
        list2_eclk.append(res_list_eclk)
        list2_cclk.append(res_list_cclk)
        list2_pleak.append(res_list_pleak)

    targetHarness.set_list2_prop(list2_prop)
    #targetHarness.print_list2_prop(targetCell.load, targetCell.slope)
    targetHarness.write_list2_prop(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_prop()
    targetHarness.set_list2_tran(list2_tran)
    #targetHarness.print_list2_tran(targetCell.load, targetCell.slope)
    targetHarness.write_list2_tran(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_tran()
    targetHarness.set_list2_setup(list2_setup)
    #targetHarness.print_list2_setup(targetCell.load, targetCell.slope)
    targetHarness.write_list2_setup(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_setup()
    targetHarness.set_list2_hold(list2_hold)
    #targetHarness.print_list2_hold(targetCell.load, targetCell.slope)
    targetHarness.write_list2_hold(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_hold()
    targetHarness.set_list2_eintl(list2_eintl)
    #targetHarness.print_list2_eintl(targetCell.load, targetCell.slope)
    targetHarness.write_list2_eintl(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_eintl()
    targetHarness.set_list2_ein(list2_ein)
    #targetHarness.print_list2_ein(targetCell.load, targetCell.slope)
    targetHarness.write_list2_ein(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_ein()
    targetHarness.set_list2_cin(list2_cin)
    #targetHarness.print_list2_cin(targetCell.load, targetCell.slope)
    targetHarness.average_list2_cin(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_cin()
    targetHarness.set_list2_eclk(list2_eclk)
    #targetHarness.print_list2_eclk(targetCell.load, targetCell.slope)
    targetHarness.write_list2_eclk(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_eclk()
    targetHarness.set_list2_cclk(list2_cclk)
    #targetHarness.print_list2_cclk(targetCell.load, targetCell.slope)
    targetHarness.average_list2_cclk(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_cclk()
    targetHarness.set_list2_pleak(list2_pleak)
    #targetHarness.print_list2_pleak(targetCell.load, targetCell.slope)
    targetHarness.write_list2_pleak(targetLib, targetCell.load, targetCell.slope)
    #targetHarness.print_lut_pleak()

def holdSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, \
            thold_lowest, thold_highest, thold_tstep, tsetup, timestep_mag, spicef):
    # hold search
    # perform two-stage simulation
    # 1st stage: sim w/  10-% output swing
    # 2nd stage: sim w/ 100-% output swing
    tsimendmag = [1, 10]; # magnify parameter of _tsimend
    tranmag = [float(targetLib.logic_threshold_low)*1.1, 1];  # magnify parameter of transient simulation
    tmp_max_val_loop = float(targetCell.slope[-1]) * 40 # use x10 of max. slope for max val.
    tmp_min_setup = tmp_max_val_loop # temporal value for setup 
    tmp_min_prop_in_out   = tmp_max_val_loop # temporal value for D2Qmin search
    tmp_min_prop_cin_out  = tmp_max_val_loop # temporal value for D2Qmin search
    tmp_min_trans_out     = tmp_max_val_loop # temporal value for D2Qmin search
    tmp_energy_start  = tmp_max_val_loop # temporal value for D2Qmin search
    tmp_energy_end    = tmp_max_val_loop # temporal value for D2Qmin search
    
    ## calculate whole slope length from logic threshold
    tmp_slope_mag = 1 / (targetLib.logic_threshold_high - targetLib.logic_threshold_low)

    #print ("debug "+str(thold_highest)+","+str(thold_lowest)+","+str(thold_tstep)+"\n\n")
    for thold in np.arange (thold_highest, thold_lowest*1.01, -thold_tstep):
        first_stage_fail = 0
        for j in range(len(tranmag)):
            if(first_stage_fail == 0):
                targetLib.print_msg_sim("dSetup: "+str(f'{tsetup:,.4f}')+str(targetLib.time_unit)+" dHold: "+str(f'{thold:,.4f}')+str(targetLib.time_unit)+" stage:"+str(j))
                cap_line = ".param cap ="+str(tmp_load)+str(targetLib.capacitance_unit)+"\n"
                slew_line = ".param slew ="+str(tmp_slope*tmp_slope_mag)+str(targetLib.time_unit)+"\n"
                cslew_line = ".param cslew ="+str(targetCell.cslope)+str(targetLib.time_unit)+"\n"
                tunit_line = ".param tunit ="+str(targetCell.slope[-1])+str(targetLib.time_unit)+"\n"
                tsetup_line = ".param tsetup ="+str(tsetup)+str(targetLib.time_unit)+"\n"
                thold_line = ".param thold ="+str(thold)+str(targetLib.time_unit)+"\n"
                tsimend_line = ".param tsimendmag ="+str(tsimendmag[j])+" tranmag ="+str(tranmag[j])+"\n"
                spicefo = str(spicef)+"_j"+str(j)+"_"+str(tmp_load)+"_"+str(tmp_slope)+"_setup"+str(f'{tsetup:,.4f}')+"_hold"+str(f'{thold:,.4f}')+".sp"
                tran_line =".tran "+str(targetCell.simulation_timestep*timestep_mag)+str(targetLib.time_unit)+" '_tsimend'\n"
                #targetLib.print_msg(spicefo)
        
                ## Delay simulation
                (res_prop_in_out, res_prop_cin_out, res_trans_out,res_energy_start, \
                res_energy_end, res_energy_clk_start, res_energy_clk_end, res_setup, res_hold)\
                    = genFileFlop_trial1(targetLib, targetCell, targetHarness, "delay", \
                        cap_line, slew_line, cslew_line, tunit_line, tsetup_line, \
                        thold_line, tsimend_line, tran_line, "none", "none", "none", "none", spicefo)
          
                ## if delay simulation failes, skip energy simulation
                ## and set fail
                if((str(res_energy_start) == "failed") or (str(res_energy_end) == "failed") \
                    or (str(res_energy_clk_start) == "failed") or (str(res_energy_clk_end) == "failed")):
                    first_stage_fail = 1
                else:
                # Energy simulation
                    estart_line = ".param ENERGY_START = "+str(res_energy_start)+"\n"
                    eend_line = ".param ENERGY_END = "+str(res_energy_end)+"\n"
                    eclkstart_line = ".param ENERGY_CLK_START = "+str(res_energy_clk_start)+"\n"
                    eclkend_line = ".param ENERGY_CLK_END = "+str(res_energy_clk_end)+"\n"
                    spicefo = str(spicef)+"_j"+str(j)+"_"+str(tmp_load)+"_"+str(tmp_slope)+"_setup"+str(f'{tsetup:,.4f}')+"_hold"+str(f'{thold:,.4f}')+"_2.sp"
                    (res_prop_in_out, res_prop_cin_out, res_trans_out, res_setup, res_hold,\
                                q_in_dyn, q_out_dyn, q_clk_dyn, q_vdd_dyn, q_vss_dyn, i_in_leak, \
                                i_vdd_leak, i_vss_leak) \
                        = genFileFlop_trial1(targetLib, targetCell, targetHarness, "energy", cap_line, slew_line, cslew_line,\
                                                                    tunit_line, tsetup_line, thold_line, tsimend_line, tran_line, \
                                                                    estart_line, eend_line, eclkstart_line, eclkend_line,  spicefo)
                    #  check 1st and 2nd run of simulation
                    # if res_trans_out failed, it may failed in both run -> exit 
                    if(res_trans_out == "failed"):
                        first_stage_fail = 1

        #  check second run of simulation
        # if (current D2Q > prev. D2Q), exceeds min D2Q
        #if((res_prop_in_out == "failed")or(float(res_prop_in_out) > tmp_min_prop_in_out)or(first_stage_fail == 1)):
        if((res_prop_in_out == "failed")or(first_stage_fail == 1)):
            if(tmp_max_val_loop == tmp_min_prop_in_out):
                print("Error: simulation failed! Check spice deck!")
                print("spice deck: "+spicefo)
                my_exit()

            targetLib.print_msg_sim("Min. D2Q found. Break loop at dHold: "+str(f'{thold:,.4f}'))

            return ( float(thold + thold_tstep), tmp_min_prop_in_out, tmp_min_prop_cin_out, tmp_min_setup, tmp_min_hold, tmp_min_trans_out, \
            #return ( float(thold + thold_tstep), tmp_min_prop_in_out, tmp_min_prop_cin_out, float(res_setup), tmp_min_hold, tmp_min_trans_out, \
                            tmp_energy_start, tmp_energy_end, tmp_energy_clk_start, tmp_energy_clk_end, \
                            tmp_q_in_dyn, tmp_q_out_dyn, tmp_q_clk_dyn,  tmp_q_vdd_dyn, tmp_q_vss_dyn, \
                            tmp_i_in_leak, tmp_i_vdd_leak, tmp_i_vss_leak)
#			break
        
        #update C2Q(res_prop_in_out) 
        tmp_min_prop_in_out  = float(res_prop_in_out)
        # in set/reset sim, res_prop_cin_out is not measured
        if((res_prop_cin_out == "failed") or (res_prop_cin_out == tmp_max_val_loop)):
            tmp_min_prop_cin_out = float(res_prop_in_out)
        else:
            tmp_min_prop_cin_out  = float(res_prop_cin_out)
        tmp_min_trans_out    = float(res_trans_out)
        if(res_energy_start != "failed"):
            tmp_energy_start = float(res_energy_start)
        if(res_energy_end != "failed"):
            tmp_energy_end   = float(res_energy_end)
        #targetLib.print_msg("res_energy_clk_start;"+res_energy_clk_start)
        if(res_energy_clk_start != "failed"):
            tmp_energy_clk_start = float(res_energy_clk_start)
        if(res_energy_clk_end != "failed"):
            tmp_energy_clk_end   = float(res_energy_clk_end)
        if(q_in_dyn != "failed"):
            tmp_q_in_dyn   = float(q_in_dyn)
        if(q_out_dyn != "failed"):
            tmp_q_out_dyn  = float(q_out_dyn)
        if(q_clk_dyn != "failed"):
            tmp_q_clk_dyn  = float(q_clk_dyn)
        if(q_vdd_dyn != "failed"):
            tmp_q_vdd_dyn  = float(q_vdd_dyn)
        if(q_vss_dyn != "failed"):
            tmp_q_vss_dyn  = float(q_vss_dyn)
        if(q_in_dyn != "failed"):
            tmp_i_in_leak  = float(i_in_leak)
        if(q_vdd_dyn != "failed"):
            tmp_i_vdd_leak = float(i_vdd_leak)
        if(q_vss_dyn != "failed"):
            tmp_i_vss_leak = float(i_vss_leak)
        if(res_setup != "failed"):
            tmp_min_setup = float(res_setup)
        if(res_hold != "failed"):
            tmp_min_hold = float(res_hold)
            #targetLib.print_msg("tmp_min_hold: "+str(tmp_min_hold)+"\n")
        #targetLib.print_msg("spicef: "+str(spicef)+"\n")

    # finish without premature ending
    print("Error! End of dhold search!!: "+str(f'{thold:,.4f}'))
    print("spice deck: "+spicefo)
    my_exit()


def setupSearchFlop(targetLib, targetCell, targetHarness, tmp_load, tmp_slope, tsetup_lowest, tsetup_highest, tsetup_tstep, tmp_min_hold, timestep_mag, spicef):
    tsimendmag = [1, 10]; # magnify parameter of _tsimend
    tranmag = [float(targetLib.logic_threshold_low)*1.1, 1];         # magnify parameter of transient simulation
    tmp_max_val_loop = float(targetCell.slope[-1]) * 10 # use x10 of max. slope for max val.
    tmp_min_setup = tmp_max_val_loop # temporal value for setup 
    tmp_min_prop_in_out   = tmp_max_val_loop # temporal value for D2Qmin search
    tmp_min_prop_cin_out  = tmp_max_val_loop # temporal value for D2Qmin search
    tmp_min_trans_out     = tmp_max_val_loop # temporal value for D2Qmin search
    tmp_energy_start  = tmp_max_val_loop # temporal value for D2Qmin search
    tmp_energy_end    = tmp_max_val_loop # temporal value for D2Qmin search

    ## calculate whole slope length from logic threshold
    tmp_slope_mag = 1 / (targetLib.logic_threshold_high - targetLib.logic_threshold_low)

    for tsetup in np.arange (tsetup_lowest, tsetup_highest*1.01, tsetup_tstep):
        first_stage_fail = 0
        for j in range(len(tranmag)):
            if(first_stage_fail == 0):
                targetLib.print_msg_sim("dSetup: "+str(f'{tsetup:,.4f}')+str(targetLib.time_unit)+" dHold: "+str(f'{tmp_min_hold:,.4f}')+str(targetLib.time_unit)+" stage:"+str(j))
                cap_line = ".param cap ="+str(tmp_load)+str(targetLib.capacitance_unit)+"\n"
                slew_line = ".param slew ="+str(tmp_slope*tmp_slope_mag)+str(targetLib.time_unit)+"\n"
                cslew_line = ".param cslew ="+str(targetCell.cslope)+str(targetLib.time_unit)+"\n"
                tunit_line = ".param tunit ="+str(targetCell.slope[-1])+str(targetLib.time_unit)+"\n"
                tsetup_line = ".param tsetup ="+str(tsetup)+str(targetLib.time_unit)+"\n"
                thold_line = ".param thold ="+str(tmp_min_hold)+str(targetLib.time_unit)+"\n"
                tsimend_line = ".param tsimendmag ="+str(tsimendmag[j])+" tranmag ="+str(tranmag[j])+"\n"
                spicefo = str(spicef)+"_j"+str(j)+"_"+str(tmp_load)+"_"+str(tmp_slope)+"_setup"+str(f'{tsetup:,.4f}')+"_hold"+str(f'{tmp_min_hold:,.4f}')+".sp"
                tran_line =".tran "+str(targetCell.simulation_timestep*timestep_mag)+str(targetLib.time_unit)+" '_tsimend'\n"
                #targetLib.print_msg_sim(spicefo)
        
                ## Delay simulation
                (res_prop_in_out, res_prop_cin_out, res_trans_out, res_energy_start, \
                res_energy_end, res_energy_clk_start, res_energy_clk_end, res_setup, res_hold)\
                    = genFileFlop_trial1(targetLib, targetCell, targetHarness, "delay", 
                        cap_line, slew_line, cslew_line,	tunit_line, tsetup_line, \
                        thold_line, tsimend_line, tran_line, "none", "none", "none", "none", spicefo)
          
                ## if delay simulation failes, skip energy simulation
                ## and set fail
                if((str(res_energy_start) == "failed") or (str(res_energy_end) == "failed") \
                    or (str(res_energy_clk_start) == "failed") or (str(res_energy_clk_end) == "failed")):
                    first_stage_fail = 1
                else:
                    ## Energy simulation 
                    estart_line = ".param ENERGY_START = "+str(res_energy_start)+"\n"
                    eend_line = ".param ENERGY_END = "+str(res_energy_end)+"\n"
                    eclkstart_line = ".param ENERGY_CLK_START = "+str(res_energy_clk_start)+"\n"
                    eclkend_line = ".param ENERGY_CLK_END = "+str(res_energy_clk_end)+"\n"
                    spicefo = str(spicef)+"_j"+str(j)+"_"+str(tmp_load)+"_"+str(tmp_slope)+"_setup"+str(f'{tsetup:,.4f}')+"_hold"+str(f'{tmp_min_hold:,.4f}')+"_2.sp"
                    (res_prop_in_out, res_prop_cin_out, res_trans_out, res_setup, res_hold,\
                                q_in_dyn, q_out_dyn, q_clk_dyn, q_vdd_dyn, q_vss_dyn, i_in_leak, \
                                i_vdd_leak, i_vss_leak) \
                        = genFileFlop_trial1(targetLib, targetCell, targetHarness, "energy", cap_line, slew_line, cslew_line,\
                                                                    tunit_line, tsetup_line, thold_line, tsimend_line, tran_line, \
                                                                    estart_line, eend_line, eclkstart_line, eclkend_line,  spicefo)
                    ##  check 1st and 2nd run of simulation
                    ## if res_trans_out failed, it may failed in both run -> exit 
                    if(res_trans_out == "failed"):
                        first_stage_fail = 1

        tmp_tsetup = tsetup - tsetup_tstep # restore previous tsetup 

        #  check second run of simulation
        # if (current D2Q > prev. D2Q), exceeds min D2Q
        if((res_prop_in_out == "failed") \
            or(float(res_prop_in_out) > tmp_min_prop_in_out) \
            or(first_stage_fail == 1)):
            if(tmp_max_val_loop == tmp_min_prop_in_out):
                targetLib.print_msg_sim("Error: simulation failed! Check spice deck!")
                targetLib.print_msg("spice deck: "+spicefo)
                my_exit()
            targetLib.print_msg_sim("Min. D2Q found. Break loop at dSetup: "+str(f'{tsetup:,.4f}'))
            # finish without premature ending
            #return float(tsetup - tsetup_tstep) 
            return ( float(tsetup - tsetup_tstep), tmp_min_prop_in_out, tmp_min_prop_cin_out,\
                            tmp_min_setup, tmp_min_hold, tmp_min_trans_out, \
                            tmp_energy_start, tmp_energy_end, tmp_energy_clk_start, tmp_energy_clk_end, \
                            tmp_q_in_dyn, tmp_q_out_dyn, tmp_q_clk_dyn,  tmp_q_vdd_dyn, tmp_q_vss_dyn, \
                            tmp_i_in_leak, tmp_i_vdd_leak, tmp_i_vss_leak)

        # update C2Q(res_prop_in_out) 
        # tmp_min_prop_in_out  = float(res_prop_in_out)
        #update C2Q(res_prop_in_out) 
        tmp_min_prop_in_out  = float(res_prop_in_out)
        # in set/reset sim, res_prop_cin_out is not measured
        if((res_prop_cin_out == "failed") or (res_prop_cin_out == tmp_max_val_loop)):
            tmp_min_prop_cin_out = float(res_prop_in_out)
        else:
            tmp_min_prop_cin_out  = float(res_prop_cin_out)
        tmp_min_trans_out    = float(res_trans_out)
        if(res_energy_start != "failed"):
            tmp_energy_start = float(res_energy_start)
        if(res_energy_end != "failed"):
            tmp_energy_end   = float(res_energy_end)
        #targetLib.print_msg_sim("res_energy_clk_start;"+res_energy_clk_start)
        if(res_energy_clk_start != "failed"):
            tmp_energy_clk_start = float(res_energy_clk_start)
        if(res_energy_clk_end != "failed"):
            tmp_energy_clk_end   = float(res_energy_clk_end)
        if(q_in_dyn != "failed"):
            tmp_q_in_dyn   = float(q_in_dyn)
        if(q_out_dyn != "failed"):
            tmp_q_out_dyn  = float(q_out_dyn)
        if(q_clk_dyn != "failed"):
            tmp_q_clk_dyn  = float(q_clk_dyn)
        if(q_vdd_dyn != "failed"):
            tmp_q_vdd_dyn  = float(q_vdd_dyn)
        if(q_vss_dyn != "failed"):
            tmp_q_vss_dyn  = float(q_vss_dyn)
        if(q_in_dyn != "failed"):
            tmp_i_in_leak  = float(i_in_leak)
        if(q_vdd_dyn != "failed"):
            tmp_i_vdd_leak = float(i_vdd_leak)
        if(q_vss_dyn != "failed"):
            tmp_i_vss_leak = float(i_vss_leak)
        if(res_setup != "failed"):
            tmp_min_setup = float(res_setup)
#		if(res_hold != "failed"):         ## In the setup search  
#			tmp_min_hold = float(res_hold)  ## hold should be ideal

    # finish without premature ending
    targetLib.print_msg_sim("Min. D2Q found at dSetup: "+str(f'{tsetup:,.4f}'))
    #return float(tsetup - tsetup_tstep) 
    return ( float(tsetup - tsetup_tstep), tmp_min_prop_in_out, tmp_min_prop_cin_out, \
                    tmp_min_setup, tmp_min_hold, tmp_min_trans_out, \
                    tmp_energy_start, tmp_energy_end, tmp_energy_clk_start, tmp_energy_clk_end, \
                    tmp_q_in_dyn, tmp_q_out_dyn, tmp_q_clk_dyn,  tmp_q_vdd_dyn, tmp_q_vss_dyn, \
                    tmp_i_in_leak, tmp_i_vdd_leak, tmp_i_vss_leak)


def genFileFlop_trial1(targetLib, targetCell, targetHarness, sim_mode, cap_line, \
        slew_line, cslew_line, tunit_line, tsetup_line, thold_line, tsimend_line, \
        tran_line, estart_line, eend_line, eclkstart_line, eclkend_line, spicef):
    #print (spicef)
    #print ("generate AND2\n")
    #targetLib.print_msg_sim(dir(targetLib))
    spicelis = spicef
    spicelis += ".lis"

    # if file is not exist, create spice file and run spice
    if(not os.path.isfile(spicelis)):
#		print("skip file: "+str(spicef))
#	else:
        with open(spicef,'w') as f:
            outlines = []
            outlines.append("*title: flop delay meas.\n")
            outlines.append(".option brief nopage nomod post=1 ingold=2 autostop\n")
            outlines.append(".inc '../"+str(targetCell.model)+"'\n")
            outlines.append(".inc '../"+str(targetCell.netlist)+"'\n")
            outlines.append(".param _vdd = '"+str(targetLib.vdd_voltage)+"*"+str(targetLib.voltage_mag)+"'\n")
            outlines.append(".param _vss = '"+str(targetLib.vss_voltage)+"*"+str(targetLib.voltage_mag)+"'\n")
            outlines.append(".param _vnw = '"+str(targetLib.nwell_voltage)+"*"+str(targetLib.voltage_mag)+"'\n")
            outlines.append(".param _vpw = '"+str(targetLib.pwell_voltage)+"*"+str(targetLib.voltage_mag)+"'\n")
            outlines.append(".param cap = 10f \n")
            outlines.append(".param slew = 100p \n")
            outlines.append(".param cslew = 100p \n")
            outlines.append(".param tunit = 100p \n")
            outlines.append(".param tsetup = 100p \n")
            outlines.append(".param thold = 100p \n")
            outlines.append(".param tsimendmag = 100 tranmag = 1\n")
            outlines.append(".param _tslew = slew \n")
            outlines.append(".param _tclk1 = slew \n")                # ^ first clock
            outlines.append(".param _tclk2 = '_tclk1 + cslew '\n")    # | 
            outlines.append(".param _tclk3 = '_tclk2 + tunit '\n")    # | 
            outlines.append(".param _tclk4 = '_tclk3 + cslew '\n")    # v ^ Recovery 
            outlines.append(".param _tclk5 = '_tclk4 + tunit '\n")    #   V Removal    
            outlines.append(".param _tstart1 = '_tclk5 + tunit * 10 + tsetup'\n")    # ^ data input start 
            outlines.append(".param _tstart2 = '_tstart1 + slew'\n")                 # v varied w/ dedge
            outlines.append(".param _tend1 = '_tstart2 + tunit + thold'\n")   # ^ data input end
            outlines.append(".param _tend2 = '_tend1 + slew'\n")      # v varied w/ dedge
            outlines.append(".param _tclk6 = '_tclk4 + tunit * 10'\n")       # ^ second clock
            outlines.append(".param _tclk7 = '_tclk6 + cslew '\n")           # v 
            outlines.append(".param _tsimend = '_tend2 + tunit * 50 * tsimendmag' \n")
            outlines.append(".param _Energy_meas_end_extent = "+str(targetLib.energy_meas_time_extent)+"\n")
            outlines.append(".measure Tran tstart2_to_tend1 param='_tend1 - _tstart2'\n") # flag to judge min. pulse input for hold search 
            outlines.append(" \n")
            outlines.append("VDD_DYN VDD_DYN 0 DC '_vdd' \n")
            outlines.append("VSS_DYN VSS_DYN 0 DC '_vss' \n")
            outlines.append("VNW_DYN VNW_DYN 0 DC '_vnw' \n")
            outlines.append("VPW_DYN VPW_DYN 0 DC '_vpw' \n")
            outlines.append("VDD_LEAK VDD_LEAK 0 DC '_vdd' \n")
            outlines.append("VSS_LEAK VSS_LEAK 0 DC '_vss' \n")
            outlines.append("VNW_LEAK VNW_LEAK 0 DC '_vnw' \n")
            outlines.append("VPW_LEAK VPW_LEAK 0 DC '_vpw' \n")
            outlines.append("* output load calculation\n")
            outlines.append("VOCAP VOUT WOUT DC 0\n")
            outlines.append(" \n")
            # in auto mode, simulation timestep is 1/10 of min. input slew
            # simulation runs 1000x of input slew time
            # outlines.append(".tran "+str(targetCell.simulation_timestep)+str(targetLib.time_unit)+" '_tsimend'\n")
            outlines.append( tran_line )
            outlines.append(" \n")
            # target Vinput
            V_in_target = None 
            
            # DATA
            if(targetHarness.target_inport_val == "01"):
                outlines.append("VIN VIN 0 PWL(0 '_vss' '_tstart1' '_vss' '_tstart2' '_vdd' '_tend1' '_vdd' '_tend2' '_vss' '_tsimend' '_vss') \n")
                V_in_target = 'VIN'
            elif(targetHarness.target_inport_val == "10"):
                outlines.append("VIN VIN 0 PWL(0 '_vdd' '_tstart1' '_vdd' '_tstart2' '_vss' '_tend1' '_vss' '_tend2' '_vdd' '_tsimend' '_vdd') \n")
                V_in_target = 'VIN'
            elif((targetHarness.target_inport_val == "1") or (targetHarness.target_inport_val == "11")):
                outlines.append("VIN VIN 0 DC '_vdd' \n")
                #outlines.append("VIN VIN 0 PWL(0 '_vss' '_tclk4' '_vss' '_tclk5' '_vdd') \n")
            elif((targetHarness.target_inport_val == "0") or (targetHarness.target_inport_val == "00")):
                outlines.append("VIN VIN 0 DC '_vss' \n")
                #outlines.append("VIN VIN 0 PWL(0 '_vdd' '_tclk4' '_vdd' '_tclk5' '_vss') \n")
            else:
                targetLib.print_msg("Error: no VIN difinition!")
                my_exit()
            outlines.append("VHIGH VHIGH 0 DC '_vdd' \n")
            outlines.append("VLOW VLOW 0 DC '_vss' \n")
  
            ## CLOCK
            ## two clock pulses are used (one for set init., another for C2Q)
            if(targetHarness.target_clock_val == "0101"):
                outlines.append("VCIN VCIN 0 PWL(0 '_vss' '_tclk1' '_vss' '_tclk2' '_vdd' '_tclk3' '_vdd' '_tclk4' '_vss' '_tclk6' '_vss' '_tclk7' '_vdd' '_tsimend' '_vdd') \n")
                ## V_in_target = 'VCIN'
            elif(targetHarness.target_clock_val == "1010"):
                outlines.append("VCIN VCIN 0 PWL(0 '_vdd' '_tclk1' '_vdd' '_tclk2' '_vss' '_tclk3' '_vss' '_tclk4' '_vdd' '_tclk6' '_vdd' '_tclk7' '_vss' '_tsimend' '_vss') \n")
                ## V_in_target = 'VCIN'
            ## one clock pulse is used (for set init.)
            elif(targetHarness.target_clock_val == "010"):
                outlines.append("VCIN VCIN 0 PWL(0 '_vss' '_tclk1' '_vss' '_tclk2' '_vdd' '_tclk3' '_vdd' '_tclk4' '_vss' '_tsimend' '_vss') \n")
            elif(targetHarness.target_clock_val == "101"):
                outlines.append("VCIN VCIN 0 PWL(0 '_vdd' '_tclk1' '_vdd' '_tclk2' '_vss' '_tclk3' '_vss' '_tclk4' '_vdd' '_tsimend' '_vdd') \n")
            else:
                targetLib.print_error("Error: no VCIN difinition!")
            
            ## RST
            if(targetHarness.target_reset_val == "01"):
                outlines.append("VRIN VRIN 0 PWL(0 '_vdd' '_tstart1' '_vdd' '_tstart2' '_vss' '_tend1' '_vss' '_tend2' '_vdd' '_tsimend' '_vdd') \n")
                V_in_target = 'VRIN'
            elif(targetHarness.target_reset_val == "10"):
                outlines.append("VRIN VRIN 0 PWL(0 '_vss' '_tstart1' '_vss' '_tstart2' '_vdd' '_tend1' '_vdd' '_tend2' '_vss' '_tsimend' '_vss') \n")
                V_in_target = 'VRIN'
            elif((targetHarness.target_reset_val == "11")or(targetHarness.target_reset_val == "1")):
                outlines.append("VRIN VRIN 0 DC '_vdd' \n")
            elif((targetHarness.target_reset_val == "00")or(targetHarness.target_reset_val == "0")):
                outlines.append("VRIN VRIN 0 DC '_vss' \n")
            elif(targetHarness.target_reset != None):
                targetLib.print_error("Error: Reset is difined as "+str(targetHarness.target_reset)+" but not VRIN is not defined!")
  
            ## SET
            if(targetHarness.target_set_val == "01"):
                outlines.append("VSIN VSIN 0 PWL(0 '_vdd' '_tstart1' '_vdd' '_tstart2' '_vss' '_tend1' '_vss' '_tend2' '_vdd' '_tsimend' '_vdd') \n")
                V_in_target = 'VSIN'
            elif(targetHarness.target_set_val == "10"):
                outlines.append("VSIN VSIN 0 PWL(0 '_vss' '_tstart1' '_vss' '_tstart2' '_vdd' '_tend1' '_vdd' '_tend2' '_vss' '_tsimend' '_vss') \n")
                V_in_target = 'VSIN'
            elif((targetHarness.target_set_val == "11")or(targetHarness.target_set_val == "1")):
                outlines.append("VSIN VSIN 0 DC '_vdd' \n")
            elif((targetHarness.target_set_val == "00")or(targetHarness.target_set_val == "0")):
                outlines.append("VSIN VSIN 0 DC '_vss' \n")
            elif(targetHarness.target_set != None):
                targetLib.print_error("Error: Set is difined as "+str(targetHarness.target_set)+" but not VSIN is not defined!")
  
            # candidate of input: D, RST, SET
            # measure D2Q
            outlines.append("** Delay \n")
            outlines.append("* Prop delay (D2Q)\n")
            ## case, input 01 -> output 10
            if(((targetHarness.target_inport_val == "01")or(targetHarness.target_set_val == "01")or(targetHarness.target_reset_val == "01"))and(targetHarness.target_outport_val == "10")):
                outlines.append(".measure Tran PROP_IN_OUT trig v("+V_in_target+") val='"+str(float(targetLib.logic_low_to_high_threshold)*float(targetLib.vdd_voltage))+"' td='_tclk5' rise=1 \n")
                outlines.append("+ targ v(VOUT) val='"+str(float(targetLib.logic_high_to_low_threshold)*float(targetLib.vdd_voltage))+"' fall=1  \n") 
                outlines.append(".measure Tran TRANS_OUT trig v(VOUT) val='"+str(float(targetLib.logic_threshold_high)*float(targetLib.vdd_voltage))+"' td='_tclk5' fall=1\n")
                outlines.append("+ targ v(VOUT) val='"+str(float(targetLib.logic_threshold_low)*float(targetLib.vdd_voltage ))+"' fall=1  \n")
                ##outlines.append("+ targ v(VOUT) val='"+str(float(targetLib.logic_threshold_low)*float(targetLib.vdd_voltage ))+"*tranmag' fall=1  \n")
                #outlines.append(".measure Tran ENERGY_START when v("+V_in_target+")='"+str(targetLib.energy_meas_low_threshold)+"' rise=1 td='_tclk5'\n")
                #outlines.append(".measure Tran ENERGY_END when v(VOUT)='"+str(targetLib.energy_meas_low_threshold)+"' fall=1 td='_tclk5' \n")
            ## case, input 01 -> output 01
            elif(((targetHarness.target_inport_val == "01")or(targetHarness.target_set_val == "01")or(targetHarness.target_reset_val == "01"))and(targetHarness.target_outport_val == "01")):
                outlines.append(".measure Tran PROP_IN_OUT trig v("+V_in_target+") val='"+str(float(targetLib.logic_low_to_high_threshold)*float(targetLib.vdd_voltage))+"' td='_tclk5' rise=1 \n")
                outlines.append("+ targ v(VOUT) val='"+str(float(targetLib.logic_low_to_high_threshold)*float(targetLib.vdd_voltage))+"' rise=1  \n") 
                outlines.append(".measure Tran TRANS_OUT trig v(VOUT) val='"+str(float(targetLib.logic_threshold_low)*float(targetLib.vdd_voltage))+"' td='_tclk5' rise=1\n")
                outlines.append("+ targ v(VOUT) val='"+str(float(targetLib.logic_threshold_high)*float(targetLib.vdd_voltage ))+"' rise=1  \n")
                #outlines.append("+ targ v(VOUT) val='"+str(float(targetLib.logic_threshold_high)*float(targetLib.vdd_voltage ))+"*tranmag' rise=1  \n")
                #outlines.append(".measure Tran ENERGY_START when v("+V_in_target+")='"+str(targetLib.energy_meas_low_threshold)+"' rise=1  td='_tclk5'\n")
                #outlines.append(".measure Tran ENERGY_END when v(VOUT)='"+str(targetLib.energy_meas_high_threshold)+"' rise=1  td='_tclk5'\n")
            ## case, input 10 -> output 01
            elif(((targetHarness.target_inport_val == "10")or(targetHarness.target_set_val == "10")or(targetHarness.target_reset_val == "10"))and(targetHarness.target_outport_val == "01")):
                outlines.append(".measure Tran PROP_IN_OUT trig v("+V_in_target+") val='"+str(float(targetLib.logic_high_to_low_threshold)*float(targetLib.vdd_voltage))+"' td='_tclk5' fall=1 \n")
                outlines.append("+ targ v(VOUT) val='"+str(float(targetLib.logic_low_to_high_threshold)*float(targetLib.vdd_voltage))+"' rise=1  \n")
                outlines.append(".measure Tran TRANS_OUT trig v(VOUT) val='"+str(float(targetLib.logic_threshold_low)*float(targetLib.vdd_voltage))+"' td='_tclk5' rise=1\n")
                outlines.append("+ targ v(VOUT) val='"+str(float(targetLib.logic_threshold_high)*float(targetLib.vdd_voltage ))+"' rise=1  \n")
                #outlines.append(".measure Tran ENERGY_START when v("+V_in_target+")='"+str(targetLib.energy_meas_high_threshold)+"' fall=1  td='_tclk5'\n")
                #outlines.append(".measure Tran ENERGY_END when v(VOUT)='"+str(targetLib.energy_meas_high_threshold)+"' rise=1  td='_tclk5'\n")
            ## case, input 10 -> output 10
            elif(((targetHarness.target_inport_val == "10")or(targetHarness.target_set_val == "10")or(targetHarness.target_reset_val == "10"))and(targetHarness.target_outport_val == "10")):
                outlines.append(".measure Tran PROP_IN_OUT trig v("+V_in_target+") val='"+str(float(targetLib.logic_high_to_low_threshold)*float(targetLib.vdd_voltage))+"' td='_tclk5' fall=1 \n")
                outlines.append("+ targ v(VOUT) val='"+str(float(targetLib.logic_high_to_low_threshold)*float(targetLib.vdd_voltage))+"' fall=1  \n")
                outlines.append(".measure Tran TRANS_OUT trig v(VOUT) val='"+str(float(targetLib.logic_threshold_high)*float(targetLib.vdd_voltage))+"' td='_tclk5' fall=1\n")
                outlines.append("+ targ v(VOUT) val='"+str(float(targetLib.logic_threshold_low)*float(targetLib.vdd_voltage ))+"' fall=1 \n")
                #outlines.append(".measure Tran ENERGY_START when v("+V_in_target+")='"+str(targetLib.energy_meas_high_threshold)+"' fall=1  td='_tclk5'\n")
                #outlines.append(".measure Tran ENERGY_END when v(VOUT)='"+str(targetLib.energy_meas_low_threshold)+"' fall=1  td='_tclk5'\n")
            else:
                print ("Target input of DFF is not registered for characterization!, die!")
                print ("inport_val:"+str(targetHarness.target_inport_val))
                print ("set_val:"+str(targetHarness.target_set_val))
                print ("reset_val:"+str(targetHarness.target_reset_val))
                print ("outport_val:"+str(targetHarness.target_outport_val))
                my_exit()
  
            outlines.append("* Prop delay (C2Q)\n")
            ## case, clock 01 -> output 10
            if((targetHarness.target_clock_val == "0101")and((targetHarness.target_outport_val == "10")or(targetHarness.target_set_val == "10")or(targetHarness.target_reset_val == "10"))):
                outlines.append(".measure Tran PROP_CIN_OUT trig v(VCIN) val='"+str(float(targetLib.logic_low_to_high_threshold)*float(targetLib.vdd_voltage))+"' td='_tclk5' rise=1 \n") # meas. 2nd clock
                outlines.append("+ targ v(VOUT) val='"+str(float(targetLib.logic_high_to_low_threshold)*float(targetLib.vdd_voltage))+"' fall=1 \n") 
            ## case, clock 01 -> output 01
            elif((targetHarness.target_clock_val == "0101")and((targetHarness.target_outport_val == "01")or(targetHarness.target_set_val == "01")or(targetHarness.target_reset_val == "01"))):
                outlines.append(".measure Tran PROP_CIN_OUT trig v(VCIN) val='"+str(float(targetLib.logic_low_to_high_threshold)*float(targetLib.vdd_voltage))+"' td='_tclk5' rise=1 \n") # meas. 2nd clock
                outlines.append("+ targ v(VOUT) val='"+str(float(targetLib.logic_low_to_high_threshold)*float(targetLib.vdd_voltage))+"' rise=1 \n") 
            ## case, clock 10 -> output 10
            elif((targetHarness.target_clock_val == "1010")and((targetHarness.target_outport_val == "10")or(targetHarness.target_set_val == "10")or(targetHarness.target_reset_val == "10"))):
                outlines.append(".measure Tran PROP_CIN_OUT trig v(VCIN) val='"+str(float(targetLib.logic_high_to_low_threshold)*float(targetLib.vdd_voltage))+"' td='_tclk5' fall=1 \n") # meas. 2nd clock
                outlines.append("+ targ v(VOUT) val='"+str(float(targetLib.logic_high_to_low_threshold)*float(targetLib.vdd_voltage))+"' fall=1 \n") 
            ## case, clock 10 -> output 01
            elif((targetHarness.target_clock_val == "1010")and((targetHarness.target_outport_val == "01")or(targetHarness.target_set_val == "01")or(targetHarness.target_reset_val == "01"))):
                outlines.append(".measure Tran PROP_CIN_OUT trig v(VCIN) val='"+str(float(targetLib.logic_high_to_low_threshold)*float(targetLib.vdd_voltage))+"' td='_tclk5' fall=1 \n") # meas. 2nd clock
                outlines.append("+ targ v(VOUT) val='"+str(float(targetLib.logic_low_to_high_threshold)*float(targetLib.vdd_voltage))+"' rise=1 \n") 
  
            # measure D2C(setup)
            outlines.append("* Prop delay (D2C,setup)\n")
            # case, D 01 -> CLK 01
            if(((targetHarness.target_inport_val == "01")or(targetHarness.target_set_val == "01")or(targetHarness.target_reset_val == "01"))and(targetHarness.target_clock_val == "0101")):
                outlines.append(".measure Tran PROP_IN_D2C trig v("+V_in_target+") val='"+str(float(targetLib.logic_low_to_high_threshold)*float(targetLib.vdd_voltage))+"' td='_tclk5' rise=1 \n")
                outlines.append("+ targ v(VCIN) val='"+str(float(targetLib.logic_low_to_high_threshold)*float(targetLib.vdd_voltage))+"' rise=1 \n") # meas. 2nd clock  
            # case, D 10 -> CLK 01
            elif(((targetHarness.target_inport_val == "10")or(targetHarness.target_set_val == "10")or(targetHarness.target_reset_val == "10"))and(targetHarness.target_clock_val == "0101")):
                outlines.append(".measure Tran PROP_IN_D2C trig v("+V_in_target+") val='"+str(float(targetLib.logic_high_to_low_threshold)*float(targetLib.vdd_voltage))+"' td='_tclk5' fall=1 \n")
                outlines.append("+ targ v(VCIN) val='"+str(float(targetLib.logic_low_to_high_threshold)*float(targetLib.vdd_voltage))+"' rise=1 \n") # meas. 2nd clock  
            # case, D 01 -> CLK 10
            elif(((targetHarness.target_inport_val == "01")or(targetHarness.target_set_val == "01")or(targetHarness.target_reset_val == "01"))and(targetHarness.target_clock_val == "1010")):
                outlines.append(".measure Tran PROP_IN_D2C trig v("+V_in_target+") val='"+str(float(targetLib.logic_low_to_high_threshold)*float(targetLib.vdd_voltage))+"' td='_tclk5' rise=1 \n")
                outlines.append("+ targ v(VCIN) val='"+str(float(targetLib.logic_high_to_low_threshold)*float(targetLib.vdd_voltage))+"' fall=1 \n") # meas. 2nd clock  
            # case, D 10 -> CLK 10
            elif(((targetHarness.target_inport_val == "10")or(targetHarness.target_set_val == "10")or(targetHarness.target_reset_val == "10"))and(targetHarness.target_clock_val == "1010")):
                outlines.append(".measure Tran PROP_IN_D2C trig v("+V_in_target+") val='"+str(float(targetLib.logic_high_to_low_threshold)*float(targetLib.vdd_voltage))+"' td='_tclk5' fall=1 \n")
                outlines.append("+ targ v(VCIN) val='"+str(float(targetLib.logic_high_to_low_threshold)*float(targetLib.vdd_voltage))+"' fall=1 \n") # meas. 2nd clock  
            #else:
                #print ("Skip D2C(setup) simulation")
  
            # measure C2D(HOLD)
            outlines.append("* Prop delay (C2D,HOLD)\n")
            
            # case, CLK 01 -> D (01->)10 
            if(((targetHarness.target_inport_val == "01")or(targetHarness.target_set_val == "01")or(targetHarness.target_reset_val == "01"))and(targetHarness.target_clock_val == "0101")):
                outlines.append(".measure Tran PROP_IN_C2D trig v(VCIN) val='"+str(float(targetLib.logic_low_to_high_threshold)*float(targetLib.vdd_voltage))+"' td='_tclk5' rise=1 \n") # meas. 2nd clock
                outlines.append("+ targ v("+V_in_target+") val='"+str(float(targetLib.logic_high_to_low_threshold)*float(targetLib.vdd_voltage))+"' fall=1 \n") 
            # case, CLK 01 -> D (10->)01 
            elif(((targetHarness.target_inport_val == "10")or(targetHarness.target_set_val == "10")or(targetHarness.target_reset_val == "10"))and(targetHarness.target_clock_val == "0101")):
                outlines.append(".measure Tran PROP_IN_C2D trig v(VCIN) val='"+str(float(targetLib.logic_low_to_high_threshold)*float(targetLib.vdd_voltage))+"' td='_tclk5' rise=1 \n") # meas. 2nd clock
                outlines.append("+ targ v("+V_in_target+") val='"+str(float(targetLib.logic_low_to_high_threshold)*float(targetLib.vdd_voltage))+"' rise=1 \n") 
            # case, CLK 10 -> D (01->)10 
            elif(((targetHarness.target_inport_val == "01")or(targetHarness.target_set_val == "01")or(targetHarness.target_reset_val == "01"))and(targetHarness.target_clock_val == "1010")):
                outlines.append(".measure Tran PROP_IN_C2D trig v(VCIN) val='"+str(float(targetLib.logic_high_to_low_threshold)*float(targetLib.vdd_voltage))+"' td='_tclk5' fall=1 \n") # meas. 2nd clock
                outlines.append("+ targ v("+V_in_target+") val='"+str(float(targetLib.logic_high_to_low_threshold)*float(targetLib.vdd_voltage))+"' fall=1'\n") 
            # case, CLK 10 -> D (10->)01 
            elif(((targetHarness.target_inport_val == "10")or(targetHarness.target_set_val == "10")or(targetHarness.target_reset_val == "10"))and(targetHarness.target_clock_val == "1010")):
                outlines.append(".measure Tran PROP_IN_C2D trig v(VCIN) val='"+str(float(targetLib.logic_high_to_low_threshold)*float(targetLib.vdd_voltage))+"' td='_tclk5' fall=1 \n") # meas. 2nd clock
                outlines.append("+ targ v("+V_in_target+") val='"+str(float(targetLib.logic_low_to_high_threshold)*float(targetLib.vdd_voltage))+"' rise=1\n") 
            #else:
                #print ("Skip C2D(hold) simulation")
  
            # get ENERGY_START and ENERGY_END for energy calculation in 2nd round 
            if(sim_mode == "delay"):
                outlines.append("* For energy calculation \n")
                if((targetHarness.target_inport_val == "01")or(targetHarness.target_set_val == "01")or(targetHarness.target_reset_val == "01")):
                    outlines.append(".measure Tran ENERGY_START when v("+V_in_target+")='"+str(targetLib.energy_meas_low_threshold_voltage)+"' rise=1 \n")
                elif((targetHarness.target_inport_val == "10")or(targetHarness.target_set_val == "10")or(targetHarness.target_reset_val == "10")):
                    outlines.append(".measure Tran ENERGY_START when v("+V_in_target+")='"+str(targetLib.energy_meas_high_threshold_voltage)+"' fall=1 \n")
                if(targetHarness.target_outport_val == "01"):
                    outlines.append(".measure Tran ENERGY_END when v(VOUT)='"+str(targetLib.energy_meas_high_threshold_voltage)+"' rise=1 \n")
                elif(targetHarness.target_outport_val == "10"):
                    outlines.append(".measure Tran ENERGY_END when v(VOUT)='"+str(targetLib.energy_meas_low_threshold_voltage)+"' fall=1 \n")
                if(targetHarness.target_clock_val == "0101"):
                    outlines.append(".measure Tran ENERGY_CLK_START when v(VCIN)='"+str(targetLib.energy_meas_low_threshold_voltage)+"'  rise=1 \n")
                    outlines.append(".measure Tran ENERGY_CLK_end   when v(VCIN)='"+str(targetLib.energy_meas_high_threshold_voltage)+"' rise=1 \n")
                elif(targetHarness.target_clock_val == "1010"):
                    outlines.append(".measure Tran ENERGY_CLK_START when v(VCIN)='"+str(targetLib.energy_meas_high_threshold_voltage)+"' fall=1 \n")
                    outlines.append(".measure Tran ENERGY_CLK_end   when v(VCIN)='"+str(targetLib.energy_meas_low_threshold_voltage)+"'  fall=1 \n")
  
            ##
            ## energy measurement 
            elif(sim_mode == "energy"):
                outlines.append(estart_line)
                outlines.append(eend_line)
                outlines.append(eclkstart_line)
                outlines.append(eclkend_line)
                outlines.append("* \n")
                outlines.append("** In/Out Q, Capacitance \n")
                outlines.append("* \n")
                outlines.append(".measure Tran Q_IN_DYN integ i("+V_in_target+") from='ENERGY_START' to='ENERGY_END'  \n")
                outlines.append(".measure Tran Q_OUT_DYN integ i(VOCAP) from='ENERGY_START' to='ENERGY_END*_Energy_meas_end_extent' \n")
                outlines.append(".measure Tran Q_CLK_DYN integ i(VCIN) from='ENERGY_CLK_START' to='ENERGY_CLK_END'  \n")
                outlines.append(" \n")
                outlines.append("* \n")
                outlines.append("** Energy \n")
                outlines.append("*  (Total charge, Short-Circuit Charge) \n")
                outlines.append(".measure Tran Q_VDD_DYN integ i(VDD_DYN) from='ENERGY_START' to='ENERGY_END*_Energy_meas_end_extent'  \n")
                outlines.append(".measure Tran Q_VSS_DYN integ i(VSS_DYN) from='ENERGY_START' to='ENERGY_END*_Energy_meas_end_extent'  \n")
                outlines.append(" \n")
                outlines.append("* Leakage current \n")
                outlines.append(".measure Tran I_VDD_LEAK avg i(VDD_DYN) from='_tstart1*0.1' to='_tstart1'  \n")
                outlines.append(".measure Tran I_VSS_LEAK avg i(VSS_DYN) from='_tstart1*0.1' to='_tstart1'  \n")
                outlines.append(" \n")
                outlines.append("* Gate leak current \n")
                outlines.append(".measure Tran I_IN_LEAK avg i(VIN) from='_tstart1*0.1' to='_tstart1'  \n")
            else:
                targetLib.print_error("Error, sim_mode should delay/energy/recovery/removal")
  
#	#		outlines.append(" \n")
#	#		outlines.append(" \n")
            outlines.append("XDFF VIN VCIN VRIN VSIN VOUT VHIGH VLOW VDD_DYN VSS_DYN VNW_DYN VPW_DYN DUT \n")
            outlines.append("C0 WOUT VSS_DYN 'cap'\n")
            outlines.append(" \n")
            outlines.append(".SUBCKT DUT IN CIN RIN SIN OUT HIGH LOW VDD VSS VNW VPW \n")
            # parse subckt definition
            tmp_array = targetCell.instance.split()
            tmp_line = tmp_array[0] # XDUT
            #targetLib.print_msg_sim(tmp_line)
            for w1 in tmp_array:
                # match tmp_array and harness 
                # search target inport
                is_matched = 0
                w2 = targetHarness.target_inport
                if(w1 == w2):
                    tmp_line += ' IN'
                    is_matched += 1
                # search stable inport
                for w2 in targetHarness.stable_inport:
                    if(w1 == w2):
                        # this is stable inport
                        # search index for this port
                        index_val = targetHarness.stable_inport_val[targetHarness.stable_inport.index(w2)]
                        if(index_val == '1'):
                            tmp_line += ' HIGH'
                            is_matched += 1
                        elif(index_val == '0'):
                            tmp_line += ' LOW'
                            is_matched += 1
                        else:
                            targetLib.print_msg('Illigal input value for stable input')
                # search target clock
                w2 = targetHarness.target_clock
                if(w1 == w2):
                    tmp_line += ' CIN'
                    is_matched += 1
                # search target reset
                w2 = targetHarness.target_reset
                if(w1 == w2):
                    tmp_line += ' RIN'
                    is_matched += 1
                # search target set
                w2 = targetHarness.target_set
                if(w1 == w2):
                    tmp_line += ' SIN'
                    is_matched += 1
                # search target outport
                for w2 in targetHarness.target_outport:
                    if(w1 == w2):
                        tmp_line += ' OUT'
                        is_matched += 1
                # search non-terget outport
                for w2 in targetHarness.nontarget_outport:
                    if(w1 == w2):
                        # this is non-terget outport
                        # search outdex for this port
                        index_val = targetHarness.nontarget_outport_val[targetHarness.nontarget_outport.index(w2)]
                        tmp_line += ' WFLOAT'+str(index_val)
                        is_matched += 1
                # search VDD/VSS/VNW/VPW
                if(w1.upper() == targetLib.vdd_name.upper()):
                        tmp_line += ' '+w1.upper() 
                        is_matched += 1
                if(w1.upper() == targetLib.vss_name.upper()):
                        tmp_line += ' '+w1.upper() 
                        is_matched += 1
                if(w1.upper() == targetLib.pwell_name.upper()):
                        tmp_line += ' '+w1.upper() 
                        is_matched += 1
                if(w1.upper() == targetLib.nwell_name.upper()):
                        tmp_line += ' '+w1.upper() 
                        is_matched += 1
                ## show error if this port has not matched
                if(is_matched == 0):
                    ## if w1 is wire name, abort
                    ## check this is instance tmp_array[0] or circuit name tmp_array[-1]
                    if((w1 != tmp_array[0]) and (w1 != tmp_array[-1])): 
                        targetLib.print_error("port: "+str(w1)+" has not matched in netlist parse!!")
                        
            tmp_line += " "+str(tmp_array[len(tmp_array)-1])+"\n" # CIRCUIT NAME
            outlines.append(tmp_line)
  
            outlines.append(".ends \n")
            outlines.append(" \n")
            outlines.append(cap_line)
            outlines.append(slew_line)
            outlines.append(cslew_line)
            outlines.append(tunit_line)
            outlines.append(tsetup_line)
            outlines.append(thold_line)
            outlines.append(tsimend_line)
                    
#### for ngspice batch mode 
            outlines.append("*enable .control to show graph in ngspice \n")
            outlines.append("*.control \n")
            outlines.append("*run \n")
            outlines.append("*plot V("+V_in_target+") V(VOUT) V(VCIN) \n")
            outlines.append("*.endc \n")
            outlines.append(".end \n") 
            f.writelines(outlines)
        f.close()
  
        spicelis = spicef
        spicelis += ".lis"
        spicerun = spicef
        spicerun += ".run"
#	#	spicelis.replace('.sp','.lis')
  
        # run simulation
        if(re.search("ngspice", targetLib.simulator)):
            cmd = str(targetLib.simulator)+" -b "+str(spicef)+" 1> "+str(spicelis)+" 2> /dev/null \n"
        elif(re.search("hspice", targetLib.simulator)):
            cmd = str(targetLib.simulator)+" "+str(spicef)+" -o "+str(spicelis)+" > /dev/null 2>&1\n"
        #cmd = str(targetLib.simulator)+" -b "+str(spicef)+" > "+str(spicelis)+"\n"
        with open(spicerun,'w') as f:
            outlines = []
            outlines.append(cmd) 
            f.writelines(outlines)
        f.close()
  
        cmd = ['sh', spicerun]
                
        if(targetLib.runsim == "true"):
            try:
                res = subprocess.check_call(cmd)
            except:
                targetLib.print_msg("Failed to lunch spice")

    # read results
    with open(spicelis,'r') as f:
        for inline in f:
            if(re.search("hspice", targetLib.simulator)):
                inline = re.sub('\=',' ',inline)
            #targetLib.print_msg(inline)
            # search measure
            if(not (re.search("warning*", inline)) and not (re.search("failed",inline)) and not (re.search("Error",inline))):
                if(re.search("prop_in_out", inline)): 
                    sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                    res_prop_in_out = "{:e}".format(float(sparray[2].strip()))
                elif(re.search("prop_cin_out", inline)):
                    sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                    res_prop_cin_out = "{:e}".format(float(sparray[2].strip()))
                elif(re.search("trans_out", inline)):
                    sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                    res_trans_out = "{:e}".format(float(sparray[2].strip()))
                elif(re.search("prop_in_d2c", inline)):
                    sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                    res_setup = "{:e}".format(float(sparray[2].strip()))
                elif(re.search("prop_in_c2d", inline)):
                    sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                    res_hold = "{:e}".format(float(sparray[2].strip()))
                elif(re.search("tstart2_to_tend1", inline)):
                    sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                    res_tstart2_to_tend1 = "{:e}".format(float(sparray[2].strip()))
                if(sim_mode == "delay"):
                    if(re.search("energy_start", inline)):
                        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                        res_energy_start = "{:e}".format(float(sparray[2].strip()))
                    elif(re.search("energy_end", inline)):
                        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                        res_energy_end = "{:e}".format(float(sparray[2].strip()))
                    if(re.search("energy_clk_start", inline)):
                        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                        res_energy_clk_start = "{:e}".format(float(sparray[2].strip()))
                    elif(re.search("energy_clk_end", inline)):
                        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                        res_energy_clk_end = "{:e}".format(float(sparray[2].strip()))
                if(sim_mode == "energy"):
                    if(re.search("q_in_dyn", inline)):
                        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                        res_q_in_dyn = "{:e}".format(float(sparray[2].strip()))
                    elif(re.search("q_out_dyn", inline)):
                        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                        res_q_out_dyn = "{:e}".format(float(sparray[2].strip()))
                    elif(re.search("q_clk_dyn", inline)):
                        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                        res_q_clk_dyn = "{:e}".format(float(sparray[2].strip()))
                    elif(re.search("q_vdd_dyn", inline)):
                        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                        res_q_vdd_dyn = "{:e}".format(float(sparray[2].strip()))
                    elif(re.search("q_vss_dyn", inline)):
                        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                        res_q_vss_dyn = "{:e}".format(float(sparray[2].strip()))
                    elif(re.search("i_vdd_leak", inline)):
                        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                        res_i_vdd_leak = "{:e}".format(float(sparray[2].strip()))
                    elif(re.search("i_vss_leak", inline)):
                        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                        res_i_vss_leak = "{:e}".format(float(sparray[2].strip()))
                    elif(re.search("i_in_leak", inline)):
                        sparray = re.split(" +", inline) # separate words with spaces (use re.split)
                        res_i_in_leak = "{:e}".format(float(sparray[2].strip()))


    f.close()
#	targetLib.print_msg(str(res_prop_in_out)+" "+str(res_trans_out)+" "+str(res_energy_start)+" "+str(res_energy_end)+" "+str(res_setup)+" "+str(res_hold))
    # check spice finish successfully
    try:
        res_prop_in_out
    except NameError:
        res_prop_in_out = "failed"	
    try:
        res_prop_cin_out
    except NameError:
        res_prop_cin_out = "failed"	
    try:
        res_trans_out
    except NameError:
        res_trans_out = "failed"	
    try:
        res_energy_start
    except NameError:
        res_energy_start = "failed"	
    try:
        res_energy_end
    except NameError:
        res_energy_end = "failed"	
    try:
        res_energy_clk_start
    except NameError:
        res_energy_clk_start = "failed"	
    try:
        res_energy_clk_end
    except NameError:
        res_energy_clk_end = "failed"	
    try:
        res_setup
    except NameError:
        res_setup = "failed"	
    try:
        res_hold
    except NameError:
        res_hold = "failed"	
    try:
        res_q_in_dyn
    except NameError:
        res_q_in_dyn = "failed"	
    try:
        res_q_out_dyn
    except NameError:
        res_q_out_dyn = "failed"	
    try:
        res_q_clk_dyn
    except NameError:
        res_q_clk_dyn = "failed"	
    try:
        res_q_vdd_dyn
    except NameError:
        res_q_vdd_dyn = "failed"	
    try:
        res_q_vss_dyn
    except NameError:
        res_q_vss_dyn = "failed"	
    try:
        res_i_in_leak
    except NameError:
        res_i_in_leak = "failed"	
    try:
        res_i_vdd_leak
    except NameError:
        res_i_vdd_leak = "failed"	
    try:
        res_i_vss_leak
    except NameError:
        res_i_vss_leak = "failed"	
    try:
        res_tstart2_to_tend1
    except NameError:
        res_tstart2_to_tend1 = "failed"	

    ## Overwrite res_hold if tstart2_to_tend1 is negative
    ## this is because hspice continue spice simulation 
    ## even if tstart2_to_tend1 is negative (illigal vin condition)

#	print(str(res_tstart2_to_tend1))
#	if(float(res_tstart2_to_tend1) < 0):
#		print("true1")
#	if(res_tstart2_to_tend1 == "failed"):
#		print("true2")
    if(res_tstart2_to_tend1 == "failed"):
        res_prop_in_out = "failed"
        #targetLib.print_msg_sim("Parameter res_tstart2_to_tend1 is failed, stop hold search!")
    elif(float(res_tstart2_to_tend1) < 0):
        res_prop_in_out = "failed"
        #targetLib.print_msg_sim("Time points in VIN waveform is negative, stop hold search!")

    if(sim_mode == "delay"):
        return res_prop_in_out, res_prop_cin_out, res_trans_out, \
                        res_energy_start, res_energy_end, res_energy_clk_start, res_energy_clk_end, \
                        res_setup, res_hold
                        
    if(sim_mode == "energy"):
        return res_prop_in_out, res_prop_cin_out, res_trans_out, \
                        res_setup, res_hold, \
                        res_q_in_dyn, res_q_out_dyn, res_q_clk_dyn, res_q_vdd_dyn, res_q_vss_dyn, \
                        res_i_in_leak, res_i_vdd_leak, res_i_vss_leak 
