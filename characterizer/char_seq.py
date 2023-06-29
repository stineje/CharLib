import re, subprocess
import numpy as np

def runSequential(self, settings, harness, output_filename):
    spice_file = f'{output_filename}_rr'
    tmp_time = 10 * max(self.in_slews)
    for slew in self.in_slews:
        for load in self.out_loads:
            # Sparse C-to-Q recovery search
            if harness.target_in_port in [self.set, self.reset]:
                harness.invert_set_reset() # invert set/reset for recovery/removal sim

            # First stage: 10% output swing, imprecise search
            mag = 20 * max(self.in_slews)/min(self.in_slews)
            findSetupTime(settings, self, harness, spice_file, load, slew,
                          self.sim_setup_lowest, 2 * self.sim_setup_highest,
                          self.sim_setup_timestep * mag, tmp_time, 3)

            # Middle stage: 100% output swing, precise search
            while mag > 2:
                setup_step = self.sim_setup_timestep * mag
                setup_min = harness.results[str(slew)][str(load)]['t_setup']
                setup_max = setup_min + 2 * setup_step
                findSetupTime(settings, self, harness, spice_file, load, slew,
                              setup_min, setup_max, setup_step, tmp_time, 3)
                mag = mag / 2

            # Final stage: full precision search
            setup_min = harness.results[str(slew)][str(load)]['t_setup']
            setup_max = setup_min + 2 * mag * self.sim_setup_timestep
            findSetupTime(settings, self, harness, spice_file, load, slew,
                          setup_min, setup_max, self.sim_setup_timestep, tmp_time, 2)

            # Removal search
            if harness.target_in_port in [self.set, self.reset]:
                harness.invert_set_reset() # restore set/reset for recovery/removal sim

            # First stage: imprecise search
            mag = 20 * max(self.in_slews)/min(self.in_slews)
            findHoldTime(settings, self, harness, spice_file, load, slew, tmp_time,
                         4 * self.sim_setup_highest, self.sim_setup_lowest,
                         self.sim_hold_timestep * mag, 3)

            # Middle stage: precise search
            while mag > 2:
                hold_step = self.sim_hold_timestep * mag
                hold_max = harness.results[str(slew)][str(load)]['t_hold'] + hold_step
                hold_min = harness.results[str(slew)][str(load)]['t_hold'] - hold_step
                findHoldTime(settings, self, harness, spice_file, load, slew, tmp_time,
                             hold_max, hold_min, hold_step, 3)
                mag = mag / 2

            #Final stage: full precision search
            hold_max = harness.results[str(slew)][str(load)]['t_hold'] + 2 * mag * self.sim_hold_timestep
            hold_min = harness.results[str(slew)][str(load)]['t_hold'] - 2 * mag * self.sim_hold_timestep
            findHoldTime(settings, self, harness, spice_file, load, slew, tmp_time,
                         hold_max, hold_min, self.sim_hold_timestep, 2)

def findHoldTime(settings, cell, harness, output_filename, load, slew, setup_time, hold_max, hold_min, hold_step, timestep_scale):
    # Scaling factors for simulation
    tsimendmag_range = [1, 10]
    tranmag_range = [1.1*settings.logic_threshold_low, 1]
    prev_results = {}
    # Run a trial for each hold time within the specified range
    for t_hold in np.arange(hold_max+hold_step, hold_min-hold_step, -hold_step):
        first_stage_failed = False
        for tsimendmag, tranmag in zip(tsimendmag_range, tranmag_range):
            spice_file = f'{output_filename}_j{tranmag_range.index(tranmag)}_{load}_{slew}_setup{setup_time:,.4f}_hold{t_hold}'

            # Delay simulation
            if not first_stage_failed:
                try:
                    harness.results[str(slew)][str(load)] = runSequentialTrial(
                        settings, cell, harness, f'{spice_file}_1', load, slew,
                        setup_time, t_hold, tsimendmag, tranmag, timestep_scale
                    )
                except NameError:
                    first_stage_failed = True

            # Energy simulation
            if not first_stage_failed:
                try:
                    harness.results[str(slew)][str(load)] = runSequentialTrial(
                        settings, cell, harness, f'{spice_file}_1', load, slew,
                        setup_time, t_hold, tsimendmag, tranmag, timestep_scale,
                        True # Use energy results from previous trial
                    )
                except NameError:
                    first_stage_failed = True

        # Add hold time to harness
        harness.results[str(slew)][str(load)]['t_hold'] = t_hold

        # If we failed this iteration, use previous results
        if first_stage_failed or harness.results[str(slew)][str(load)]['prop_in_out'] >= 40*max(cell.in_slews):
            harness.results[str(slew)][str(load)] = prev_results
            # TODO: Handle the possibility that we failed on iteration 1 and don't have a hold time
            return

        # Save previous results
        prev_results = harness.results[str(slew)][str(load)]