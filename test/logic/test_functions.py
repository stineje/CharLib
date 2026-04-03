from charlib.characterizer.cell import Pin
from charlib.characterizer.logic.functions import Function

def test_noninverting_dff():
    """Verify truth table and test vectors for the noninverting function of a D flip-flop"""

    output = Pin('Q', 'output')
    inputs = [
        Pin('CLK', 'input', role='clock', edge_triggered=True),
        Pin('D', 'input')
    ]
    function = Function(output, 'D', *inputs, state='IQ')

    assert(function.expression == 'D')
    assert(function.functional_expression == 'CLK & (D) | ~CLK & IQ')
    assert(set(function.operands) == {'CLK', 'D', 'IQ'})

    expected_truth_table = [
        {'CLK': 0, 'D': 0, 'IQ': 0, 'Q': 0},
        {'CLK': 0, 'D': 0, 'IQ': 1, 'Q': 1},
        {'CLK': 0, 'D': 1, 'IQ': 0, 'Q': 0},
        {'CLK': 0, 'D': 1, 'IQ': 1, 'Q': 1},
        {'CLK': 1, 'D': 0, 'IQ': 0, 'Q': 0},
        {'CLK': 1, 'D': 0, 'IQ': 1, 'Q': 0},
        {'CLK': 1, 'D': 1, 'IQ': 0, 'Q': 1},
        {'CLK': 1, 'D': 1, 'IQ': 1, 'Q': 1},
    ]
    for row in function.truth_table():
        assert(row in expected_truth_table)
    assert(len(expected_truth_table) == len(function.truth_table()))

    expected_test_vectors = [
        {'CLK': '01', 'D': '1', 'IQ': '0', 'Q': '01'},
        {'CLK': '01', 'D': '0', 'IQ': '1', 'Q': '10'},
        {'CLK': '1', 'D': '01', 'IQ': '0', 'Q': '01'},
        {'CLK': '1', 'D': '10', 'IQ': '1', 'Q': '10'},
    ]
    for vector in function.test_vectors:
        assert(vector in expected_test_vectors)
    assert(len(expected_test_vectors) == len(function.test_vectors))

def test_inverting_dffsr():
    """Verify truth table and test vectors for the inverting output of a DFFSR

    This test uses a DFF with posedge clock and active low set & reset.
    """
    output = Pin('QN', 'output', inverted=True)
    inputs = [
        Pin('CLK', 'input', role='clock', edge_triggered=True),
        Pin('S', 'input', role='set', inverted=True),
        Pin('R', 'input', role='reset', inverted=True),
        Pin('D', 'input')
    ]
    function = Function(output, '!D', *inputs, state='IQN')

    assert(function.expression == '~D')
    assert(set(function.operands) == {'CLK', 'D', 'IQN', 'S', 'R'})

    expected_truth_table = [
        {'CLK': 0, 'D': 0, 'IQN': 0, 'S': 0, 'R': 0, 'QN': 1},
        {'CLK': 0, 'D': 0, 'IQN': 0, 'S': 0, 'R': 1, 'QN': 0},
        {'CLK': 0, 'D': 0, 'IQN': 0, 'S': 1, 'R': 0, 'QN': 1},
        {'CLK': 0, 'D': 0, 'IQN': 0, 'S': 1, 'R': 1, 'QN': 0},
        {'CLK': 0, 'D': 0, 'IQN': 1, 'S': 0, 'R': 0, 'QN': 1},
        {'CLK': 0, 'D': 0, 'IQN': 1, 'S': 0, 'R': 1, 'QN': 0},
        {'CLK': 0, 'D': 0, 'IQN': 1, 'S': 1, 'R': 0, 'QN': 1},
        {'CLK': 0, 'D': 0, 'IQN': 1, 'S': 1, 'R': 1, 'QN': 1},
        {'CLK': 0, 'D': 1, 'IQN': 0, 'S': 0, 'R': 0, 'QN': 1},
        {'CLK': 0, 'D': 1, 'IQN': 0, 'S': 0, 'R': 1, 'QN': 0},
        {'CLK': 0, 'D': 1, 'IQN': 0, 'S': 1, 'R': 0, 'QN': 1},
        {'CLK': 0, 'D': 1, 'IQN': 0, 'S': 1, 'R': 1, 'QN': 0},
        {'CLK': 0, 'D': 1, 'IQN': 1, 'S': 0, 'R': 0, 'QN': 1},
        {'CLK': 0, 'D': 1, 'IQN': 1, 'S': 0, 'R': 1, 'QN': 0},
        {'CLK': 0, 'D': 1, 'IQN': 1, 'S': 1, 'R': 0, 'QN': 1},
        {'CLK': 0, 'D': 1, 'IQN': 1, 'S': 1, 'R': 1, 'QN': 1},
        {'CLK': 1, 'D': 0, 'IQN': 0, 'S': 0, 'R': 0, 'QN': 1},
        {'CLK': 1, 'D': 0, 'IQN': 0, 'S': 0, 'R': 1, 'QN': 0},
        {'CLK': 1, 'D': 0, 'IQN': 0, 'S': 1, 'R': 0, 'QN': 1},
        {'CLK': 1, 'D': 0, 'IQN': 0, 'S': 1, 'R': 1, 'QN': 1},
        {'CLK': 1, 'D': 0, 'IQN': 1, 'S': 0, 'R': 0, 'QN': 1},
        {'CLK': 1, 'D': 0, 'IQN': 1, 'S': 0, 'R': 1, 'QN': 0},
        {'CLK': 1, 'D': 0, 'IQN': 1, 'S': 1, 'R': 0, 'QN': 1},
        {'CLK': 1, 'D': 0, 'IQN': 1, 'S': 1, 'R': 1, 'QN': 1},
        {'CLK': 1, 'D': 1, 'IQN': 0, 'S': 0, 'R': 0, 'QN': 1},
        {'CLK': 1, 'D': 1, 'IQN': 0, 'S': 0, 'R': 1, 'QN': 0},
        {'CLK': 1, 'D': 1, 'IQN': 0, 'S': 1, 'R': 0, 'QN': 1},
        {'CLK': 1, 'D': 1, 'IQN': 0, 'S': 1, 'R': 1, 'QN': 0},
        {'CLK': 1, 'D': 1, 'IQN': 1, 'S': 0, 'R': 0, 'QN': 1},
        {'CLK': 1, 'D': 1, 'IQN': 1, 'S': 0, 'R': 1, 'QN': 0},
        {'CLK': 1, 'D': 1, 'IQN': 1, 'S': 1, 'R': 0, 'QN': 1},
        {'CLK': 1, 'D': 1, 'IQN': 1, 'S': 1, 'R': 1, 'QN': 0},
    ]
    for row in function.truth_table():
        assert(row in expected_truth_table)
    assert(len(expected_truth_table) == len(function.truth_table()))

    expected_test_vectors = [
        # R->QN
        {'CLK': '0', 'D': '0', 'IQN': '0', 'S': '1', 'R': '10', 'QN': '01'},
        {'CLK': '0', 'D': '1', 'IQN': '0', 'S': '1', 'R': '10', 'QN': '01'},
        {'CLK': '1', 'D': '0', 'IQN': '0', 'S': '1', 'R': '10', 'QN': '01'},
        {'CLK': '1', 'D': '1', 'IQN': '0', 'S': '1', 'R': '10', 'QN': '01'},
        # S->QN
        {'CLK': '0', 'D': '0', 'IQN': '1', 'S': '10', 'R': '1', 'QN': '10'},
        {'CLK': '0', 'D': '1', 'IQN': '1', 'S': '10', 'R': '1', 'QN': '10'},
        {'CLK': '1', 'D': '0', 'IQN': '1', 'S': '10', 'R': '1', 'QN': '10'},
        {'CLK': '1', 'D': '1', 'IQN': '1', 'S': '10', 'R': '1', 'QN': '10'},
        # CLK->QN
        {'CLK': '01', 'D': '0', 'IQN': '0', 'S': '1', 'R': '1', 'QN': '01'},
        {'CLK': '01', 'D': '1', 'IQN': '1', 'S': '1', 'R': '1', 'QN': '10'},
        # D->QN
        {'CLK': '1', 'D': '10', 'IQN': '0', 'S': '1', 'R': '1', 'QN': '01'},
        {'CLK': '1', 'D': '01', 'IQN': '1', 'S': '1', 'R': '1', 'QN': '10'},
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
