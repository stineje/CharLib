from charlib.characterizer.characterizer import Characterizer

if __name__ == "__main__":
    # Test gf180mcu_osu_sc 9t dff_1
    characterizer = Characterizer(**{
        'lib_name': 'gf180mcu_osu_sc_gp9t3v3__dff_1_test',
        'debug': True,
    })
    characterizer.add_cell('gf180mcu_osu_sc_gp9t3v3__dff_1', {
        'netlist': 'globalfoundries-pdk-libs-gf180mcu_osu_sc/gf180mcu_osu_sc_gp9t3v3/spice/gf180mcu_osu_sc_gp9t3v3.spice',
        'models': ['models/sm141064.ngspice typical', 'models/design.ngspice'],
        'functions': ['Q<=D', 'QN<=!D'],
        'state': ['IQ=Q', 'IQN=QN'],
        'clock': 'posedge CLK',
        'pairs': ['Q QN'],
        'clock_slews': [0.07, 2.5, 10],
        'loads': [0.005, 0.06, 0.2],
        'data_slews': [0.1, 0.5, 1.2],
        'setup_hold_constraint_load': 0.24,
        'sequential_n_sweep_samples': 40,
    })

    cell, config = characterizer.cells.pop()
    metastability_tasks = characterizer.settings.simulation.metastability_constraint(cell, config, characterizer.settings)
    for task, *args in metastability_tasks:
        print(task.__name__, args)
        cell_group = task(*args)
        characterizer.library.add_group(cell_group)
        break
    print(str(characterizer.library))
