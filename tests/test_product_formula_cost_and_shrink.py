import numpy as np
import pytest
from research.trotter_common_basis import evaluate
from research.generated_case_shrink import minimize,ordered_case,check

@pytest.mark.parametrize("order",[1,2])
@pytest.mark.parametrize("steps",[1,4,16])
def test_common_basis_product_formula(order,steps):
    row=evaluate(1101,-.7,steps,order,3)
    assert row["native_residual"]<=1e-9 and row["common_residual"]<=1e-9
    assert row["approximation_error"]<=row["analytical_bound"]+2e-12

@pytest.mark.parametrize("seed",range(250))
def test_generated_ordered_case_with_shrink_on_failure(seed):
    n,v,rows,phase=ordered_case(seed)
    if not check(n,v,rows,phase):
        reduced=minimize(rows,lambda s:not check(n,v,s,phase))
        pytest.fail(f"seed={seed}, n={n}, phase={phase!r}, minimized={reduced!r}")

@pytest.mark.parametrize("seed",range(16))
def test_deliberate_generated_fault_reproduces(seed):
    n,v,rows,phase=ordered_case(seed)
    rows=rows+(("p",(0,),.73),)
    assert check(n,v,rows,phase)
    fails=lambda s:not check(n,v,s,phase,defect=True)
    assert fails(rows)
    reduced=minimize(rows,fails)
    assert fails(reduced["items"])
    if reduced["local_minimal"]:
        for i in range(len(reduced["items"])):
            assert not fails(reduced["items"][:i]+reduced["items"][i+1:])

def test_shrink_budget_and_nonreproducing_input():
    with pytest.raises(ValueError):minimize((1,2),lambda _:False)
    with pytest.raises(ValueError):minimize((1,2),lambda _:True,max_attempts=129)
    got=minimize(tuple(range(10)),lambda seq:9 in seq,max_attempts=1)
    assert got["attempts"]==1 and not got["local_minimal"] and 9 in got["items"]
