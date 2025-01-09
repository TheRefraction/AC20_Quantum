import random
import time

from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import *
from qiskit.visualization import plot_histogram
from qiskit_aer import AerSimulator, Aer

def get_parameters(length):
    constant = random.randint(0, 1)
    if constant:
        doors = [0 for _ in range(length)]
    else:
        doors = [random.randint(0, 1) for _ in range(length)]
        doors[random.randint(0, length - 1)] = 1 # At least one door!!!

    return doors, constant

def xor_fun(length, doors, inputs):
    res = 0

    for j in range(length):
        if doors[j]:
            res = res ^ inputs[j]

    return res

def is_constant(length, doors):
    start_time = time.time()
    num = 2 ** (length - 1) + 1 # Check that
    res = 0

    for j in range(num):
        word = [(j >> bit) & 1 for bit in range(length)]

        if xor_fun(length, doors, word):
            res += 1
        else:
            res -= 1

    return (res == num or res == -num), (time.time() - start_time)


def init_circuit(register_size, doors, constant):
    # Define a quantum circuit with n + 1 qubits and bits
    circuit = QuantumCircuit(register_size + 1, register_size)

    # Define some alias
    hadamard_gate = HGate()
    xpauli_gate = XGate()
    cnot_gate = CXGate()

    # Applying X on the ancilla
    circuit.append(xpauli_gate, [register_size])

    # Applying H on all registers
    for j in range(register_size + 1):
        circuit.append(hadamard_gate, [j])

    circuit.barrier()

    # Oracle
    if not constant:
        for j in range(register_size):
            if doors[j]:
                circuit.append(cnot_gate, [j, register_size])


    circuit.barrier()

    # Applying H on all registers except the ancilla
    for j in range(register_size):
        circuit.append(hadamard_gate, [j])

    # Measure all except the ancilla
    circuit.measure(range(register_size), range(register_size))

    #circuit.draw("mpl")

    return circuit

def main():
    random.seed()

    local = False
    if local:
        print("[INFO] : Running in simulation mode")

    service = QiskitRuntimeService(channel="ibm_quantum")
    print("[INFO] : Running on IBM Quantum service")

    shots = 1000
    print(f"[INFO] : Running experiments with {shots} shots")

    optimization = 2
    print(f"[INFO] : Circuit transpilation will be run with a {optimization}-level optimization")

    for n in range(4, 64, 2):
        print(f"Now running with {n} qubits (1st register)")
        doors, constant = get_parameters(n)

        print("Initializing quantum circuit")
        qc = init_circuit(n, doors, constant)

        if local:
            backend = Aer.get_backend('aer_simulator')
        else:
            backend = service.least_busy(operational=True, simulator=False, min_num_qubits=n+1)

        print(f"Backend : {backend.name}")

        print("Transpiling quantum circuit")
        isa_qc = transpile(qc, backend, optimization_level=optimization)

        if local:
            result = AerSimulator().run(isa_qc, shots=shots).result()

            print(f"Result : {result.get_counts()}")
        else:
            sampler = Sampler(mode=backend)

            qc_job = sampler.run([isa_qc], shots=shots)
            print(f"Running job : {qc_job.job_id}")
            print(f"Time estimation : {qc_job.usage_estimation}")

            result = qc_job.result()

            print(f"Result : {result[0].data.c.get_counts()}")

            #plot_histogram(result[0].data.c.get_counts())


        print(f"Real Constant Value : {constant}")
        constant_res, time_elapsed = is_constant(n, doors)
        print(f"Constant (classic) : {constant_res}. Took {time_elapsed} seconds.")
        print("----------------------------------------------------------")

def test():
    service = QiskitRuntimeService(channel="ibm_quantum")
    job = service.job('cxzwavk9b62g008h3nn0')
    job_result = job.result()

    print(f"{job_result[0].data.c.get_counts()}")
    plot_histogram(job_result[0].data.c.get_counts())

main()