"""Research-only kernels. Never imported by the installed SDK.

Inputs are already validated snapshots and bounded research fixtures.
No public API, altered payload cap, persistent cache or second simulator.
"""
import heapq
import numpy as np

def topk_reference(state,k):
    return tuple(heapq.nlargest(min(k,len(state)),range(len(state)),
                                key=lambda i:(abs(state[i])**2,-i)))

def topk_chunks(state,k,chunk):
    # Keep at most k candidates plus one block. Order by descending
    # vectorized magnitude and ascending basis index. Scalar and vector
    # complex magnitude rounding can differ: explicitly qualify the ordered
    # result against the scalar reference, especially near ties.
    selected=np.empty(0,dtype=np.int64)
    scores=np.empty(0,dtype=np.float64)
    for start in range(0,len(state),chunk):
        block=state[start:start+chunk]
        idx=np.arange(start,start+len(block),dtype=np.int64)
        p=np.abs(block)**2
        order=np.lexsort((idx,-p))[:k]
        selected=np.concatenate((selected,idx[order]))
        scores=np.concatenate((scores,p[order]))
        keep=np.lexsort((selected,-scores))[:k]
        selected,scores=selected[keep],scores[keep]
    return tuple(int(i) for i in selected)

def marginal_reference(state,n,wires,norm):
    p=(np.abs(state)**2/norm).reshape((2,)*n)
    axes=[n-1-i for i in wires]
    rest=[i for i in range(n) if i not in axes]
    return p.transpose(axes+rest).reshape(1<<len(wires),-1).sum(axis=1)

def marginal_chunks(state,wires,norm,chunk):
    out=np.zeros(1<<len(wires),dtype=np.float64)
    for start in range(0,len(state),chunk):
        block=state[start:start+chunk]
        j=np.arange(start,start+len(block),dtype=np.int64)
        labels=np.zeros(len(j),dtype=np.int64)
        for wire in wires:
            labels=(labels<<1)|((j>>wire)&1)
        out+=np.bincount(labels,weights=np.abs(block)**2/norm,minlength=len(out))
    return out

def wire_components(circuit):
    """Conservative structural partition, not a factorized simulator.

    Only inspect a bound logical native circuit without classical bits or
    layout. Any operation joining wires conservatively joins the components.
    A factorized input would be required for independent evolution.
    """
    if circuit.parameters or circuit.num_clbits or circuit.layout is not None:
        raise ValueError("expected bound logical circuit without classical bits/layout")
    from qiskit.circuit import Gate
    roots=list(range(circuit.num_qubits))
    def find(i):
        while roots[i]!=i:
            i=roots[i]
        return i
    for item in circuit.data:
        if not isinstance(item.operation,Gate) or item.clbits:
            raise ValueError("unsupported nonunitary or non-gate instruction")
        wires=[circuit.find_bit(w).index for w in item.qubits]
        if wires:
            root=find(wires[0])
            for wire in wires[1:]:
                roots[find(wire)]=root
    groups={}
    for wire in range(circuit.num_qubits):
        groups.setdefault(find(wire),[]).append(wire)
    return tuple(sorted(tuple(g) for g in groups.values()))
