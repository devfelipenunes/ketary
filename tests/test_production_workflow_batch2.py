"""Application-oriented programs with analytic or independently constructed oracles.

A test is an authored executable fixture, not a human usability observation.
"""
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Operator,Kraus,SparsePauliOp,DensityMatrix
from scipy.linalg import expm

I=np.eye(2,dtype=complex)
X=np.array([[0,1],[1,0]],complex)
Y=np.array([[0,-1j],[1j,0]],complex)
Z=np.diag([1.,-1.]).astype(complex)
H=(X+Z)/np.sqrt(2)

def permutation(n,fn):
    U=np.zeros((1<<n,1<<n))
    for i in range(1<<n):U[fn(i),i]=1
    return U

def test_deutsch_jozsa_promise_classification():
    for oracle,want in [(q.constant_oracle(3,value=1),1.),(q.parity_oracle("101",offset=1),0.)]:
        r=q.deutsch_jozsa(oracle).run()
        assert r.math.marginal_probabilities([2,1,0])["000"]==pytest.approx(want)

def test_hidden_parity_recovery():
    secret="1011"
    r=q.bernstein_vazirani(secret).run()
    report=q.decode_bernstein_vazirani(r)
    assert report["label"]==secret and report["peak_probability"]==pytest.approx(1.)

def test_simon_period_recovery():
    secret="101";n=len(secret)
    r=q.simon(secret).run()
    distribution=r.math.marginal_probabilities([2,1,0])
    valid=[label for label in distribution if (int(label,2)&int(secret,2)).bit_count()%2==0]
    for label,p in distribution.items():assert p==pytest.approx(1/(1<<(n-1)) if label in valid else 0.)
    assert q.recover_simon(valid,n)==secret

def test_marked_set_amplitude_amplification():
    labels=["001","110"];r=q.amplitude_amplification(q.phase_oracle(labels),iterations=1).run()
    # theta=asin(sqrt(2/8))=pi/6, one Grover iterate reaches marked subspace.
    for i in range(8):
        label=format(i,"03b")
        assert r.math.probability(label)==pytest.approx(.5 if label in labels else 0.)

def test_phase_estimation_fractional_eigenphase():
    phase=5/16
    report=q.decode_phase_estimation(q.phase_estimation(phase,precision=4).run(),precision=4)
    assert report["phase"]==pytest.approx(phase)
    assert report["peak_probability"]==pytest.approx(1.)

def test_superdense_complete_message_alphabet():
    for label in ["00","01","10","11"]:
        assert q.superdense(label).run().math.probability(label)==pytest.approx(1.)

def test_teleportation_inverse_preparation():
    pytest.importorskip("qiskit_aer")
    r=q.teleportation(.82,-.53,verify=True).run_shots(shots=64,seed=71)
    assert all(label[0]=="0" for label in r.counts)
    assert q.decode_teleportation(r)["probabilities"]=={"0":1.,"1":0.}

def test_swap_test_overlap():
    t,u=.81,-.27
    c=q.Circuit(3).ry(t,1).ry(u,2).h(0).cswap(0,1,2).h(0)
    expected=(1+np.cos((t-u)/2)**2)/2
    assert c.run().math.marginal_probabilities([0])["0"]==pytest.approx(expected)

def test_hadamard_test_complex_matrix_element():
    t,p=.63,.92
    c=q.Circuit(2).h(0).ry(t,1).crz(p,0,1)
    expected=np.cos(p/2)-1j*np.cos(t)*np.sin(p/2)
    r=c.run()
    got=r.math.expectation(q.X(0))+1j*r.math.expectation(q.Y(0))
    assert got==pytest.approx(expected)

def test_reversible_full_adder():
    # Preserve a,b,c; XOR sum into bit 3 and majority carry into bit 4.
    c=q.Circuit(5).cx(0,3).cx(1,3).cx(2,3).ccx(0,1,4).ccx(0,2,4).ccx(1,2,4)
    def expected(i):
        count=(i&7).bit_count()
        return i^((count%2)<<3)^((count>=2)<<4)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,permutation(5,expected),atol=1e-9,rtol=0)

def test_unsigned_comparator_oracle():
    c=q.Circuit(5)
    for i in range(16):
        if (i&3)>(i>>2):
            zero=[w for w in range(4) if not (i>>w)&1]
            if zero:c.x(zero)
            c.mcx(range(4),4)
            if zero:c.x(zero)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,permutation(5,lambda i:i^((((i&3)>((i>>2)&3)))<<4)),atol=1e-9,rtol=0)

def test_reversible_linear_map():
    c=q.Circuit(3).cx(0,1).cx(1,2).swap(0,2)
    def expected(i):
        a,b,d=i&1,(i>>1)&1,(i>>2)&1
        return (a^b^d)|((a^b)<<1)|(a<<2)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,permutation(3,expected),atol=1e-9,rtol=0)

def test_clifford_t_toffoli_lowering():
    c=q.Circuit(3).h(2).cx(1,2).tdg(2).cx(0,2).t(2).cx(1,2).tdg(2).cx(0,2).t(1).t(2).h(2).cx(0,1).t(0).tdg(1).cx(0,1)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,permutation(3,lambda i:i^(4 if (i&3)==3 else 0)),atol=1e-9,rtol=0)

def test_coherent_entanglement_swapping():
    c=q.Circuit(4).h([0,2]).cx(0,1).cx(2,3).cx(1,2).h(1).cx(2,3).cz(1,3)
    rho=c.run().math.density_matrix([3,0])
    v=np.array([1,0,0,1])/np.sqrt(2)
    np.testing.assert_allclose(rho,np.outer(v,v),atol=1e-9,rtol=0)

def test_phase_flip_code_recovery():
    t,p=.72,-.54
    for error in [None,0,1,2]:
        c=q.Circuit(3).ry(t,0).rz(p,0).cx(0,1).cx(0,2).h([0,1,2])
        if error is not None:c.z(error)
        c.h([0,1,2]).cx(0,2).cx(0,1).ccx(1,2,0)
        v=np.array([np.exp(-.5j*p)*np.cos(t/2),np.exp(.5j*p)*np.sin(t/2)])
        np.testing.assert_allclose(c.run().math.density_matrix([0]),np.outer(v,v.conj()),atol=1e-9,rtol=0)

def test_four_qubit_error_detection_code():
    # [[4,2,2]] code space, all four logical basis states.
    for bits in [0,3,5,6]:
        v=np.zeros(16);v[bits]=v[bits^15]=1/np.sqrt(2)
        c=q.Circuit.prepare_state(v)
        for check in ["XXXX","ZZZZ"]:assert c.run().math.expectation(check)==pytest.approx(1.)
        for w in range(4):
            for axis in "xyz":
                r=getattr(c.copy(),axis)(w).run()
                assert min(r.math.expectation("XXXX"),r.math.expectation("ZZZZ"))==pytest.approx(-1.)

def test_two_qubit_pauli_tomography():
    c=q.Circuit(2).ry(.72,0).h(1).cx(0,1).rz(.81,1)
    r=c.run();basis={"I":I,"X":X,"Y":Y,"Z":Z}
    reconstructed=sum((r.math.expectation(a+b)*np.kron(basis[a],basis[b])/4 for a,b in itertools.product(basis,repeat=2)),np.zeros((4,4),complex))
    v=r.math.statevector()
    np.testing.assert_allclose(reconstructed,np.outer(v,v.conj()),atol=1e-9,rtol=0)
    assert abs(np.trace(reconstructed)-1)<1e-9

def test_helstrom_binary_state_discrimination():
    a=np.array([1.,0.]);b=np.ones(2)/np.sqrt(2)
    _,basis=np.linalg.eigh(np.outer(a,a)-np.outer(b,b))
    c=q.Circuit.from_unitary(basis.conj().T)
    success=(c.run(initial_state=a).math.probability("1")+c.run(initial_state=b).math.probability("0"))/2
    assert success==pytest.approx((1+1/np.sqrt(2))/2)

def test_bb84_basis_sifting_ideal():
    for bit,alice,bob in itertools.product([0,1],repeat=3):
        c=q.Circuit(1)
        if bit:c.x(0)
        if alice:c.h(0)
        if bob:c.h(0)
        assert c.run().math.probability(str(bit))==pytest.approx(1. if alice==bob else .5)
    # This is basis sifting only, not a security proof or protocol implementation.

def test_discrete_quantum_walk_cycle():
    c=q.Circuit(3)
    step=q.Circuit(3).h(2).ccx(2,0,1).cx(2,0).x(2).cx(2,0).ccx(2,0,1).x(2)
    c.apply(step,times=3)
    shift=permutation(3,lambda i:(i&4)|(((i&3)+(1 if i&4 else -1))%4))
    U=shift@np.kron(H,np.eye(4))
    np.testing.assert_allclose(c.run().math.statevector(),np.linalg.matrix_power(U,3)[:,0],atol=1e-9,rtol=0)

def test_fermion_jordan_wigner_anticommutation():
    n=3;ann=[];refs=[]
    for w in range(n):
        label_x=["I"]*n;label_y=["I"]*n
        for j in range(w):label_x[n-1-j]=label_y[n-1-j]="Z"
        label_x[n-1-w]="X";label_y[n-1-w]="Y"
        ann.append(SparsePauliOp.from_list([("".join(label_x),.5),("".join(label_y),.5j)]))
        A=np.zeros((1<<n,1<<n))
        for i in range(1<<n):
            if i&(1<<w):A[i^(1<<w),i]=(-1)**((i&((1<<w)-1)).bit_count())
        refs.append(A)
        np.testing.assert_allclose(ann[-1].to_matrix(),A,atol=1e-9,rtol=0)
    v=np.arange(1,9,dtype=complex);v/=np.linalg.norm(v);r=q.Result(v)
    for i,j in itertools.product(range(n),repeat=2):
        op=ann[i]@ann[j].adjoint()+ann[j].adjoint()@ann[i]
        # Simplify only zero native terms for this bounded reference.
        assert r.math.expectation_complex(op.simplify(atol=0,rtol=0))==pytest.approx(float(i==j))

def test_fermionic_hopping_excitation_transport():
    Hq=.5*(q.X(0)@q.X(1)+q.Y(0)@q.Y(1)+q.X(1)@q.X(2)+q.Y(1)@q.Y(2))
    t=.48
    r=q.Circuit(3).evolve_exact(Hq,time=t).run(initial_state="001")
    adjacency=np.array([[0,1,0],[1,0,1],[0,1,0]],float)
    v=expm(-1j*t*adjacency)[:,0];expected=np.zeros(8,complex);expected[[1,2,4]]=v
    np.testing.assert_allclose(r.math.statevector(),expected,atol=1e-9,rtol=0)

@pytest.mark.parametrize("t,U,hop",[(.32,1.7,.8),(-.32,1.7,.8),(.17,.9,1.1)])
def test_two_site_hubbard_number_conservation(t,U,hop):
    n=4
    number=lambda w:(q.I(3)-q.Z(w))*.5
    Hq=-hop*.5*(q.X(0)@q.X(1)+q.Y(0)@q.Y(1)+q.X(2)@q.X(3)+q.Y(2)@q.Y(3))+U*((number(0)@number(2))+(number(1)@number(3)))
    # Number operators overlap only in identities; the disjoint tensor is valid.
    M=np.zeros((16,16))
    for i in range(16):
        bits=[(i>>w)&1 for w in range(4)]
        M[i,i]=U*(bits[0]*bits[2]+bits[1]*bits[3])
        for a,b in [(0,1),(2,3)]:
            if bits[a]!=bits[b]:M[i^((1<<a)|(1<<b)),i]=-hop
    c=q.Circuit(n).evolve_exact(Hq,time=t)
    exact=expm(-1j*t*M)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,exact,atol=1e-9,rtol=0)
    r=c.run(initial_state="0101")
    expected=exact[:,5]
    np.testing.assert_allclose(r.math.statevector(),expected,atol=1e-9,rtol=0)
    assert sum(r.math.probability(format(i,"04b")) for i in range(16) if i.bit_count()!=2)<1e-9

def test_quantum_fisher_metrology_scaling():
    t=q.Circuit.parameter("t")
    ghz=q.Circuit.symbolic(3).apply(q.ghz(3)).rz(t,[0,1,2])
    separable=q.Circuit.symbolic(3).h([0,1,2]).rz(t,[0,1,2])
    assert 4*np.real(ghz.quantum_geometric_tensor({t:.33})[0][0])==pytest.approx(9.)
    assert 4*np.real(separable.quantum_geometric_tensor({t:.33})[0][0])==pytest.approx(3.)

def test_natural_gradient_rank_deficient_update():
    a,b=q.Circuit.parameter_vector("v",2);x,y=.4,.2;eta=.1
    c=q.Circuit.symbolic(1).ry(a+b,0)
    bindings={a:x,b:y}
    G=np.array(c.quantum_geometric_tensor(bindings)).real
    grad=np.array(c.expectation_jacobian(bindings,[q.Z(0)]))[0]
    delta=-eta*np.linalg.pinv(G,rcond=1e-12)@grad
    np.testing.assert_allclose(delta,[2*eta*np.sin(x+y)]*2,atol=1e-9,rtol=0)
    assert c.bind({a:x+delta[0],b:y+delta[1]}).run().math.expectation("Z")<np.cos(x+y)

def test_discrete_geometric_phase_loop():
    theta=.9;angles=[0.,2*np.pi/3,4*np.pi/3]
    states=[q.Circuit(1).ry(theta,0).p(phi,0).run().math.statevector() for phi in angles]
    product=np.prod([np.vdot(states[i],states[(i+1)%3]) for i in range(3)])
    expected=(np.cos(theta/2)**2+np.exp(2j*np.pi/3)*np.sin(theta/2)**2)**3
    assert product==pytest.approx(expected)

def test_depolarizing_fixed_point():
    p=.27
    channel=Kraus([np.sqrt(1-p)*I]+[np.sqrt(p/3)*A for A in [X,Y,Z]])
    c=q.Circuit(1).ry(.71,0).rz(.33,0)
    v=c.run().math.statevector();rho=np.outer(v,v.conj())
    expected=(1-4*p/3)*rho+(2*p/3)*I
    np.testing.assert_allclose(c.run_channel(channel).data,expected,atol=1e-9,rtol=0)
    np.testing.assert_allclose(q.Circuit(1).run_channel(channel,DensityMatrix(I/2)).data,I/2,atol=1e-9)

def test_dense_hamiltonian_bad_native_output_fails_atomically(monkeypatch):
    import qiskit
    source=q.Circuit(4).h(0)
    before=Operator(source.to_qiskit()).data.copy()
    monkeypatch.setattr(qiskit,"transpile",lambda *args,**kwargs:qiskit.QuantumCircuit(4))
    with pytest.raises(q.UnsupportedOperation,match="strict synthesized operator residual"):
        source.evolve_exact(.7*q.X(0)+.3*q.Z(1),time=.4)
    np.testing.assert_array_equal(Operator(source.to_qiskit()).data,before)
