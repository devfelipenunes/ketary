"""Bounded research decision DAG, exact arithmetic and recovery synthesis."""
from dataclasses import dataclass
from independent20 import admit,column,correctable_pauli_set,anticommute,pauli

def normalize(v,k):
    """Canonicalize common powers of two, preserving exact values."""
    if type(k) is not int or k<0:raise ValueError("denominator")
    while k and all(c%2==0 for a in v for c in a):
        v=tuple(tuple(c//2 for c in a) for a in v);k-=1
    return v,k

@dataclass(frozen=True)
class DecisionDAG:
    nodes:tuple
    root:int
    width:int
    denominator:int

def compress(v,k,n,*,max_nodes=4096):
    """Hash-consed full binary amplitude decision DAG (unweighted).
    This is a post-compression experiment, not a scalable DD simulator."""
    if type(n) is not int or not 1<=n<=10 or type(v) is not tuple or len(v)!=1<<n or type(max_nodes) is not int or not 1<=max_nodes<=4096:raise ValueError("bounded vector")
    if any(type(a) is not tuple or len(a)!=4 or any(type(c) is not int for c in a) for a in v):raise ValueError("amplitude")
    v,k=normalize(v,k);nodes=[];ids={}
    def intern(key):
        if key not in ids:
            if len(nodes)>=max_nodes:raise OverflowError("node cap")
            ids[key]=len(nodes);nodes.append(key)
        return ids[key]
    try:
        layer=[intern(("leaf",a)) for a in v]
        for level in range(1,n+1):
            layer=[intern(("branch",level,layer[i],layer[i+1])) for i in range(0,len(layer),2)]
    except OverflowError:return None
    return DecisionDAG(tuple(nodes),layer[0],n,k)

def expand(dag):
    if type(dag) is not DecisionDAG:raise TypeError("DAG")
    def walk(i,level):
        node=dag.nodes[i]
        if level==0:
            if node[0]!="leaf":raise ValueError("leaf")
            return (node[1],)
        if node[:2]!=("branch",level) or not 0<=node[2]<i or not 0<=node[3]<i:raise ValueError("branch")
        return walk(node[2],level-1)+walk(node[3],level-1)
    return walk(dag.root,dag.width),dag.denominator

def state_dag(n,g,*,max_work=2_000_000):
    rows=admit(n,g,max_work)
    if (1<<n)*(len(rows)+3)>max_work:return None
    return compress(*column(n,rows,0),n)

@dataclass(frozen=True)
class Recovery:
    status:str
    table:tuple

def recovery_table(n,stabilizers,errors,*,max_pairs=4096):
    """Synthesize syndrome -> Pauli correction for the admitted finite set.
    Physical syndrome extraction and fault tolerance are separate."""
    r=correctable_pauli_set(n,stabilizers,errors,max_pairs=max_pairs)
    if r.status!="PASS":return Recovery(r.status,())
    table={}
    for e in errors:
        key=tuple(anticommute(e,s) for s in stabilizers)
        table.setdefault(key,e)
    return Recovery("PASS",tuple(sorted(table.items())))

def correction(n,stabilizers,error,table):
    pauli(n,error)
    if type(table) is not Recovery or table.status!="PASS":raise ValueError("recovery")
    key=tuple(anticommute(error,s) for s in stabilizers)
    return dict(table.table).get(key)
