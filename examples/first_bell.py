"""Prepare and inspect an ideal Bell state using a single execution."""
import ketary as q

def main():
    circuit = q.bell()
    result = circuit.run()
    result.test.normalized().require()
    result.test.probability("00", 0.5).require()
    result.test.probability("11", 0.5).require()
    result.test.entangled(partition=([0], [1])).require()
    print(result.math.probabilities())
    return result

if __name__ == "__main__":
    main()
