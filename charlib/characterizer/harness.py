"""Tools for mapping cell pins to physical states"""

class Harness:
    """Connect ports of a cell to the appropriate waveforms for a test.

    Harness maps cell ports to logic levels or transitions for a particular path through the cell.

    Keeps track of:
    - which inputs are changing
    - whether each of those inputs is rising or falling
    - which outputs are expected to change in response
    - whether each of those outputs is expected to rise or fall
    - the logic value required for each stable input
    - required level or transition for special pins, like enables, resets, and clocks"""

    def __init__(inputs: list, outputs: list, pin_state_map: dict):

