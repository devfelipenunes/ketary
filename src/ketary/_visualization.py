"""Small dependency-free SVG renderers for ideal snapshot data."""
from ._validation import _int,ResourceLimit


class _ResultVisualize:
    def __init__(self,result):
        self._result=result

    def histogram(self,*,k=8):
        """SVG of top k basis probabilities, not renormalized."""
        k=_int(k,1)
        if k>32:
            raise ResourceLimit("histogram supports at most 32 bars")
        data=self._result.math.top_probabilities(k=k)
        height=78+36*len(data)
        omitted=max(0.,1-sum(data.values()))
        rows=[f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="{height}" viewBox="0 0 720 {height}" role="img" aria-label="Ideal basis probabilities">',
              '<rect width="100%" height="100%" fill="white"/>',
              '<g font-family="monospace" font-size="13" fill="#172554">',
              '<text x="12" y="23" font-size="16">Ideal Z-basis probabilities</text>']
        for i,(label,p) in enumerate(data.items()):
            y=34+36*i
            rows.append(f'<text x="12" y="{y+16}">{label}</text>')
            rows.append(f'<rect x="215" y="{y}" width="{390*p:.4f}" height="23" fill="#2563eb"/>')
            rows.append(f'<text x="612" y="{y+16}">{p:.6f}</text>')
        rows.append(f'<text x="12" y="{height-14}">Omitted probability mass: {omitted:.6g}</text></g></svg>')
        return "".join(rows)

    def bloch(self,wire=0):
        """Bloch vector coordinates for a one-qubit reduced state."""
        wire=_int(wire)
        if wire>=self._result.num_qubits:
            raise ValueError("invalid Bloch wire")
        label=lambda axis:"I"*(self._result.num_qubits-1-wire)+axis+"I"*wire
        return {axis.lower():self._result.math.expectation(label(axis)) for axis in "XYZ"}


    def bloch_svg(self,wire=0):
        """Orthographic Bloch sphere schematic; coordinates are also labeled."""
        v=self.bloch(wire)
        # Oblique projection of x/y/z onto a two-dimensional schematic.
        def project(x,y,z):
            return (160+90*x+45*y,145+28*x-48*y-90*z)
        px,py=project(v["x"],v["y"],v["z"])
        rows=['<svg xmlns="http://www.w3.org/2000/svg" width="320" height="320" viewBox="0 0 320 320" role="img" aria-label="Bloch vector schematic">',
              '<rect width="320" height="320" fill="white"/><circle cx="160" cy="145" r="100" fill="#eff6ff" stroke="#94a3b8"/>',
              '<ellipse cx="160" cy="145" rx="100" ry="31" fill="none" stroke="#94a3b8"/>',
              '<g font-family="monospace" font-size="12" fill="#172554">']
        for label,xyz in (("X",(1,0,0)),("Y",(0,1,0)),("Z",(0,0,1))):
            x,y=project(*xyz)
            rows.append(f'<line x1="160" y1="145" x2="{x}" y2="{y}" stroke="#64748b"/><text x="{x+4}" y="{y-4}">{label}</text>')
        rows.append(f'<line x1="160" y1="145" x2="{px:.3f}" y2="{py:.3f}" stroke="#dc2626" stroke-width="3"/><circle cx="{px:.3f}" cy="{py:.3f}" r="4" fill="#dc2626"/>')
        for i,axis in enumerate("xyz"):
            rows.append(f'<text x="16" y="{270+i*16}">{axis} = {v[axis]:.6g}</text>')
        rows.append("</g></svg>")
        return "".join(rows)


def circuit_svg(circuit,*,max_qubits=12,max_gates=64):
    """Bounded schematic of ordered logical operations, not physical routing."""
    from html import escape
    max_qubits,max_gates=_int(max_qubits,1),_int(max_gates)
    if max_qubits>12 or max_gates>64:
        raise ResourceLimit("SVG hard cap is 12 wires and 64 gates")
    circuit._require_bound()
    native=circuit._qc
    n,count=native.num_qubits,len(native.data)
    if n>max_qubits or count>max_gates:
        raise ResourceLimit("circuit exceeds SVG size limit")
    width=100+max(1,count)*100
    height=66+42*n
    rows=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Ordered logical quantum circuit">',
          '<rect width="100%" height="100%" fill="white"/>',
          '<g font-family="monospace" font-size="12" fill="#172554">',
          f'<text x="12" y="20">Logical circuit | phase={float(native.global_phase):.5g} rad</text>']
    y=lambda w:45+42*w
    for wire in range(n):
        rows.append(f'<text x="8" y="{y(wire)+4}">q{wire}</text><line x1="38" y1="{y(wire)}" x2="{width-12}" y2="{y(wire)}" stroke="#94a3b8"/>')
    for i,item in enumerate(native.data):
        x=80+100*i
        op=item.operation
        wires=[native.find_bit(w).index for w in item.qubits]
        label=escape(op.name.upper())
        params=",".join(f"{float(p):.3g}" for p in op.params)
        if len(wires)>1:
            rows.append(f'<line x1="{x}" y1="{y(min(wires))}" x2="{x}" y2="{y(max(wires))}" stroke="#2563eb" stroke-width="2"/>')
        for j,wire in enumerate(wires):
            suffix=f":{j}" if len(wires)>1 else ""
            rows.append(f'<rect x="{x-32}" y="{y(wire)-12}" width="64" height="24" rx="3" fill="#dbeafe" stroke="#2563eb"/><text x="{x}" y="{y(wire)+4}" text-anchor="middle">{label}{suffix}</text>')
        if params:
            rows.append(f'<text x="{x}" y="{height-9}" text-anchor="middle" font-size="10">{escape(params)}</text>')
    rows.append("</g></svg>")
    return "".join(rows)
