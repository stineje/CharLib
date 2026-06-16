from charlib.characterizer.characterizer import Characterizer

if __name__ == "__main__":
    characterizer = Characterizer(
        lib_name='osu350_dffsr_example',
        units={'pulling_resistance': 'kOhm'},
        named_nodes={'primary_ground': {'name': 'GND'}})
    characterizer.add_cell('DFFSR', {
        'netlist':      'osu350/spice/osu035_stdcells.sp',
        'models':       ['osu350/models/ami035.m'],
        'area':         704,
        'clock':        'posedge CLK',
        'set':          'negedge S',
        'reset':        'negedge R',
        'state':        ['DS0000 = Q'],
        'functions':    ['Q <= D'],
        'data_slews':   [0.06, 0.18, 0.42, 0.6, 1.2],
        'loads':        [0.015, 0.04, 0.08, 0.2, 0.4],
        'clock_slews':  [0.06, 0.3, 0.6],
        'metastability_constraint_search_tolerance': 0.01,
        'metastability_constraint_search_timestep': 0.005,
        'metastability_constraint_load': 0.24,
        'metastability_constraint_sweep_samples': 40})
    liberty = characterizer.characterize()
    print(liberty)
