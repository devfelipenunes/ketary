"""Direct exact amplitude DAG operations; bounded unweighted research backend.

All nodes are interned, operations are memoized on subgraphs, no dense
vector is created by the engine. Historical nodes count against the cap.
Global denominator may grow; no weighted edges or general rotations.
"""
from functools import lru_cache
from independent20 import ZERO,ONE,add,neg,twice,sqrt2,iphase

class Limit(Exception):pass

class Arena:
    def __init__(self,n,cap=65536,work=2_000_000):
        if type(n) is not int or not 1<=n<=20 or type(cap) is not int or not 1<=cap<=65536 or type(work) is not int or not 1<=work<=2_000_000:raise ValueError("limits")
        self.n=n;self.cap=cap;self.remaining=work;self.nodes=[];self.ids={};self.k=0
        self.memo={}
        zero=self.leaf(ZERO);root=self.leaf(ONE)
        for level in range(1,n+1):
            root=self.branch(level,root,zero);zero=self.branch(level,zero,zero)
        self.root=root
    def charge(self):
        if self.remaining<1:raise Limit("work")
        self.remaining-=1
    def intern(self,key):
        self.charge()
        if key not in self.ids:
            if len(self.nodes)>=self.cap:raise Limit("node cap")
            self.ids[key]=len(self.nodes);self.nodes.append(key)
        return self.ids[key]
    def leaf(self,a):return self.intern((0,a))
    def branch(self,l,a,b):return self.intern((l,a,b))
    def children(self,i):return self.nodes[i][1:]
    def mapped(self,i,kind):
        self.charge();key=("map",i,kind)
        if key in self.memo:return self.memo[key]
        l,*v=self.nodes[i]
        if l:
            a,b=v;r=self.branch(l,self.mapped(a,kind),self.mapped(b,kind))
        else:
            a=v[0]
            if kind=="neg":b=neg(a)
            elif kind=="i":b=iphase(a,1)
            elif kind=="-i":b=iphase(a,3)
            elif kind=="twice":b=twice(a)
            elif kind=="sqrt":b=sqrt2(a)
            elif kind=="t":b=add(sqrt2(a),iphase(sqrt2(a),1))
            elif kind=="tdg":b=add(sqrt2(a),iphase(sqrt2(a),3))
            else:raise ValueError("map")
            r=self.leaf(b)
        self.memo[key]=r;return r
    def plus(self,a,b):
        self.charge();key=("plus",a,b)
        if key in self.memo:return self.memo[key]
        l,*x=self.nodes[a];m,*y=self.nodes[b]
        assert l==m
        r=self.branch(l,self.plus(x[0],y[0]),self.plus(x[1],y[1])) if l else self.leaf(add(x[0],y[0]))
        self.memo[key]=r;return r
    def single(self,i,op,target):
        self.charge();key=("single",i,op,target)
        if key in self.memo:return self.memo[key]
        l,a,b=self.nodes[i]
        if l-1>target:r=self.branch(l,self.single(a,op,target),self.single(b,op,target))
        elif l-1==target:
            if op==0:a,b=self.mapped(self.plus(a,b),"sqrt"),self.mapped(self.plus(a,self.mapped(b,"neg")),"sqrt")
            elif op==1:b=self.mapped(b,"i")
            elif op==2:b=self.mapped(b,"-i")
            elif op==3:a,b=b,a
            elif op==4:b=self.mapped(b,"neg")
            elif op in (6,7):a,b=self.mapped(a,"twice"),self.mapped(b,"t" if op==6 else "tdg")
            else:raise ValueError("op")
            r=self.branch(l,a,b)
        else:raise ValueError("target")
        self.memo[key]=r;return r
    def select(self,a,b,control):
        """Pointwise choose a on control=0, b on control=1."""
        self.charge();key=("select",a,b,control)
        if key in self.memo:return self.memo[key]
        l,x,y=self.nodes[a];m,u,v=self.nodes[b];assert l==m
        if l-1==control:r=self.branch(l,x,v)
        else:r=self.branch(l,self.select(x,u,control),self.select(y,v,control))
        self.memo[key]=r;return r
    def cx(self,i,c,t):
        self.charge();key=("cx",i,c,t)
        if key in self.memo:return self.memo[key]
        l,a,b=self.nodes[i]
        if l-1>max(c,t):r=self.branch(l,self.cx(a,c,t),self.cx(b,c,t))
        elif l-1==c:r=self.branch(l,a,self.single(b,3,t))
        elif l-1==t:r=self.branch(l,self.select(a,b,c),self.select(b,a,c))
        else:raise ValueError("wires")
        self.memo[key]=r;return r
    def gate(self,op,a,b):
        if any(type(i) is not int for i in (op,a,b)) or not 0<=op<=7 or not 0<=a<self.n or (op==5 and (not 0<=b<self.n or a==b)) or (op!=5 and b!=0):raise ValueError("gate")
        if self.k>=512:raise Limit("denominator")
        root=self.cx(self.root,a,b) if op==5 else self.single(self.root,op,a)
        self.root=root;self.k+=int(op in (0,6,7))
    def amplitude(self,i):
        if type(i) is not int or not 0<=i<1<<self.n:raise ValueError("index")
        node=self.root
        for bit in reversed(range(self.n)):node=self.nodes[node][1+((i>>bit)&1)]
        return self.nodes[node][1],self.k
    def live_nodes(self):
        seen=set();todo=[self.root]
        while todo:
            i=todo.pop()
            if i in seen:continue
            seen.add(i)
            if self.nodes[i][0]:todo.extend(self.children(i))
        return len(seen)

def simulate(n,packed,*,cap=65536,work=2_000_000):
    if type(packed) is not bytes or len(packed)%3 or len(packed)>1536:raise ValueError("snapshot")
    # Validate all gates before any cap-triggered inconclusive result.
    rows=tuple(zip(packed[::3],packed[1::3],packed[2::3]))
    if type(n) is not int or not 1<=n<=20:raise ValueError("width")
    for op,a,b in rows:
        if op>7 or a>=n or (op==5 and (b>=n or a==b)) or (op!=5 and b!=0):raise ValueError("gate")
    try:
        arena=Arena(n,cap,work)
        for op,a,b in rows:arena.gate(op,a,b)
        return arena
    except Limit:return None
