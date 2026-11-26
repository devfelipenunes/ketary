import zipfile
from research.alpha_rebuild_compare import inventory,compare

def wheel(path,stamp,content):
    with zipfile.ZipFile(path,"w") as z:
        entry=zipfile.ZipInfo("ketary/__init__.py",date_time=stamp)
        z.writestr(entry,content)

def test_rebuild_distinguishes_content_and_bytes(tmp_path):
    a=tmp_path/"a.whl";b=tmp_path/"b.whl"
    wheel(a,(2026,1,1,0,0,0),"source")
    wheel(b,(2026,1,2,0,0,0),"source")
    row=compare(inventory(a),inventory(b))
    assert row["content_equal"] and not row["byte_equal"]
    assert row["changed_metadata"]==["ketary/__init__.py"]
    assert row["changed_content"]==[]
    wheel(b,(2026,1,2,0,0,0),"different")
    row=compare(inventory(a),inventory(b))
    assert not row["content_equal"] and row["changed_content"]==["ketary/__init__.py"]
    assert compare(inventory(a),inventory(a))["byte_equal"]


def test_deterministic_tar_preserves_content_and_ignores_mtime(tmp_path,monkeypatch):
    import os
    from research.alpha_rebuild_compare import deterministic_tar
    monkeypatch.chdir(tmp_path)
    root=tmp_path/"release"
    root.mkdir()
    (root/"file.txt").write_text("source")
    a=deterministic_tar(tmp_path/"a","release",1795731117)
    os.utime(root/"file.txt",(12345,12345))
    os.utime(root,(23456,23456))
    b=deterministic_tar(tmp_path/"b","release",1795731117)
    row=compare(inventory(a),inventory(b))
    assert row["byte_equal"] and row["content_equal"] and not row["changed_metadata"]
    assert inventory(a)["members"]=={"release":None,"release/file.txt":__import__("hashlib").sha256(b"source").hexdigest()}

def test_deterministic_tar_rejects_symlink(tmp_path,monkeypatch):
    import pytest
    from research.alpha_rebuild_compare import deterministic_tar
    monkeypatch.chdir(tmp_path)
    root=tmp_path/"release"
    root.mkdir()
    (root/"link").symlink_to(tmp_path)
    with pytest.raises(ValueError,match="non-regular"):
        deterministic_tar(tmp_path/"bad","release",1795731117)
