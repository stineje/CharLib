from charlib.characterizer.cell import Pin
from charlib.characterizer.logic.functions import Function, StateFunction

def test_noninverting_dff():
    """Verify truth table and test vectors for the noninverting function of a D flip-flop"""

    expr = 'D'
    state_var = 'IQ'
    clock_pin = Pin('CLK', 'input', role='clock', edge_triggered=True)
    function = StateFunction(expr, state_var, clock=clock_pin)

    assert(function.base_expression == 'D')
    assert(function.expression == 'CLK & (D) | ~CLK & IQ')
    assert(set(function.operands) == {'CLK', 'D', 'IQ'})

    expected_truth_table = [
        {'CLK': 0, 'D': 0, 'IQ': 0, Function.OUT: 0},
        {'CLK': 0, 'D': 0, 'IQ': 1, Function.OUT: 1},
        {'CLK': 0, 'D': 1, 'IQ': 0, Function.OUT: 0},
        {'CLK': 0, 'D': 1, 'IQ': 1, Function.OUT: 1},
        {'CLK': 1, 'D': 0, 'IQ': 0, Function.OUT: 0},
        {'CLK': 1, 'D': 0, 'IQ': 1, Function.OUT: 0},
        {'CLK': 1, 'D': 1, 'IQ': 0, Function.OUT: 1},
        {'CLK': 1, 'D': 1, 'IQ': 1, Function.OUT: 1},
    ]
    for row in function.truth_table():
        assert(row in expected_truth_table)
    assert(len(expected_truth_table) == len(function.truth_table()))

    expected_test_vectors = [
        {'CLK': '01', 'D': '1', 'IQ': '0', Function.OUT: '01'},
        {'CLK': '01', 'D': '0', 'IQ': '1', Function.OUT: '10'},
    ]
    for vector in function.test_vectors:
        assert(vector in expected_test_vectors)
    assert(len(expected_test_vectors) == len(function.test_vectors))

def test_inverting_dffsr():
    """Verify truth table and test vectors for the inverting output of a DFFSR

    This test uses a DFF with posedge clock and active low set & reset.
    """
    expr = '!D'
    state_var = 'IQN'
    clock_pin = Pin('CLK', 'input', role='clock', edge_triggered=True)
    set_pin = Pin('S', 'input', role='set', inverted=True)
    reset_pin = Pin('R', 'input', role='reset', inverted=True)
    function = StateFunction(expr, state_var, clock=clock_pin, preset=set_pin, clear=reset_pin)

    assert(function.base_expression == '~D')
    assert(function.expression == 'R & (~S | (CLK & (~D) | ~CLK & IQN))')
    assert(set(function.operands) == {'CLK', 'D', 'IQN', 'S', 'R'})

    expected_truth_table = [
        {'CLK': 0, 'D': 0, 'IQN': 0, 'S': 0, 'R': 0, Function.OUT: 0},
        {'CLK': 0, 'D': 0, 'IQN': 0, 'S': 0, 'R': 1, Function.OUT: 1},
        {'CLK': 0, 'D': 0, 'IQN': 0, 'S': 1, 'R': 0, Function.OUT: 0},
        {'CLK': 0, 'D': 0, 'IQN': 0, 'S': 1, 'R': 1, Function.OUT: 0},
        {'CLK': 0, 'D': 0, 'IQN': 1, 'S': 0, 'R': 0, Function.OUT: 0},
        {'CLK': 0, 'D': 0, 'IQN': 1, 'S': 0, 'R': 1, Function.OUT: 1},
        {'CLK': 0, 'D': 0, 'IQN': 1, 'S': 1, 'R': 0, Function.OUT: 0},
        {'CLK': 0, 'D': 0, 'IQN': 1, 'S': 1, 'R': 1, Function.OUT: 1},
        {'CLK': 0, 'D': 1, 'IQN': 0, 'S': 0, 'R': 0, Function.OUT: 0},
        {'CLK': 0, 'D': 1, 'IQN': 0, 'S': 0, 'R': 1, Function.OUT: 1},
        {'CLK': 0, 'D': 1, 'IQN': 0, 'S': 1, 'R': 0, Function.OUT: 0},
        {'CLK': 0, 'D': 1, 'IQN': 0, 'S': 1, 'R': 1, Function.OUT: 0},
        {'CLK': 0, 'D': 1, 'IQN': 1, 'S': 0, 'R': 0, Function.OUT: 0},
        {'CLK': 0, 'D': 1, 'IQN': 1, 'S': 0, 'R': 1, Function.OUT: 1},
        {'CLK': 0, 'D': 1, 'IQN': 1, 'S': 1, 'R': 0, Function.OUT: 0},
        {'CLK': 0, 'D': 1, 'IQN': 1, 'S': 1, 'R': 1, Function.OUT: 1},
        {'CLK': 1, 'D': 0, 'IQN': 0, 'S': 0, 'R': 0, Function.OUT: 0},
        {'CLK': 1, 'D': 0, 'IQN': 0, 'S': 0, 'R': 1, Function.OUT: 1},
        {'CLK': 1, 'D': 0, 'IQN': 0, 'S': 1, 'R': 0, Function.OUT: 0},
        {'CLK': 1, 'D': 0, 'IQN': 0, 'S': 1, 'R': 1, Function.OUT: 1},
        {'CLK': 1, 'D': 0, 'IQN': 1, 'S': 0, 'R': 0, Function.OUT: 0},
        {'CLK': 1, 'D': 0, 'IQN': 1, 'S': 0, 'R': 1, Function.OUT: 1},
        {'CLK': 1, 'D': 0, 'IQN': 1, 'S': 1, 'R': 0, Function.OUT: 0},
        {'CLK': 1, 'D': 0, 'IQN': 1, 'S': 1, 'R': 1, Function.OUT: 1},
        {'CLK': 1, 'D': 1, 'IQN': 0, 'S': 0, 'R': 0, Function.OUT: 0},
        {'CLK': 1, 'D': 1, 'IQN': 0, 'S': 0, 'R': 1, Function.OUT: 1},
        {'CLK': 1, 'D': 1, 'IQN': 0, 'S': 1, 'R': 0, Function.OUT: 0},
        {'CLK': 1, 'D': 1, 'IQN': 0, 'S': 1, 'R': 1, Function.OUT: 0},
        {'CLK': 1, 'D': 1, 'IQN': 1, 'S': 0, 'R': 0, Function.OUT: 0},
        {'CLK': 1, 'D': 1, 'IQN': 1, 'S': 0, 'R': 1, Function.OUT: 1},
        {'CLK': 1, 'D': 1, 'IQN': 1, 'S': 1, 'R': 0, Function.OUT: 0},
        {'CLK': 1, 'D': 1, 'IQN': 1, 'S': 1, 'R': 1, Function.OUT: 0},
    ]
    for row in function.truth_table():
        assert(row in expected_truth_table)
    assert(len(expected_truth_table) == len(function.truth_table()))

    expected_test_vectors = [
        {'CLK': '0', 'D': '0', 'IQN': '1', 'S': '1', 'R': '10', Function.OUT: '10'},
        {'CLK': '0', 'D': '1', 'IQN': '1', 'S': '1', 'R': '10', Function.OUT: '10'},
        {'CLK': '1', 'D': '0', 'IQN': '1', 'S': '1', 'R': '10', Function.OUT: '10'},
        {'CLK': '1', 'D': '1', 'IQN': '1', 'S': '1', 'R': '10', Function.OUT: '10'},
        {'CLK': '0', 'D': '0', 'IQN': '0', 'S': '10', 'R': '1', Function.OUT: '01'},
        {'CLK': '0', 'D': '1', 'IQN': '0', 'S': '10', 'R': '1', Function.OUT: '01'},
        {'CLK': '1', 'D': '0', 'IQN': '0', 'S': '10', 'R': '1', Function.OUT: '01'},
        {'CLK': '1', 'D': '1', 'IQN': '0', 'S': '10', 'R': '1', Function.OUT: '01'},
        {'CLK': '01', 'D': '0', 'IQN': '0', 'S': '1', 'R': '1', Function.OUT: '01'},
        {'CLK': '01', 'D': '1', 'IQN': '1', 'S': '1', 'R': '1', Function.OUT: '10'},
    ]
    for vector in function.test_vectors:
        print(vector)
        assert(vector in expected_test_vectors)
    assert(len(expected_test_vectors) == len(function.test_vectors))


def test_noninverting_srlat():
    """Verify truth table and test vectors for the noninverting function of an SR latch"""
    pass # TODO

def test_inverting_dlat():
    """Verify truth table and test vectors for the inverting function of a D-latch"""
    pass # TODO

def test_and2():
    pass # TODO

def test_xor2():
    pass # TODO

def test_addf():
    pass # TODO
