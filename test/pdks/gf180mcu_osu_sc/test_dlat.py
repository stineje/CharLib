from charlib.characterizer.characterizer import Characterizer

if __name__ == "__main__":
    # Test gf180mcu_osu_sc 9t dff_1
    characterizer = Characterizer(**{
        'lib_name': 'gf180mcu_osu_sc_gp9t3v3__dlat_1_test',
        'debug': True,
        'multithreaded': False,
    })
    characterizer.add_cell('gf180mcu_osu_sc_gp9t3v3__dlat_1', {
        'netlist': 'globalfoundries-pdk-libs-gf180mcu_osu_sc/gf180mcu_osu_sc_gp9t3v3/spice/gf180mcu_osu_sc_gp9t3v3.spice',
        'models': ['models/sm141064.spice typical', 'models/design.spice'],
        'functions': ['Q<=D'],
        'state': ['IQ=Q'],
        'enable': 'CLK',
        'data_slews':  [0.0706, 0.1903, 0.5123, 1.3794, 3.7140],
        'loads':       [0.0013, 0.0048, 0.0172, 0.0616, 0.2206, 0.7901],
        'clock_slews': [0.0699991, 2.64574],
        'metastability_constraint_search_tolerance': 0.01,
        'metastability_constraint_search_timestep': 0.005,
        'metastability_constraint_load': 0.24,
        'metastability_constraint_sweep_samples': 40,
    })

    cell, config = characterizer.cells.pop()
    for task, *args in characterizer.analyse_cell(cell, config):
        print(task.__name__, args)
        cell_group = task(*args)
        characterizer.library.add_group(cell_group)
    print(characterizer.library.to_liberty(precision=6))
