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
