from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import *
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import EstimatorV2 as Estimator
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime import SamplerV2 as Sampler

import random
import time

def get_parameters():
    random.seed()

    while True:
        try:
            num = int(input("Enter the number of qubits:"))
            if 0 < num <= 100:
                break
            else:
                print("Invalid number of qubits!")
        except ValueError:
            print("Invalid input!")

    constant = random.randint(0, 1)
    doors = []
    if not constant:
        doors = [random.randint(0, 1) for _ in range(num)]

    return num, doors, constant

def xor_fun(len, doors, inp):
    res = 0

    for i in range(len):
        if doors[i]:
            res = res ^ inp[i]

    return res

def is_balanced(len, doors, constant):
    if constant:
        return False, 0

    start_time = time.time()
    num = 2 ** len
    res = 0

    for i in range(num):
        word = [(i >> bit) & 1 for bit in range(len)]

        if xor_fun(len, doors, word):
            res += 1
        else:
            res -= 1

    return res == 0, (time.time() - start_time)


def init_circuit(len, doors, constant):
    circuit = QuantumCircuit(len + 1, len + 1)
    func = QuantumCircuit(len + 1, 0, name = "Uf")

    hadamard_gate = HGate()
    xpauli_gate = XGate()
    cnot_gate = CXGate()

    circuit.append(xpauli_gate, [n])

    for i in range(len + 1):
        circuit.append(hadamard_gate, [i])

    circuit.barrier()

    if not constant:
        for i in range(len):
            if doors[i]:
                func.append(cnot_gate, [i, len])

    gate = func.to_gate()
    circuit.append(gate, range(len + 1))

    circuit.barrier()

    for i in range(len):
        circuit.append(hadamard_gate, [i])

    circuit.measure(range(len), range(len))

    circuit.draw("mpl")

    return circuit

cheat = False
local = True

n, c, d = get_parameters()

print(f"Number of qubits: {n}")

if cheat:
    print(f"CNOT doors bitstring: {c}")
    print(f"Constant function: {d}")

qc = init_circuit(n, c, d)

if cheat:
    qc.decompose().draw("mpl")

service = QiskitRuntimeService()
if local:
    real_backend = service.backend("ibm_kyiv")
    backend = AerSimulator.from_backend(real_backend)
else:
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=n+1)

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
isa_qc = pm.run(qc)
isa_qc.draw("mpl", idle_wires=False)
print(f">>> Circuit ops (ISA): {isa_qc.count_ops()}")

sampler = Sampler(mode=backend)
job = sampler.run([isa_qc])

print(f">>> Job ID: {job.job_id()}")
print(f">>> Job Status: {job.status()}")

result = job.result()
print(f">>> {result}")
if not local:
    print(f"  > Expectation value: {result[0].data.evs}")
    print(f"  > Metadata: {result[0].metadata}")

balanced, time_elapsed = is_balanced(n, c, d)
print(f"Balanced (classic): {balanced}. Took {time_elapsed} seconds.")