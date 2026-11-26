import io
import tarfile
import zipfile
import pytest
from research.alpha_study_schedule import assignments
from research.alpha_distribution_audit import audit,safe_name

def test_formative_schedule_has_independent_order_balance():
    rows=assignments(4)
    assert {(r["first_route"],r["first_variant"]) for r in rows}=={("Ketary","A"),("Ketary","B"),("Qiskit","A"),("Qiskit","B")}
    for count in (3,4,5):
        for r in assignments(count):
            assert r["first_route"]!=r["second_route"]
            assert r["first_variant"]!=r["second_variant"]
            assert set(r["task_order"])==set("VDH")
    for invalid in (0,2,6,True):
        with pytest.raises(ValueError):assignments(invalid)

def test_archive_path_admission():
    assert safe_name("ketary/py.typed")
    for path in ("../bad","/absolute","root/../../bad","a\\b"):
        assert not safe_name(path)

def test_distribution_checker_fixture(tmp_path):
    wheel=tmp_path/"ketary.whl";sdist=tmp_path/"ketary.tar.gz"
    with zipfile.ZipFile(wheel,"w") as z:
        for path in ("ketary/py.typed","ketary/__init__.pyi","ketary-0.1.0.dev0.dist-info/licenses/LICENSE","ketary-0.1.0.dev0.dist-info/RECORD"):
            z.writestr(path,"")
        z.writestr("ketary-0.1.0.dev0.dist-info/METADATA","Name: ketary\nVersion: 0.1.0.dev0\nRequires-Python: <3.13,>=3.12\n")
    with tarfile.open(sdist,"w:gz") as t:
        for name in ("ketary-0.1.0.dev0/LICENSE","ketary-0.1.0.dev0/pyproject.toml"):
            data=b"fixture";member=tarfile.TarInfo(name);member.size=len(data);t.addfile(member,io.BytesIO(data))
    r=audit(wheel,sdist)
    assert len(r["wheel"]["sha256"])==64 and r["sdist"]["members"]==2
    with zipfile.ZipFile(wheel,"a") as z:z.writestr("../bad","")
    with pytest.raises(AssertionError):audit(wheel,sdist)
