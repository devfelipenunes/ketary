import pytest
from research.copy_replay_inventory import worker

@pytest.mark.parametrize("kind",["copy","native_export","encode","decode","bind","run","snapshot_export"])
def test_copy_inventory_semantics(kind):
    row=worker(4,4,kind,3)
    assert row["verified"]
    assert len(row["raw_ms"])==3
    assert sum(v is not None for v in row["retained"].values())==1
