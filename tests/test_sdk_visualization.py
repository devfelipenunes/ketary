import xml.etree.ElementTree as ET
import pytest
import ketary as q


def test_histogram_and_bloch(monkeypatch):
    r=q.bell().run()
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("hidden execution"))
    chart=r.visualize.histogram(k=2)
    root=ET.fromstring(chart)
    assert root.tag=="{http://www.w3.org/2000/svg}svg"
    assert "00" in chart and "11" in chart
    assert "Omitted probability mass: 0" in chart
    assert r.visualize.bloch(0)==pytest.approx({"x":0,"y":0,"z":0},abs=1e-12)
    with pytest.raises(q.ResourceLimit):
        r.visualize.histogram(k=33)
    with pytest.raises(ValueError):
        r.visualize.bloch(2)


def test_bloch_pure_state():
    assert q.Circuit(1).h(0).run().visualize.bloch()==pytest.approx({"x":1,"y":0,"z":0},abs=1e-12)
