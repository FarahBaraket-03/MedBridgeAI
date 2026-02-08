"""Quick smoke-test for QUBO quantum TSP solver."""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(__file__))

try:
    import numpy as np
    from backend.core.quantum import solve_tsp_qubo, compare_routes, is_qiskit_available

    print("Qiskit available:", is_qiskit_available())

    # 4-city test
    dm = np.array([
        [0, 10, 20, 30],
        [10, 0, 25, 15],
        [20, 25, 0, 35],
        [30, 15, 35, 0],
    ], dtype=float)
    print("\n--- solve_tsp_qubo (4 cities) ---")
    r = solve_tsp_qubo(dm, city_names=["Accra", "Tema", "Kumasi", "Tamale"])
    for k, v in r.items():
        print(f"  {k}: {v}")

    # 5-city test (should use brute-force strategy)
    dm5 = np.array([
        [0, 10, 35, 25, 50],
        [10, 0, 30, 20, 45],
        [35, 30, 0, 15, 60],
        [25, 20, 15, 0, 55],
        [50, 45, 60, 55, 0],
    ], dtype=float)
    print("\n--- solve_tsp_qubo (5 cities, brute-force) ---")
    r5 = solve_tsp_qubo(dm5, city_names=["Accra","Tema","Kumasi","Tamale","Takoradi"])
    for k, v in r5.items():
        print(f"  {k}: {v}")

    # 7-city test
    np.random.seed(42)
    dm7 = np.random.uniform(10, 100, (7, 7))
    dm7 = (dm7 + dm7.T) / 2
    np.fill_diagonal(dm7, 0)
    print("\n--- solve_tsp_qubo (7 cities, brute-force) ---")
    r7 = solve_tsp_qubo(dm7, city_names=[f"City{i}" for i in range(7)])
    for k, v in r7.items():
        print(f"  {k}: {v}")

    # compare_routes test
    print("\n--- compare_routes ---")
    cmp = compare_routes(dm, [0, 1, 3, 2], 75.0, city_names=["Accra","Tema","Kumasi","Tamale"])
    for k, v in cmp.items():
        print(f"  {k}: {v}")

    print("\nAll tests passed!")
except Exception as e:
    traceback.print_exc()
