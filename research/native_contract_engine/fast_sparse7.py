"""Exact sparse optimization; same output and bounds as the existing research kernel."""
from sparse import Propagation,BudgetExceeded
from benchmark import py
def propagate_fast(n,gates,p,*,max_terms=4096,max_work=2_000_000):
    if type(n) is not int or not 1<=n<=64 or type(gates) not in (tuple,list) or len(gates)>100_000:raise ValueError("width/gates")
    if type(max_terms) is not int or not 1<=max_terms<=4096 or type(max_work) is not int or not 1<=max_work<=2_000_000:raise ValueError("budget")
    if type(p) is not tuple or len(p)!=3 or any(type(v) is not int for v in p):raise ValueError("Pauli")
    x,z,r=p
    if not 0<=x<1<<n or not 0<=z<1<<n or r not in (0,1):raise ValueError("Pauli")
    tc=0
    for row in gates:
        if type(row) is not tuple or len(row)!=3 or any(type(v) is not int for v in row):raise ValueError("gate")
        op,a,b=row
        if not 0<=op<=7 or not 0<=a<n or (op==5 and (not 0<=b<n or a==b)) or (op!=5 and b!=0):raise ValueError("gate")
        tc+=op>=6
    if tc>32:raise BudgetExceeded("T-count cap")
    terms={(x,z):((-1)**r,0)};k=0;peak=1;work=0
    for op,a,b in reversed(gates):
        work+=len(terms)
        if work>max_work:raise BudgetExceeded("term-work cap")
        out={}
        def add(key,aa,bb):
            u,v=out.get(key,(0,0));pair=(u+aa,v+bb)
            if pair==(0,0):out.pop(key,None)
            else:out[key]=pair
            if len(out)>max_terms:raise BudgetExceeded("live term cap")
        if op<6:
            for (x,z),(u,v) in terms.items():
                xx,zz,sign=py([(op,a,b)],n,(x,z,0))
                out[xx,zz]=(-u,-v) if sign else (u,v)
        else:
            A=1<<a
            if not any(x&A for x,z in terms):continue
            k+=1
            for (x,z),(u,v) in terms.items():
                if not x&A:add((x,z),2*u,2*v)
                else:
                    add((x,z),2*v,u)
                    sign=1 if bool(z&A)==(op==6) else -1
                    add((x,z^A),sign*2*v,sign*u)
        terms=out;peak=max(peak,len(terms))
    return Propagation(tuple(sorted((x,z,u<<(tc-k),v<<(tc-k)) for (x,z),(u,v) in terms.items())),tc,peak,work)

