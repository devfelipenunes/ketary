"""Conservative simultaneous confidence intervals for IID classical shots."""
from dataclasses import dataclass
from collections.abc import Mapping
import math
from ._validation import _int,_real,ResourceLimit
from ._classical import ShotResult
from ._contracts import _predicates

@dataclass(frozen=True,init=False)
class StatisticalContract:
    num_clbits: int
    probabilities: tuple[tuple[str,float], ...]
    margin: float
    confidence: float

    def __init__(self,num_clbits,*,probabilities,margin=.1,confidence=.95):
        n=_int(num_clbits,1)
        if n>12:
            raise ResourceLimit("statistical width exceeds twelve")
        p=_predicates(probabilities,n,"01",0,1)
        if not p or math.fsum(v for _,v in p)>1+1e-12:
            raise ValueError("expected nonempty consistent probability targets")
        m,c=_real(margin),_real(confidence)
        if not 0<m<1 or not 0<c<1:
            raise ValueError("margin/confidence must lie strictly between zero and one")
        for key,value in (("num_clbits",n),("probabilities",p),("margin",m),("confidence",c)):
            object.__setattr__(self,key,value)

    def verify(self,result):
        from ._reports import StatisticalReport
        return StatisticalReport(self._verify(result))

    def _verify(self,result):
        """Hoeffding + union bound over prespecified marginal outcome events.

        PASS requires every simultaneous interval inside its tolerance band;
        FAIL requires a disjoint interval; overlap is INCONCLUSIVE. Assumes IID
        shots and fixed hypotheses, not optional stopping or arbitrary hardware.
        """
        if not isinstance(result,ShotResult):
            raise TypeError("expected ShotResult")
        if result.num_clbits!=self.num_clbits:
            raise ValueError("classical width mismatch")
        if set(result.measured_bits)!=set(range(self.num_clbits)):
            return {"status":"UNSUPPORTED","reason":"not all classical bits were measured"}
        counts=result.counts
        shots=_int(result.shots,1)
        if len(result._counts)!=len(counts) or any(
            type(k) is not str or len(k)!=self.num_clbits or set(k)-set("01")
            or type(v) is not int or v<0 for k,v in counts.items()) or sum(counts.values())!=shots:
            raise ValueError("invalid shot counts")
        radius=math.sqrt(math.log(2*len(self.probabilities)/(1-self.confidence))/(2*shots))
        rows={}
        for label,p in self.probabilities:
            estimate=counts.get(label,0)/shots
            lo,hi=max(0,estimate-radius),min(1,estimate+radius)
            target_lo,target_hi=max(0,p-self.margin),min(1,p+self.margin)
            status="FAIL" if hi<target_lo or lo>target_hi else "PASS" if lo>=target_lo and hi<=target_hi else "INCONCLUSIVE"
            rows[label]={"status":status,"estimate":estimate,"interval":[lo,hi],"target_band":[target_lo,target_hi]}
        statuses={v["status"] for v in rows.values()}
        return {"schema_version":1,"scope":"prespecified outcome probabilities; IID shots assumed",
                "method":"Hoeffding union bound","status":"FAIL" if "FAIL" in statuses else "INCONCLUSIVE" if "INCONCLUSIVE" in statuses else "PASS",
                "shots":shots,"confidence":self.confidence,"checks":rows}
