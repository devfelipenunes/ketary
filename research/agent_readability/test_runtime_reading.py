import ketary as q
from source_reader import read_source

def test_runtime_reading_of_functions_and_loops():
    # Trusted fixture: runtime objects capture realized operations, while the
    # literal reader correctly abstains on dynamic source.
    def ladder(n):
        c=q.Circuit(n).h(0)
        for i in range(n-1):
            c.cx(i,i+1)
        return c
    c=ladder(4)
    report=c.inspect()
    assert [x["wires"] for x in report["operations"]]==[[0],[0,1],[1,2],[2,3]]
    assert c.run().verify(probabilities={"0000":.5,"1111":.5})["status"]=="PASS"
    assert read_source("import ketary as q\nc=q.Circuit(4)\nfor i in range(3): c.cx(i,i+1)")["status"]=="UNSUPPORTED"
