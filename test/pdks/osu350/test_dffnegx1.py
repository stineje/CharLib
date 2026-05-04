from charlib.characterizer.characterizer import Characterizer

if __name__ == "__main__":
    # Test OSU350 DFFPOSX1
    characterizer = Characterizer(**{
        'lib_name': 'OSU350_DFFNEGX1_TEST',
        'debug': True,
        'units': {
            'pulling_resistance': 'kOhm'
        },
        'named_nodes': {
            'primary_ground': {
                'name': 'GND',
            },
        },
    })
    characterizer.add_cell('DFFNEGX1', {
        'netlist': 'osu350_spice_temp/DFFNEGX1.sp',
        'models': ['model.sp'],
        'area': 384,
        'functions': ['Q<=D'],
        'state': ['IQ=Q'],
        'clock': 'negedge CLK',
        'clock_slews': [0.06, 0.3, 0.6],
        'data_slews': [0.06, 0.18, 0.42, 0.6, 1.2],
        'loads': [0.015, 0.04, 0.08, 0.2, 0.4],
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
