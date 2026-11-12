import glob
import json
import numpy as np

if __name__ == "__main__":
    files = glob.glob("data/result_*.json")
    
    if not files:
        print("No files found in data/. Either the jobs are still running, or every problem was rejected by the Goldilocks filter.")
        exit()

    times = [json.load(open(f))["time"] for f in files]
    targets = [json.load(open(f))["target_ast"] for f in files]
    
    print(f"=== GOLDILOCKS ANALYSIS ===")
    print(f"Jobs that passed the filter: {len(files)} out of 100")
    print(f"Average time of accepted jobs: {np.mean(times):.3f} seconds")
    print(f"Fastest accepted: {min(times):.3f} seconds")
    print(f"Slowest accepted: {max(times):.3f} seconds")
    
    print("\n=== SAMPLE ACCEPTED TARGETS ===")
    for t in targets[:5]:
        print(t)