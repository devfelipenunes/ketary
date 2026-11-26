"""Two-observable constrained variational workflow on a synthetic toy model.

The coefficients are deliberately synthetic, not molecular chemistry data.
The exact oracle is a separately assembled matrix and odd-sector eigensystem.
"""
import numpy as np
from scipy.optimize import minimize_scalar
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Statevector
import ketary as q

def test_toy_two_site_variational_sector():
    Z=np.diag([1.,-1.]);X=np.array([[0.,1.],[1.,0.]]);I=np.eye(2)
    H=-np.eye(4)+.4*np.kron(I,Z)-.4*np.kron(Z,I)+.1*np.kron(Z,Z)+.18*np.kron(X,X)
    parity=np.kron(Z,Z)
    energy=-q.I()+.4*q.Z(0)-.4*q.Z(1)+.1*(q.Z(0)@q.Z(1))+.18*(q.X(0)@q.X(1))
    symmetry=q.Z(0)@q.Z(1)
    a=q.Circuit.parameter("theta")
    layer=q.Circuit.symbolic(2).ry(a,0).cx(0,1)
    sdk=q.Circuit.symbolic(2).x(1).apply(layer)
    b=Parameter("theta")
    native=QuantumCircuit(2);native.x(1);native.ry(b,0);native.cx(0,1)
    expected=float(np.linalg.eigvalsh(H[np.ix_([1,2],[1,2])])[0])
    history={"ketary":[],"native":[]}
    def objective(route,x):
        x=float(x)
        if route=="ketary":
            r=sdk.bind({a:x}).run()
            values=r.math.expectations([energy,symmetry])
        else:
            v=Statevector.from_instruction(native.assign_parameters({b:x})).data
            values=tuple(float(np.vdot(v,m@v).real) for m in (H,parity))
        np.testing.assert_allclose(values[1],-1.,atol=1e-9,rtol=0)
        loss=float(values[0]+2*(values[1]+1)**2)
        history[route].append((x,*values,loss))
        return loss
    for x in (-1.4,-.3,.8,2.2):
        np.testing.assert_allclose(objective("ketary",x),objective("native",x),atol=1e-9,rtol=0)
        grad=sdk.expectation_jacobian({a:x},[energy,symmetry])
        # Initial |10>; amplitudes cos(x/2)|10>+sin(x/2)|01>.
        np.testing.assert_allclose(grad,[[-.8*np.sin(x)+.18*np.cos(x)],[0.]],atol=1e-9,rtol=0)
    for route in history:
        opt=minimize_scalar(lambda x:objective(route,x),bounds=(-np.pi,np.pi),method="bounded")
        assert opt.success and abs(opt.fun-expected)<1e-7
        assert len(history[route])>4
        r=sdk.bind({a:float(opt.x)}).run()
        q.Contract(2,expectations={energy:expected,symmetry:-1.},atol=1e-7).verify(r).require()
        assert r.math.observable_variance(energy)<1e-7
