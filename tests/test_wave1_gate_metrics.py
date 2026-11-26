from research.circuit_rewrite_ladder import metrics

def test_gate_call_metrics_distinguish_positional_roles():
    row=metrics("c.h(0).rx(-.3,1).cx(0,1)\nc.rzz(theta,pairs=edges)\nc.run()")
    assert row["explicit_gate_calls"]==4
    assert row["positional_wire_literals"]==4
    assert row["positional_angle_literals"]==1
    assert row["calls"]==5
    assert "run" in row["attribute_call_vocabulary"]

def test_computed_inputs_are_not_literal_guesses():
    row=metrics("c.rx(2*t,i).cx(pairs=edges)")
    assert row["explicit_gate_calls"]==2
    assert row["positional_wire_literals"]==row["positional_angle_literals"]==0
