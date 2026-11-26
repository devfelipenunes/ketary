import ketary as q

def test_verified_teleportation_decode():
    shots=q.teleportation(.4,.8,verify=True).run_shots(shots=32,seed=42)
    assert q.decode_teleportation(shots)["counts"]=={"0":32,"1":0}
