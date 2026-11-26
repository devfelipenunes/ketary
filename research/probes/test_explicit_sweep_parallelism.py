import numpy as np
from research.explicit_sweep_parallelism import workload,thread_task,process_task,evaluate

def test_isolated_serial_and_replay_task_oracles():
    cs,payloads,reference=workload(6,4)
    for c,payload,wanted in zip(cs,payloads,reference,strict=True):
        np.testing.assert_allclose(thread_task(c),wanted,atol=1e-9,rtol=0)
        np.testing.assert_allclose(process_task(payload),wanted,atol=1e-9,rtol=0)
        assert c.to_json()==payload
