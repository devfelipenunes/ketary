"""Distinct bounded authored applications, with analytic output contracts."""
import numpy as np
import pytest
import ketary as q

def strict(a,b):
    np.testing.assert_allclose(a,b,atol=1e-9,rtol=0)

@pytest.mark.parametrize("frequency",[1,3,6])
def test_fourier_frequency_recovery(frequency):
    n=3;N=1<<n
    c=q.Circuit(n).h(range(n))
    for w in range(n):c.p(2*np.pi*frequency*(1<<w)/N,w)
    c.apply(q.qft(n,inverse=True))
    want=np.eye(N,dtype=complex)[frequency]
    strict(c.run().math.statevector(),want)

def test_modular_order_finding_15():
    # For base 2 mod 15, multiplication on the nonzero orbit is a cyclic
    # four-bit left rotation, not a generic modular exponentiation circuit.
    c=q.Circuit(7).x(3).h([0,1,2])
    for control,rotations in ((0,1),(1,2)):
        for _ in range(rotations):
            for a,b in ((5,6),(4,5),(3,4)):c.cswap(control,a,b)
    c.apply(q.qft(3,inverse=True),wires=[0,1,2])
    r=c.run()
    want={format(k,"03b"):(.25 if k%2==0 else 0.) for k in range(8)}
    got=r.math.marginal_probabilities([2,1,0])
    strict([got[k] for k in want],list(want.values()))
    # The odd numerator over four gives the exact order on the promised orbit.
    assert pow(2,4,15)==1 and all(pow(2,k,15)!=1 for k in range(1,4))

def test_diagonal_linear_system_postselection():
    # Oracle-assisted two-eigenvalue inverse, not general HHL.
    c=q.Circuit(3).h(0).cx(0,1).ry(np.pi,2).cry(-2*np.pi/3,1,2).cx(0,1)
    state=c.run().math.statevector()
    post=state[[4,5]]
    strict(np.vdot(post,post).real,5/8)
    strict(post/np.linalg.norm(post),np.array([2,1])/np.sqrt(5))
    strict(state[[2,3,6,7]],0)

@pytest.mark.parametrize("phase",[-.61,0.,1.2])
def test_quantum_eraser_conditional_fringe(phase):
    c=q.Circuit(2).h(0).cx(0,1).p(phase,0).h([0,1])
    p=abs(c.run().math.statevector())**2
    strict(p[0]+p[2],.5)
    strict(p[0]/(p[0]+p[1]),(1+np.cos(phase))/2)
    strict(p[2]/(p[2]+p[3]),(1-np.cos(phase))/2)

@pytest.mark.parametrize("theta,phi",[(.4,.7),(1.3,-.9)])
def test_rank_two_subspace_compression(theta,phi):
    # A known two-dimensional repetition subspace, no generic learned codec.
    encoded=q.Circuit(2).ry(theta,0).p(phi,0).cx(0,1)
    state=encoded.run().math.statevector()
    compressed=encoded.copy().cx(0,1)
    want=np.array([np.cos(theta/2),np.exp(1j*phi)*np.sin(theta/2),0,0])
    strict(compressed.run().math.statevector(),want)
    strict(compressed.copy().cx(0,1).run().math.statevector(),state)
    strict(compressed.run().math.density_matrix([1]),np.diag([1.,0.]))

def test_unambiguous_binary_discrimination():
    # Three-outcome unambiguous discrimination of |0> and |+>.
    s=1/np.sqrt(2);a=np.array([np.sqrt(1-s),0,np.sqrt(s),0])
    b=np.array([0,np.sqrt(1-s),np.sqrt(s),0])
    columns=np.column_stack([a,(b-s*a)/np.sqrt(1-s*s)])
    u,_,_=np.linalg.svd(columns,full_matrices=True)
    U=np.column_stack([columns,u[:,2:]])
    strict(U.conj().T@U,np.eye(4))
    c=q.Circuit.from_unitary(U)
    for label,expected in (("00",[1-s,0,s,0]),("0+",[0,1-s,s,0])):
        strict(abs(c.run(initial_state=label).math.statevector())**2,expected)

@pytest.mark.parametrize("fidelity",[.6,.8,.95])
def test_bell_pair_bit_error_purification(fidelity):
    # Bit-error-only bilateral recurrence; no general Werner-state claim.
    success=0.;good=0.
    for a in (0,1):
        for b in (0,1):
            c=q.Circuit(4).h(0).cx(0,1).h(2).cx(2,3)
            if a:c.x(1)
            if b:c.x(3)
            c.cx(0,2).cx(1,3)
            state=c.run().math.statevector()
            weight=(fidelity if a==0 else 1-fidelity)*(fidelity if b==0 else 1-fidelity)
            for target in (0,3):
                block=state[4*target:4*target+4]
                success+=weight*np.vdot(block,block).real
                good+=weight*abs((block[0]+block[3])/np.sqrt(2))**2
    expected=fidelity**2+(1-fidelity)**2
    strict(success,expected);strict(good/success,fidelity**2/expected)
    assert good/success>fidelity

@pytest.mark.parametrize("secret",[0,1])
def test_ghz_phase_secret_sharing(secret):
    c=q.Circuit(3).h(0).cx(0,1).cx(1,2)
    if secret:c.z(0)
    r=c.run()
    for w in range(3):strict(r.math.density_matrix([w]),np.eye(2)/2)
    # Any two shares also reveal no phase bit in their reduced state.
    for wires in ([0,1],[0,2],[1,2]):strict(r.math.density_matrix(wires),np.diag([.5,0,0,.5]))
    p=abs(c.copy().h(range(3)).run().math.statevector())**2
    strict(p,[.25 if j.bit_count()%2==secret else 0 for j in range(8)])
