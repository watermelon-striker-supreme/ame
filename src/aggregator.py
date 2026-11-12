import glob
import json
from collections import Counter

def extract_patterns(ast_string):
    patterns = []
    if "Multiply(left=Input(), right=Literal())" in ast_string or "Multiply(left=Literal(), right=Input())" in ast_string:
        patterns.append("Multiply_Input_Literal")
    if "Add(left=Input(), right=Literal())" in ast_string or "Add(left=Literal(), right=Input())" in ast_string:
        patterns.append("Add_Input_Literal")
    if "Multiply(left=Input(), right=Input())" in ast_string:
        patterns.append("Multiply_Input_Input")
    return patterns

def automate_sleep_phase(folder_path):
    files = glob.glob(f"{folder_path}/result_*.json")
    if not files:
        print(f"No files found in {folder_path}. Run the Wake phase first.")
        return

    all_patterns = []
    for filepath in files:
        with open(filepath, "r") as f:
            data = json.load(f)
            all_patterns.extend(extract_patterns(data["ast"]))

    counts = Counter(all_patterns)
    
    new_macros_code = "from dataclasses import dataclass\nfrom base import Expr, Literal\n\n"
    available_macros = []

    print("=== AUTOMATED SLEEP PHASE (UTILITY SCORING) ===")
    for pattern, count in counts.items():
        frequency = count / len(files)
        node_savings = 1.0 
        search_space_cost = 1.0
        utility = (frequency * node_savings) / search_space_cost
        
        print(f"Pattern: {pattern} | Freq: {frequency:.2f} | Utility: {utility:.2f}")
        
        if utility > 0.20:
            if pattern == "Multiply_Input_Literal":
                new_macros_code += "@dataclass\nclass MultConst(Expr):\n    child: Expr\n    const: Literal\n    def size(self) -> int: return 1 + self.child.size()\n\n"
                available_macros.append("MultConst")
                print("  >> Compiled 'MultConst' (Utility passed)")
            elif pattern == "Add_Input_Literal":
                new_macros_code += "@dataclass\nclass AddConst(Expr):\n    child: Expr\n    const: Literal\n    def size(self) -> int: return 1 + self.child.size()\n\n"
                available_macros.append("AddConst")
                print("  >> Compiled 'AddConst' (Utility passed)")
            elif pattern == "Multiply_Input_Input":
                new_macros_code += "@dataclass\nclass Square(Expr):\n    child: Expr\n    def size(self) -> int: return 1 + self.child.size()\n\n"
                available_macros.append("Square")
                print("  >> Compiled 'Square' (Utility passed)")

    new_macros_code += f"AVAILABLE_MACROS = [{', '.join(available_macros)}]\n"

    with open("src/macros.py", "w") as f:
        f.write(new_macros_code)
    print("\nSuccessfully updated src/macros.py")

if __name__ == "__main__":
    automate_sleep_phase("data")