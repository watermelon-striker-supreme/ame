import glob
import json
import numpy as np

def analyze_folder(folder_path, label):
    files = glob.glob(f"{folder_path}/result_*.json")
    if not files: return
    
    times = []
    ast_lengths = []
    macro_usage = 0
    
    for filepath in files:
        with open(filepath, "r") as f:
            data = json.load(f)
            times.append(data["time"])
            ast_str = data["ast"]
            ast_lengths.append(len(ast_str))
            if "AddConst" in ast_str or "MultConst" in ast_str:
                macro_usage += 1
                
    print(f"=== {label} ({len(files)} JOBS) ===")
    print(f"Average Solve Time: {np.mean(times):.2f} seconds")
    print(f"Fastest Solve Time: {min(times):.2f} seconds")
    print(f"Average AST Length: {np.mean(ast_lengths):.1f} characters")
    print(f"Macro Usage: {macro_usage} out of {len(files)} ({(macro_usage/len(files))*100:.1f}%)\n")

if __name__ == "__main__":
    analyze_folder("data_phase1", "PHASE 1 (NO MACROS)")
    analyze_folder("data_phase2", "PHASE 2 (WITH MACROS)")