"""Research: explicit session with one native buffer, aggregate work budget."""
import ctypes as C
from common5 import *
from engine import _verify_admitted,Native
from front_b import Session
from test_engine import native
from benchmark_engine import setup
from benchmark import invoke
class BoundNative(Native):
    def __init__(self,pre):
        super().__init__();self.pre=pre;self.buf=(C.c_uint8*len(pre.packed)).from_buffer_copy(pre.packed)
    def run(self,pre,ps,method):
        if pre is not self.pre:raise ValueError("wrong snapshot")
        if method=="scalar":return [invoke(self.scalar,self.buf,pre.width,p) for p in ps]
        m=len(ps);x=(C.c_uint64*m)(*(p[0] for p in ps));z=(C.c_uint64*m)(*(p[1] for p in ps));r=(C.c_uint8*m)(*(p[2] for p in ps))
        if self.batch(self.buf,len(self.buf)//3,pre.width,x,z,r,m):raise ValueError("native rejection")
        return list(zip(x,z,r))
def main():
    base=native();rows=[];checks=0
    for n in (16,32):
        for g in (100,1000,10000):
            c,p,obs=setup(n,g,64);s=Session(p);bound=BoundNative(p)
            for m in (1,8,64,256):
                if g*m>2_000_000:continue
                o=(obs*4)[:m]
                old=lambda:s.run(o,native=base)
                new=lambda:s.run(o,native=bound)
                assert semantic(old())==semantic(new());checks+=m
                rows.append({"n":n,"gates":g,"m":m,"timings":measure({"copy_each_chunk":old,"bound_buffer":new,"new_session_and_buffer":lambda:Session(p).run(o,native=BoundNative(p))})})
            c.z(0)
            try:bound.run(prepare(c),[obs[0].post],"scalar")
            except ValueError:pass
            else:raise AssertionError("different snapshot accepted")
    output({"scope":"research-owned FFI buffer; not a security boundary or thread safety guarantee; same reports","checks":checks,"rows":rows})
if __name__=="__main__":main()
