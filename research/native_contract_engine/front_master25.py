"""R25 independent bounded experiments. Run suites separately."""
import hashlib,json,random,sys
from itertools import product
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator,Pauli,Statevector
from common5 import circuit,measure
from benchmark import label
from native9 import RustSession
from cuts21 import cuts
from certificate23 import encode as json_encode
from binary25 import encode,decode,verify
from dag22 import simulate
from expectation23 import expectation as plain_exp
from weighted25 import compress,amplitude,expectation
from recovery25 import extraction,recovery_circuit
from structures21 import recovery_table,correction
from contract_forms11 import label_mask
from semantics25 import separable,strict_equal,z_instrument
from independent20 import anticommute
import ketary_native_research as rn

def pack(gs):return bytes(v for g in gs for v in g)
def reject(f):
    try:f()
    except (ValueError,TypeError,OverflowError,rn.BudgetExceeded):return
    raise AssertionError("expected rejection")

def binary():
    checks=0;rows=[]
    for n in (2,8,16,32,64):
        gs=[g for i in range(n) for g in [(6,i,0),(4,i,0),(7,i,0),(4,i,0)]]
        g=pack(gs);s=RustSession(n,g);p=((1<<n)-1,0,0)
        cert=cuts(s,p,p,chunk=4);assert cert
        raw=encode(cert);assert decode(raw)==cert and verify(n,g,p,p,raw)
        assert not verify(n,g,p,p,raw+b"x")
        assert not verify(n,g,p,p,raw[:-1])
        # Modify first intermediate sign and recompute the checksum.
        w=(n+7)//8;mut=bytearray(raw[:-32]);mut[40+(2*w+1)+1+2*w]^=1
        forged=bytes(mut)+hashlib.sha256(mut).digest()
        assert not verify(n,g,p,p,forged)
        assert not verify(n,g+b"\x04\x00\x00",p,p,raw)
        assert not verify(n,g,p,p,raw,max_work=1)
        empty=cuts(RustSession(n,b""),p,p);assert decode(encode(empty))==empty
        rows.append({"n":n,"binary_bytes":len(raw),"json_bytes":len(json_encode(cert)),"timings":measure({"encode":lambda:encode(cert),"verify":lambda:verify(n,g,p,p,raw)},reps=15)})
        checks+=8
    return {"checks":checks,"rows":rows,"scope":"strict binary certificate, replay not authentication"}

def weighted():
    checks=0;rows=[];rng=random.Random(2501)
    for n in (2,3,4,5):
        for j in range(16):
            gs=[]
            for _ in range(20):
                a,b=rng.sample(range(n),2);op=rng.randrange(8);gs.append((op,a,b if op==5 else 0))
            d=simulate(n,pack(gs));assert d
            w=compress(d);assert w
            for i in range(1<<n):assert amplitude(w,i)==d.amplitude(i);checks+=1
            for _ in range(12):
                p=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2));a,b=expectation(w,p),plain_exp(d,p)
                assert (a.status,a.numerator,a.denominator_power)==(b.status,b.numerator,b.denominator_power);checks+=1
    for n in (16,32,64):
        for name,gs in (("uniform",[(0,i,0) for i in range(n)]),("ghz",[(0,0,0)]+[(5,0,i) for i in range(1,n)]),("phase",[(0,i,0) for i in range(n)]+[(6,i,0) for i in range(n)])):
            d=simulate(n,pack(gs),wide=True);w=compress(d);assert w
            p=(1,0,0);a,b=expectation(w,p),plain_exp(d,p)
            assert (a.numerator,a.denominator_power)==(b.numerator,b.denominator_power)
            assert expectation(w,p,max_work=1).status=="INCONCLUSIVE"
            rows.append({"n":n,"case":name,"unweighted_live":d.live_nodes(),"weighted_nodes":len(w.nodes),"timings":measure({"compress":lambda:compress(d),"weighted_expect":lambda:expectation(w,p),"plain_expect":lambda:plain_exp(d,p)},reps=9)})
            checks+=2
    return {"checks":checks,"rows":rows,"scope":"exact phase quotient after execution; no weighted gate execution"}

def simd():
    rng=random.Random(2502);checks=0;rows=[]
    for n in (2,8,32,64):
        for count in (256,4096):
            gs=[]
            for _ in range(count):
                a,b=rng.sample(range(n),2);op=rng.randrange(6);gs.append((op,a,b if op==5 else 0))
            s=RustSession(n,pack(gs));t=rn.CliffordTableau(s.native,2_000_000)
            for k in (1,63,64,65,127,128):
                ps=tuple((rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2)) for _ in range(k))
                a=s.native.clifford_images_128(ps,False,2_000_000)
                b=s.native.clifford_images_128(ps,True,2_000_000)
                assert a==b==t.images(ps,1,2_000_000);checks+=k
            rows.append({"n":n,"gates":count,"sse2":s.native.simd_available(),"timings":measure({"two_scalar_slices":lambda:s.native.clifford_images_128(ps,False,2_000_000),"simd_or_fallback":lambda:s.native.clifford_images_128(ps,True,2_000_000),"prepared_tableau":lambda:t.images(ps,1,2_000_000)},reps=21)})
    reject(lambda:s.native.clifford_images_128(ps,True,1))
    reject(lambda:RustSession(2,b"\x06\x00\x00").native.clifford_images_128(((0,0,0),),True,100))
    return {"checks":checks+2,"rows":rows,"scope":"explicit SSE2 gate scan, portable fallback, not automatically selected"}

def recovery():
    checks=0;rows=[]
    for n,labels,axes in ((3,("IZZ","ZZI"),(1,)),(5,("IXZZX","XZZXI","ZZXIX","ZXIXZ"),(1,2,3)),(7,("IIIXXXX","IXXIIXX","XIXIXIX","IIIZZZZ","IZZIIZZ","ZIZIZIZ"),(1,2,3))):
        ss=tuple(label_mask(p,n) for p in labels);m=len(ss)
        es=((0,0,0),)+tuple((int(bool(ax&1))<<i,int(bool(ax&2))<<i,0) for i in range(n) for ax in axes)
        table=recovery_table(n,ss,es);assert table.status=="PASS"
        q=extraction(n,ss);full=recovery_circuit(n,ss,es);assert full.num_clbits==m
        assert full.count_ops().get("measure")==m
        d=1<<n;P=np.eye(d,dtype=complex)
        for p in ss:P=P@(np.eye(d)+Pauli(label(n,p)).to_matrix())/2
        vals,vecs=np.linalg.eigh(P);V=vecs[:,vals>0.5];assert V.shape[1]==2
        for e in es:
            E=Pauli(label(n,e)).to_matrix();c=correction(n,ss,e,table);C=Pauli(label(n,c)).to_matrix()
            syn=sum(anticommute(e,p)<<i for i,p in enumerate(ss))
            for v in (V[:,0],V[:,1],(V[:,0]+1j*V[:,1])/np.sqrt(2)):
                start=np.zeros(1<<(n+m),complex);start[:d]=E@v
                out=Statevector(start).evolve(q).data.reshape(1<<m,d)
                assert np.linalg.norm(out[syn])>1-1e-9
                assert abs(np.vdot(v,C@out[syn]))>1-1e-9
                checks+=1
        rows.append({"n":n,"ancillas":m,"errors":len(es),"measurements":full.count_ops().get("measure"),"conditional_blocks":full.count_ops().get("if_else",0)})
    return {"checks":checks,"rows":rows,"scope":"ideal extraction circuit and branch correction validated separately; no hardware or noisy dynamic execution"}

def semantics():
    rng=random.Random(2503);checks=0
    for n in (2,3,4,5):
        for j in range(12):
            gs=[]
            for _ in range(12):
                a,b=rng.sample(range(n),2);op=rng.randrange(8);gs.append((op,a,b if op==5 else 0))
            g=pack(gs);u=Operator(circuit(n,gs).to_qiskit()).data;v=u[:,0];d=1<<n
            for mask in (1,(1<<n)-2):
                a=[i for i in range(n) if mask>>i&1];b=[i for i in range(n) if not mask>>i&1]
                mat=v.reshape((2,)*n).transpose([n-1-i for i in a+b]).reshape(1<<len(a),-1)
                rank=np.linalg.matrix_rank(mat,tol=1e-9)
                assert separable(n,g,mask).status==("PASS" if rank==1 else "FAIL");checks+=1
            assert strict_equal(n,g,g).status=="PASS"
            assert strict_equal(n,g,g+pack([(4,0,0),(3,0,0),(4,0,0),(3,0,0)])).status=="FAIL"
            checks+=2
            p=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))
            for outcome in (0,1):
                r=z_instrument(n,g,p,0,outcome);a,b,k=r
                val=lambda t:(t[0]+t[1]*np.sqrt(2))/(1<<k)
                w=v.copy();w[np.arange(d)%2!=outcome]=0
                assert abs(val(a)-np.vdot(w,w).real)<1e-9
                assert abs(val(b)-np.vdot(w,Pauli(label(n,p)).to_matrix()@w).real)<1e-9;checks+=2
    return {"checks":checks,"scope":"exact pure bipartite separability, packed strict phase, unnormalized single Z branch"}

if __name__=="__main__":
    print(json.dumps({"suite":sys.argv[1],**{"binary":binary,"weighted":weighted,"simd":simd,"recovery":recovery,"semantics":semantics}[sys.argv[1]]()},indent=2,allow_nan=False))
