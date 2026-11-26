import numpy as np
import pytest
from research.alpha_buffer_normalization import finite_full,finite_chunked,finite_reuse,norm_and_valid,byte_full,byte_ascii,run

@pytest.mark.parametrize("kind",["normal","nonfinite","nonunit","strided","readonly"])
def test_finite_scan_and_norm_contract(kind):
    a=np.zeros(32768,dtype=np.complex128);a[0]=1
    if kind=="nonfinite":a[-1]=complex(0,float("nan"))
    if kind=="nonunit":a[0]=.9
    if kind=="strided":a=a[::2]
    if kind=="readonly":a.flags.writeable=False
    ref=norm_and_valid(a,finite_full)
    for checker in (finite_chunked,finite_reuse):
        got=norm_and_valid(a,checker)
        assert got[1]==ref[1]
        assert got[0]==ref[0] or (np.isnan(got[0]) and np.isnan(ref[0]))
    assert finite_chunked(a)==finite_reuse(a)==finite_full(a)

@pytest.mark.parametrize("text",["","ascii","é","🧪","x\ud800"])
def test_utf8_strict(text):
    try:expected=byte_full(text)
    except UnicodeError:
        with pytest.raises(UnicodeError):byte_ascii(text)
    else:assert byte_ascii(text)==expected

def test_profile_smoke():
    assert len(run(1101,1,quick=True))==4
