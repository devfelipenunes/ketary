"""Integrated workflow checks after symbolic evolution and sweep refinements."""
import runpy
from pathlib import Path
import numpy as np
import pytest
import ketary as q
from scipy.linalg import expm

ROOT=Path(__file__).resolve().parents[1]
def test_example_end_to_end():
    example=runpy.run_path(str(ROOT/"examples/symbolic_qaoa.py"))
    rows=[[.5,.3],[.7,.4],[.9,.2]]
    n=4;edges=[(0,1),(1,2),(2,3),(3,0)];weights=[.5,1.2,.7,.9]
    cost=np.array([sum(w*(((i>>a)^(i>>b))&1) for (a,b),w in zip(edges,weights,strict=True)) for i in range(16)])
    mixer=np.zeros((16,16),complex)
    for i in range(16):
        for j in range(n):mixer[i^(1<<j),i]=1.
    wanted=[]
    for g,b in rows:
        state=expm(-1j*b*mixer)@(np.exp(-1j*g*cost)/4)
        wanted.append(float(np.vdot(state,cost*state).real))
    np.testing.assert_allclose(example["evaluate"](rows),wanted,atol=1e-9,rtol=0)

@pytest.mark.parametrize("seed",[1101,2202,3303])
def test_symbolic_mixed_phase_sweep_replay(seed):
    a,b=q.Circuit.parameter_vector("t",2)
    template=(q.Circuit.symbolic(3).h([0,1,2])
              .evolve(.7*q.Y(0)@q.X(2)+.4*q.I(),time=a)
              .evolve(q.Z(1),time=b))
    rng=np.random.default_rng(seed);rows=rng.uniform(-1,1,(3,2))
    plan=template.sweep_rows(rows)
    for row,result in zip(rows,plan.run(),strict=True):
        bound=template.bind(row)
        replay=q.Circuit.from_json(bound.to_json())
        y=np.array([[0,-1j],[1j,0]]);x=np.array([[0,1],[1,0]]);z=np.diag([1,-1]);I=np.eye(2)
        H=.7*np.kron(np.kron(x,I),y)+.4*np.eye(8)
        G=np.kron(np.kron(I,z),I)
        v=expm(-1j*row[1]*G)@expm(-1j*row[0]*H)@(np.ones(8)/np.sqrt(8))
        np.testing.assert_allclose(result.math.statevector(),v,atol=1e-9,rtol=0)
        np.testing.assert_allclose(replay.run().math.statevector(),v,atol=1e-9,rtol=0)
    assert template.parameters==(a,b)
