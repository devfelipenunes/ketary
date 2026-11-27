"""Direct exact phase-weighted DAG (edge weights i**k). No dense vector.
Weights limited to quarter-turn phases; general complex weights not supported.
"""
from weighted25 import Weighted
from independent20 import ZERO,ONE,iphase,add,neg,twice,sqrt2
from dag22 import Limit

class Arena:
    def __init__(self,n,cap,work):
        self.n=n;self.cap=cap;self.left=work;self.nodes=[];self.ids={};self.zeros=[];self.memo={};self.k=0
        self.zeros.append(self.leaf(ZERO)[0])
        self.root=self.leaf(ONE)
        for l in range(1,n+1):
            z=(self.zeros[-1],0)
            self.zeros.append(self.branch(l,z,z)[0])
            self.root=self.branch(l,self.root,z)
    def charge(self):
        if self.left<=0:raise Limit("work")
        self.left-=1
    def intern(self,node):
        self.charge()
        if node not in self.ids:
            if len(self.nodes)>=self.cap:raise Limit("nodes")
            self.ids[node]=len(self.nodes);self.nodes.append(node)
        return self.ids[node]
    def iszero(self,e):
        l=self.nodes[e[0]][0]
        return l<len(self.zeros) and e[0]==self.zeros[l]
    def phase(self,e,k):
        return (e[0],0 if self.iszero(e) else (e[1]+k)%4)
    def leaf(self,a):
        k,v=min(((k,iphase(a,-k)) for k in range(4)),key=lambda x:x[1])
        return self.intern((0,v)),k
    def branch(self,l,a,b):
        k=next((e[1] for e in (a,b) if not self.iszero(e)),0)
        return self.intern((l,self.phase(a,-k),self.phase(b,-k))),k
    def children(self,e):
        l,a,b=self.nodes[e[0]]
        return l,self.phase(a,e[1]),self.phase(b,e[1])
    def linear(self,e,kind):
        self.charge()
        if self.iszero(e):return e
        key=("linear",e[0],kind)
        if key not in self.memo:
            l,*v=self.nodes[e[0]]
            if l:r=self.branch(l,self.linear(v[0],kind),self.linear(v[1],kind))
            else:
                a=v[0]
                if kind=="sqrt":b=sqrt2(a)
                elif kind=="twice":b=twice(a)
                elif kind in ("t","tdg"):
                    a=sqrt2(a);b=add(a,iphase(a,1 if kind=="t" else -1))
                else:raise ValueError("kind")
                r=self.leaf(b)
            self.memo[key]=r
        return self.phase(self.memo[key],e[1])
    def plus(self,a,b):
        self.charge()
        if self.iszero(a):return b
        if self.iszero(b):return a
        k=a[1];a=self.phase(a,-k);b=self.phase(b,-k)
        key=("plus",a,b)
        if key not in self.memo:
            l,*x=self.nodes[a[0]];m,*y=self.nodes[b[0]];assert l==m
            if l:
                _,u,v=self.children(a);_,s,t=self.children(b)
                r=self.branch(l,self.plus(u,s),self.plus(v,t))
            else:r=self.leaf(add(iphase(x[0],a[1]),iphase(y[0],b[1])))
            self.memo[key]=r
        return self.phase(self.memo[key],k)
    def single(self,e,op,target):
        self.charge()
        if self.iszero(e):return e
        key=("single",e[0],op,target)
        if key not in self.memo:
            l,a,b=self.children((e[0],0))
            if l-1>target:r=self.branch(l,self.single(a,op,target),self.single(b,op,target))
            elif l-1==target:
                if op==0:a,b=self.linear(self.plus(a,b),"sqrt"),self.linear(self.plus(a,self.phase(b,2)),"sqrt")
                elif op in (1,2,4):b=self.phase(b,{1:1,2:3,4:2}[op])
                elif op==3:a,b=b,a
                elif op in (6,7):a,b=self.linear(a,"twice"),self.linear(b,"t" if op==6 else "tdg")
                else:raise ValueError("gate")
                r=self.branch(l,a,b)
            else:raise ValueError("target")
            self.memo[key]=r
        return self.phase(self.memo[key],e[1])
    def select(self,a,b,c):
        self.charge();key=("select",a,b,c)
        if key not in self.memo:
            l,x,y=self.children(a);m,u,v=self.children(b);assert l==m
            r=self.branch(l,x,v) if l-1==c else self.branch(l,self.select(x,u,c),self.select(y,v,c))
            self.memo[key]=r
        return self.memo[key]
    def cx(self,e,c,t):
        self.charge()
        if self.iszero(e):return e
        key=("cx",e[0],c,t)
        if key not in self.memo:
            l,a,b=self.children((e[0],0))
            if l-1>max(c,t):r=self.branch(l,self.cx(a,c,t),self.cx(b,c,t))
            elif l-1==c:r=self.branch(l,a,self.single(b,3,t))
            elif l-1==t:r=self.branch(l,self.select(a,b,c),self.select(b,a,c))
            else:raise ValueError("wires")
            self.memo[key]=r
        return self.phase(self.memo[key],e[1])
    def freeze(self):
        # Retain only reachable nodes in topological order.
        live=set();todo=[self.root[0]]
        while todo:
            self.charge();i=todo.pop()
            if i in live:continue
            live.add(i);l,*v=self.nodes[i]
            if l:todo.extend(e[0] for e in v)
        ids={old:new for new,old in enumerate(sorted(live))}
        nodes=[]
        for i in sorted(live):
            self.charge();l,*v=self.nodes[i]
            nodes.append((l,*((ids[e[0]],e[1]) for e in v)) if l else (0,v[0]))
        return Weighted(self.n,self.k,(ids[self.root[0]],self.root[1]),tuple(nodes))

def simulate(n,g,*,max_nodes=65536,max_work=2_000_000):
    if type(n) is not int or not 1<=n<=64 or type(g) is not bytes or len(g)%3 or len(g)>1536 or type(max_nodes) is not int or not 1<=max_nodes<=65536 or type(max_work) is not int or not 1<=max_work<=2_000_000:raise ValueError("bounds")
    rows=tuple(zip(g[::3],g[1::3],g[2::3]))
    for op,a,b in rows:
        if op>7 or a>=n or (op==5 and (b>=n or a==b)) or (op!=5 and b!=0):raise ValueError("gate")
    try:
        arena=Arena(n,max_nodes,max_work)
        for op,a,b in rows:
            arena.root=arena.cx(arena.root,a,b) if op==5 else arena.single(arena.root,op,a)
            arena.k+=int(op in (0,6,7))
        return arena.freeze()
    except Limit:return None
