import random
import time

from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import *
from qiskit.visualization import plot_histogram
from qiskit_aer import AerSimulator, Aer

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
    start_time = time.time()
    num = 2 ** len
    res = 0

    for i in range(num):
        word = [(i >> bit) & 1 for bit in range(len)]

        if constant or xor_fun(len, doors, word):
            res += 1
        else:
            res -= 1

    return res == 0, (time.time() - start_time)


def init_circuit(len, doors, constant):
    circuit = QuantumCircuit(len + 1)
    func = QuantumCircuit(len + 1, 0)

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

        circuit = circuit.compose(func)

    circuit.barrier()

    for i in range(len):
        circuit.append(hadamard_gate, [i])

    circuit.measure_all()

    #circuit.draw("mpl")

    return circuit

local = False

n, c, d = get_parameters()

print(f"Number of qubits: {n}")

qc = init_circuit(n, c, d)

service = QiskitRuntimeService(channel="ibm_quantum")

if local:
    sim = Aer.get_backend('aer_simulator')
    qc_transpiled = transpile(qc, sim)

    result = AerSimulator().run(qc_transpiled, shots=1000).result()
    counts = result.get_counts()
    print(counts)
else:
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=n+1)
    print(backend.name)

    qc_transpiled = transpile(qc, backend, optimization_level=2)
    #qc_transpiled.draw("mpl")

    sampler = Sampler(mode=backend)
    qc_job = sampler.run([qc_transpiled], shots=1000)

    print(qc_job.job_id)
    print(qc_job.usage_estimation)

    result = qc_job.result()
    print(result)

    plot_histogram(result[0].data.meas.get_counts())

balanced, time_elapsed = is_balanced(n, c, d)
print(f"Balanced (classic): {balanced}. Took {time_elapsed} seconds.")
print(f"Real Constant Value (balanced otherwise): {c}")