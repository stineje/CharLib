@register
def sequential_setup_hold_complex(cell, cell_settings, charlib_settings):
    """procedure for measuring setup and hold time
    This function returns (yield) jobs to be submitted to the PoolExecutor"""
    for variation in cell_settings.variations('data_slews', 'clock_slews'):
        for path in cell.paths():
            yield (sweep_setup_hold_skew_for_c2q, cell, cell_settings, charlib_settings, variation, path)

def sequential_setup_hold_search(cell, config, settings, variation, path):
    """The goal of this fucntion is to find the minimum setup and hold time of a sequential cell,
    give an input transition and output load.

    Terminology used here :
    - clock-to-q delay = C2Q = c2q
    - setup skew = the amount of D2C set in simulation, usually becomes setup time
    - hold skew = the amount of C2D set in simulation, usually becomes hold time

    The following few terminologies are used in this very important paper : https://ieeexplore.ieee.org/document/4167994
    - minimum hold pair = MHP 
    - minimum setup pair = MSP
    - minimum setup & hold pair = MSHP = the pair of setup and hold time where the sum of the two
                                         is the smallest out of the sum from all other pairs on the same contour   
                                         on the same contour (i.e. same C2Q)
    
    The big picture steps taken here, which does not completely reflect what the paper define is :
    1. Find the 3D C2Q vs setup time (ts) vs hold time (th) surface.
    2. Find a setup skew vs hold skew contour by selecting C2Q based on boundry conditions.
    3. Find one point on the contour (MSHP) for our LIBERTY library

    =======================
    = The steps in detail =
    =======================
    * assumption : smallest setup time always cooresponds to the largest hold time, vice versa
    * terminology : to the rigth means increase in time, to the left means decrease in time

    1. find min setup skew : infinite hold skew, binary search to the right for min setup time
    2. find max hold skew to run the cell : min setup skew, binary search to the left for max hold time 
    3. save pulse width (setup skew + hold skew) from the last run, keep moving the window to the left by 
       a binary search.
       During the binary search, if there is no transition on Q, double the setup skew (which also increase the pulse width).
       Algorithm stops when setup skew has been increased 5 times and there is still no transition on Q. 
       This means we have hit the smallest hold possible, the smallest hold time is hold skew from the second last run.
    4. take minimum min hold skew and increase setup skew to the left until the C2Q curve flattens out. 
       Check that the C2Q curve flattens out by checking the slope of the C2Q curve.
       
    After these few steps, we should have the boundries for 3D C2Q vs setup time (ts) vs hold time (th) surface.
    """
    pass


def sweep_setup_hold_skew_for_c2q(cell, config, settings, variation, path):
    """This function takes a range of setup skew and a range of hold skew,
    and runs every single combination of the two to find the C2Q delay.
    Giving us the 3D C2Q vs setup time (ts) vs hold time (th) surface.
    """
    t_setup_skew_range = (0e-12, 700e-12)
    t_setup_skew_step = 10e-12
    t_hold_skew_range = (-500e-12, 200e-12)
    t_hold_skew_step = 10e-12

    setup_skews = np.arange(t_setup_skew_range[0], t_setup_skew_range[1], t_setup_skew_step)
    hold_skews = np.arange(t_hold_skew_range[0], t_hold_skew_range[1], t_hold_skew_step)

    t_stabilizing = 10 * (variation['clock_slew'] * settings.units.time).value
    debug_path = None
    if settings.debug:
        debug_path = settings.debug_dir / cell.name / __name__.split('.')[-1] / f'{path[0]}_{path[1]}_to_{path[2]}_{path[3]}'
        debug_path.mkdir(parents=True, exist_ok=True)
    for state_map in cell.nonmasking_conditions_for_path(*path):
        c2q_values = []
        for t_setup_skew in setup_skews:
            c2q_hold_skew_values = []
            for t_hold_skew in hold_skews:
                t_c2q = get_c2q(cell, config, settings, variation['clock_slew'], variation['data_slew'], t_setup_skew, t_hold_skew, 40e-15, t_stabilizing, state_map, debug_path)
                c2q_hold_skew_values.append(float(t_c2q))
            c2q_values.append(c2q_hold_skew_values)

        if debug_path is not None:
            plot_c2q_surface(setup_skews, hold_skews, np.array(c2q_values), cell.name, debug_path)
            write_c2q_csv(setup_skews, hold_skews, c2q_values, cell.name, debug_path)

    return cell.liberty

def write_c2q_csv(setup_skews, hold_skews, c2q_values, cell_name, debug_path):
    """Write C2Q delay data to a CSV file with columns: setup_skew, hold_skew, c2q."""
    with open(debug_path / f'{cell_name}_c2q.csv', 'w', newline='') as f:
        writer = csv.writer(f, delimiter=' ')
        writer.writerow(['setup_skew', 'hold_skew', 'c2q'])
        for i, t_setup in enumerate(setup_skews):
            for j, t_hold in enumerate(hold_skews):
                writer.writerow([t_setup, t_hold, c2q_values[i][j]])

def plot_c2q_surface(setup_skews, hold_skews, c2q_values, cell_name, debug_path):
    """Plot C2Q delay as a 3D surface over setup_skew and hold_skew."""
    setup_grid, hold_grid = np.meshgrid(setup_skews * 1e9, hold_skews * 1e9, indexing='ij')
    c2q_ns = c2q_values * 1e9

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_surface(hold_grid, setup_grid, c2q_ns, cmap='viridis', edgecolor='none', alpha=0.9)

    # Plot red dots where C2Q failed to converge (NaN)
    nan_mask = np.isnan(c2q_ns)
    if np.any(nan_mask):
        z_min = np.nanmin(c2q_ns) if not np.all(nan_mask) else 0
        ax.scatter(hold_grid[nan_mask], setup_grid[nan_mask],
                   np.full(np.sum(nan_mask), z_min), color='red', s=20, label='did not converge')
        ax.legend()

    ax.set_xlabel('Hold Skew (ns)')
    ax.set_ylabel('Setup Skew (ns)')
    ax.invert_yaxis()
    ax.set_zlabel('C2Q Delay (ns)')
    ax.set_title(f'{cell_name} — C2Q vs Setup Skew vs Hold Skew')
    fig.colorbar(surf, ax=ax, shrink=0.5, label='C2Q (ns)')

    plt.tight_layout()
    plt.savefig(debug_path / f'{cell_name}_c2q_surface.png', dpi=150)
    plt.close(fig)
