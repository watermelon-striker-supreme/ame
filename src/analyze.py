import glob
import json
import numpy as np

if __name__ == "__main__":
    files = glob.glob("data/result_*.json")
    if not files:
        print("No files found in data/.")
        exit()

    fitness = [json.load(open(f))["fitness"] for f in files]
    found_sizes = [json.load(open(f))["found_size"] for f in files]
    
    macro_usage = sum(1 for f in files if any(m in json.load(open(f))["found_ast"] for m in ["Macro_", "Square", "AddConst", "MultConst"]))
    
    print(f"=== ANALYSIS OF {len(files)} JOBS ===")
    print(f"Average Fitness: {np.mean(fitness):.2f}")
    print(f"Average Found Size: {np.mean(found_sizes):.2f}")
    print(f"Macro Usage: {macro_usage} out of {len(files)}")