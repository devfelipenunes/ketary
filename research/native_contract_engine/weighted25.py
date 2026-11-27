"""Exact phase-weighted live DAG quotient, no dense expansion.

Edges carry i^k, k mod 4. Equivalent subgraphs under a common quarter-turn
phase share a node. This is a post-execution weighted representation, not
a general weighted-DD simulator or arbitrary complex normalization.
"""
from dataclasses import dataclass
from dag22 import Arena
from independent20 import ZERO,iphase,add,pauli
from expectation23 import cmul,conjugate,Expectation

@dataclass(frozen=True)
class Weighted:
    width:int
    denominator:int
    root:tuple
    nodes:tuple

def compress(arena,*,max_work=2_000_000,max_nodes=65536):
    if type(arena) is not Arena or type(max_work) is not int or not 1<=max_work<=2_000_000 or type(max_nodes) is not int or not 1<=max_nodes<=65536:raise ValueError("bounds")
    nodes=[];ids={};memo={};left=max_work
    class Limit(Exception):pass
    def charge():
        nonlocal left
        left-=1
        if left<0:raise Limit()
    def intern(key):
        charge()
        if key not in ids:
            if len(nodes)>=max_nodes:raise Limit()
            ids[key]=len(nodes);nodes.append(key)
        return ids[key]
    def visit(i):
        charge()
        if i in memo:return memo[i]
        l,*v=arena.nodes[i]
        if not l:
            a=v[0]
            if a==ZERO:edge=(intern((0,ZERO)),0,True)
            else:
                k,b=min(((k,iphase(a,-k)) for k in range(4)),key=lambda q:q[1])
                edge=(intern((0,b)),k,False)
        else:
            a,b=map(visit,v);k=next((e[1] for e in (a,b) if not e[2]),0)
            def normalize(e):return (e[0],0 if e[2] else (e[1]-k)%4)
            edge=(intern((l,normalize(a),normalize(b))),k,a[2] and b[2])
        memo[i]=edge;return edge
    try:r=visit(arena.root)
    except Limit:return None
    return Weighted(arena.n,arena.k,r[:2],tuple(nodes))

def amplitude(d,i):
    if type(d) is not Weighted or type(i) is not int or not 0<=i<1<<d.width:raise ValueError("input")
    j,k=d.root
    for b in reversed(range(d.width)):
        node=d.nodes[j];assert node[0]==b+1
        j,h=node[1+((i>>b)&1)];k=(k+h)%4
    return iphase(d.nodes[j][1],k),d.denominator

def expectation(d,p,*,max_work=2_000_000):
    if type(d) is not Weighted or type(max_work) is not int or not 1<=max_work<=2_000_000:raise ValueError("bounds")
    x,z,s=pauli(d.width,p);cache={};visits=0
    class Limit(Exception):pass
    def edge(a,b):
        return iphase(pair(a[0],b[0]),b[1]-a[1])
    def pair(a,b):
        nonlocal visits
        visits+=1
        if visits>max_work:raise Limit()
        key=(a,b)
        if key in cache:return cache[key]
        l,*aa=d.nodes[a];m,*bb=d.nodes[b];assert l==m
        if not l:r=cmul(conjugate(aa[0]),bb[0])
        else:
            bit=1<<(l-1);flip=int(bool(x&bit))
            r=add(edge(aa[flip],bb[0]),iphase(edge(aa[1^flip],bb[1]),2 if z&bit else 0))
        cache[key]=r;return r
    try:r=iphase(edge(d.root,d.root),(x&z).bit_count()+2*s)
    except Limit:return Expectation("INCONCLUSIVE",None,None,max_work)
    if r[2:]!=(0,0):raise ArithmeticError("imaginary expectation")
    k=2*d.denominator;a,b=r[:2]
    while k and a%2==b%2==0:a//=2;b//=2;k-=1
    return Expectation("EXACT",(a,b),k,visits)
