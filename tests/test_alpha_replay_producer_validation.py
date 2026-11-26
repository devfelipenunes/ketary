"""Adversarial producer metadata and replay/evidence boundaries (#93)."""
import hashlib
import json
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Operator


def canonical(data):
    return json.dumps(data,sort_keys=True,separators=(",",":"),allow_nan=False)


def rehash(envelope):
    envelope["sha256"]=hashlib.sha256(canonical(envelope["data"]).encode()).hexdigest()
    return envelope


@pytest.mark.parametrize("invalid",["", "a"*101, "\ud800", "\udfff", 1, True, []])
def test_invalid_producer_before_native_circuit(invalid,monkeypatch):
    payload=json.loads(q.bell().to_json())
    envelope=q.Circuit(1).x(0).test.compare(q.Circuit(1),inputs=["0"]).evidence.to_dict()
    payload["producer"]["python"]=invalid
    envelope["data"]["producer"]["python"]=invalid
    rehash(envelope)
    from ketary import _replay
    monkeypatch.setattr(_replay,"_sdk",lambda:pytest.fail("native allocation before metadata validation"))
    with pytest.raises(ValueError):
        q.Circuit.from_json(canonical(payload))
    with pytest.raises(ValueError):
        q.Evidence.from_json(canonical(envelope))
    with pytest.raises(ValueError):
        q.Evidence.from_dict(envelope)


@pytest.mark.parametrize("text",["é","版本","🚀","a"*100])
def test_unicode_scalar_metadata_preserves_semantics(text):
    source=q.Circuit(2).h(1).cx(1,0)
    data=json.loads(source.to_json())
    data["producer"]["python"]=text
    restored=q.Circuit.from_json(canonical(data))
    np.testing.assert_allclose(Operator(restored.to_qiskit()).data,
                               Operator(source.to_qiskit()).data,atol=1e-12,rtol=0)
    artifact=q.Circuit(1).x(0).test.compare(q.Circuit(1),inputs=["0"]).evidence.to_dict()
    artifact["data"]["producer"]["python"]=text
    rehash(artifact)
    assert q.Evidence.from_json(canonical(artifact)).to_dict()==artifact
    assert q.Evidence.from_dict(artifact).reproduce()["reproduced"]


@pytest.mark.parametrize("number",["1e309","-1e309","9"*400])
def test_numeric_overflow_preflight(number,monkeypatch):
    raw=q.Circuit(1).ry(.5,0).to_json().replace('"params":[0.5]',f'"params":[{number}]')
    assert number in raw
    from ketary import _replay
    monkeypatch.setattr(_replay,"_sdk",lambda:pytest.fail("native allocation before numeric validation"))
    with pytest.raises(ValueError):
        q.Circuit.from_json(raw)
