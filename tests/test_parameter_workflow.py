import pytest
from research.parameter_workflow import cases

@pytest.mark.parametrize("n,rows",[(2,1),(4,8),(6,32)])
def test_parameter_workflow(n,rows):
    row=cases(n,rows,1101,3)
    assert set(row["variants"])=={"manual","identity","ordered","sweep_rows","qiskit"}
    assert all(v["max_error"]<1e-9 for v in row["variants"].values())
