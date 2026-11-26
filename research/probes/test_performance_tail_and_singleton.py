from research.performance_tail_and_singleton import singleton

def test_single_item_grouped_full_path():
    row=singleton(4,3,1101)
    assert all(len(v["raw_ms"])==3 for v in row["variants"].values())
