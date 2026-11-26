"""Build a weighted symbolic QAOA layer and evaluate independent rows."""
import ketary as q

def build():
    n=4
    edges=q.ring(range(n))
    weights=(.5,1.2,.7,.9)
    gamma,beta=q.Circuit.parameter_vector("t",2)
    cost=q.maxcut_hamiltonian(n,edges,weights=weights)
    mixer=sum(q.X(i) for i in range(n))
    circuit=(q.Circuit.symbolic(n).h(range(n))
             .evolve(cost,time=gamma).evolve(mixer,time=beta))
    return circuit,cost

def evaluate(rows):
    circuit,cost=build()
    results=circuit.sweep_rows(rows).run()
    for result in results:result.test.normalized().require()
    return tuple(result.math.expectation(cost) for result in results)

if __name__=="__main__":
    for energy in evaluate([[.5,.3],[.7,.4],[.9,.2]]):print(energy)
