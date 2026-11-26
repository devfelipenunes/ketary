import pytest
from research.language_corpus import CASES,evaluate

@pytest.mark.parametrize("case",CASES,ids=[row[0] for row in CASES])
@pytest.mark.parametrize("index",range(10))
def test_language_corpus(case,index):
    result=evaluate(case,index,reps=1)
    assert all(v["max_error"]<1e-9 for v in result["variants"].values())
