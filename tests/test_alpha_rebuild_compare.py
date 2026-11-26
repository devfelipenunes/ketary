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
