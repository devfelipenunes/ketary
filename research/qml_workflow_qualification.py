"""Four bounded authored QML workloads, matched Qiskit and analytic oracles."""
import argparse,io,json,math,random,statistics,time,tokenize,inspect
from pathlib import Path
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector,Operator
from qiskit.circuit import Parameter
import ketary as q

TRAIN=(-1.2,-.6,.2,.8)
HELD=(-.9,-.3,.45,1.1)
PAIRS=((-1.1,-.6),(-.3,.7),(.4,-.8),(.9,1.2))

def sdk_angle(x,t):
    return q.Circuit(1).ry(x+t,0)
def native_angle(x,t):
    c=QuantumCircuit(1);c.ry(x+t,0);return c
def sdk_parity(x,y):
    return q.Circuit(2).ry([x,y],[0,1]).cx(0,1)
def native_parity(x,y):
    c=QuantumCircuit(2);c.ry(x,0);c.ry(y,1);c.cx(0,1);return c
def sdk_kernel(x,y):
    a=q.Circuit(1).ry(x,0)
    return a.compose(q.Circuit(1).ry(y,0).inverse())
def native_kernel(x,y):
    a=QuantumCircuit(1);a.ry(x,0)
    b=QuantumCircuit(1);b.ry(y,0)
    return a.compose(b.inverse())
def sdk_regression(x,t):
    a=q.Circuit.parameter("t")
    c=q.Circuit.symbolic(1).ry(a*x,0).ry(a,0)
    return c.bind({a:t})
def native_regression(x,t):
    a=Parameter("t");c=QuantumCircuit(1);c.ry(a*x,0);c.ry(a,0)
    return c.assign_parameters({a:t})

def evaluate_angle(route,points,t):
    return np.array([route(x,t).run().math.expectation("Z") for x in points])
def evaluate_native_angle(route,points,t):
    return np.array([float(abs(Statevector.from_instruction(route(x,t)).data[0])**2-
                           abs(Statevector.from_instruction(route(x,t)).data[1])**2) for x in points])
def native_z(c):
    v=Statevector.from_instruction(c).data
    return float(sum((-1 if (i>>(c.num_qubits-1))&1 else 1)*abs(a)**2 for i,a in enumerate(v)))

def angle_train(route,native=False):
    # Fixed synthetic targets, no data-dependent held-out selection.
    x=np.asarray(TRAIN);target=np.cos(x+.41);t=-.2;history=[]
    for _ in range(8):
        pred=np.array([native_z(route(float(a),t)) if native else route(float(a),t).run().math.expectation("Z") for a in x])
        # Same explicit analytic shift rule on both implementations.
        plus=np.array([native_z(route(float(a),t+np.pi/2)) if native else route(float(a),t+np.pi/2).run().math.expectation("Z") for a in x])
        minus=np.array([native_z(route(float(a),t-np.pi/2)) if native else route(float(a),t-np.pi/2).run().math.expectation("Z") for a in x])
        grad=float(np.mean((pred-target)*(plus-minus)))
        history.append((float(np.mean((pred-target)**2)),grad,t))
        t-=.3*grad
    held=np.array([native_z(route(x,t)) if native else route(x,t).run().math.expectation("Z") for x in HELD])
    return np.array(history),held,t

def analytic_angle_train():
    x=np.asarray(TRAIN);target=np.cos(x+.41);t=-.2;history=[]
    for _ in range(8):
        pred=np.cos(x+t);grad=float(np.mean(2*(pred-target)*-np.sin(x+t)))
        history.append((float(np.mean((pred-target)**2)),grad,t));t-=.3*grad
    return np.array(history),np.cos(np.asarray(HELD)+t),t

def parity_scores(route,native=False):
    return np.array([native_z(route(x,y)) if native else route(x,y).run().math.expectation("ZI") for x,y in PAIRS])
def kernel_scores(route,native=False):
    return np.array([float(abs(Statevector.from_instruction(route(x,y)).data[0])**2) if native else route(x,y).run().math.probability("0") for x,y in PAIRS])

def regression_scores(route,native=False,t=.37):
    xs=TRAIN+HELD
    pred=np.array([native_z(route(x,t)) if native else route(x,t).run().math.expectation("Z") for x in xs])
    if native:
        # occurrence-specific shift on explicitly separate native rotations.
        grad=[]
        for x in xs:
            def value(a,b):
                c=QuantumCircuit(1);c.ry(a,0);c.ry(b,0);return native_z(c)
            a,b=t*x,t
            grad.append(.5*x*(value(a+np.pi/2,b)-value(a-np.pi/2,b))+.5*(value(a,b+np.pi/2)-value(a,b-np.pi/2)))
    else:
        p=q.Circuit.parameter("t")
        grad=[q.Circuit.symbolic(1).ry(p*x,0).ry(p,0).expectation_jacobian({p:t},[q.Z(0)])[0][0] for x in xs]
    target=np.cos(np.asarray(xs)*.63+.63)
    loss=float(np.mean((pred[:4]-target[:4])**2));d_loss=float(2*np.mean((pred[:4]-target[:4])*np.asarray(grad)[:4]))
    return np.array([*pred,*grad,loss,d_loss])

def references():
    xx=np.array(TRAIN+HELD)
    pred=np.cos(.37*(xx+1));grad=-(xx+1)*np.sin(.37*(xx+1))
    target=np.cos(.63*(xx+1))
    return {"angle":np.concatenate([analytic_angle_train()[0].ravel(),analytic_angle_train()[1],[analytic_angle_train()[2]]]),
            "parity":np.array([np.cos(x)*np.cos(y) for x,y in PAIRS]),
            "kernel":np.array([np.cos((x-y)/2)**2 for x,y in PAIRS]),
            "regression":np.array([*pred,*grad,np.mean((pred[:4]-target[:4])**2),2*np.mean((pred[:4]-target[:4])*grad[:4])])}

def flatten_angle(value):
    history,held,t=value;return np.concatenate([history.ravel(),held,[t]])

def routes():
    return {
        "angle":(lambda:flatten_angle(angle_train(sdk_angle)),lambda:flatten_angle(angle_train(native_angle,True)),sdk_angle,native_angle),
        "parity":(lambda:parity_scores(sdk_parity),lambda:parity_scores(native_parity,True),sdk_parity,native_parity),
        "kernel":(lambda:kernel_scores(sdk_kernel),lambda:kernel_scores(native_kernel,True),sdk_kernel,native_kernel),
        "regression":(lambda:regression_scores(sdk_regression),lambda:regression_scores(native_regression,True),sdk_regression,native_regression),
    }

def source_metrics(fn):
    code=inspect.getsource(fn)
    tokens=[x for x in tokenize.generate_tokens(io.StringIO(code).readline) if x.type not in (tokenize.ENCODING,tokenize.ENDMARKER,tokenize.NEWLINE,tokenize.NL,tokenize.INDENT,tokenize.DEDENT,tokenize.COMMENT)]
    return dict(source=code,lines=len(code.splitlines()),tokens=len(tokens))

def evaluate(name,reps=7):
    if name not in routes() or not 3<=reps<=30:raise ValueError("bounded diagnostic")
    sdk,native,s_builder,n_builder=routes()[name]
    expected=references()[name]
    # Both builders compared on representative full operators before timing.
    args=(.3,.7);sc=s_builder(*args);nc=n_builder(*args)
    np.testing.assert_allclose(Operator(sc.to_qiskit()).data,Operator(nc).data,atol=1e-9,rtol=0)
    s=sdk();n=native()
    for got in (s,n):np.testing.assert_allclose(got,expected,atol=1e-9,rtol=0)
    classification={}
    if name=="angle":
        # Train on continuous surrogate only, evaluate fixed binary labels
        # on disjoint held-out points at a threshold fixed before fitting.
        threshold=.8
        truth=(np.cos(np.asarray(HELD)+.41)>=threshold).astype(int)
        for k,values in (("sdk",s),("native",n),("analytic",expected)):
            labels=(values[-5:-1]>=threshold).astype(int)
            classification[k]=dict(labels=labels.tolist(),accuracy=float(np.mean(labels==truth)))
        classification.update(threshold=threshold,targets=truth.tolist(),split="held-out")
        assert classification["sdk"]==classification["native"]==classification["analytic"]
    elif name=="parity":
        # The synthetic targets indicate whether the expected parity score
        # exceeds a predeclared threshold; this is not a fitted classifier.
        threshold=.5
        truth=(expected>=threshold).astype(int)
        for k,values in (("sdk",s),("native",n),("analytic",expected)):
            labels=(values>=threshold).astype(int)
            classification[k]=dict(labels=labels.tolist(),accuracy=float(np.mean(labels==truth)))
        classification.update(threshold=threshold,targets=truth.tolist(),split="fixed evaluation")
        assert classification["sdk"]==classification["native"]==classification["analytic"]
    samples={"sdk":[],"native":[]};rng=random.Random(29501);orders=[]
    for _ in range(reps):
        order=list(samples);rng.shuffle(order);orders.append(order)
        for k in order:
            fn=sdk if k=="sdk" else native
            start=time.perf_counter_ns();out=fn();samples[k].append((time.perf_counter_ns()-start)/1e6)
            np.testing.assert_allclose(out,expected,atol=1e-9,rtol=0)
    return dict(workflow=name,max_error=float(max(np.max(abs(s-expected)),np.max(abs(n-expected)))),
                sdk_source=source_metrics(s_builder),native_source=source_metrics(n_builder),
                sdk_gates=len(sc.to_qiskit().data),native_gates=len(nc.data),state_payload_bytes=16*(1<<sc.num_qubits),
                variants={k:dict(raw_ms=v,p50_ms=statistics.median(v),p95_ms=float(np.quantile(v,.95))) for k,v in samples.items()},
                classification=classification,order=orders,expected=expected.tolist(),sdk=s.tolist(),native=n.tolist())

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--repetitions",type=int,default=7);a=p.parse_args()
    rows=[]
    for name in routes():
        row=evaluate(name,a.repetitions);rows.append(row);print(json.dumps(row,allow_nan=False),flush=True)
    a.output.write_text(json.dumps(dict(scope="authored synthetic workloads; builder-only source metrics; full workload timings, no general ML or performance advantage",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
