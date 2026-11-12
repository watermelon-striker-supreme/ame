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
    # NEW: Look for cubes (x^3)
    if "Multiply(left=Square(child=Input()), right=Input())" in ast_string or "Multiply(left=Input(), right=Square(child=Input()))" in ast_string:
        patterns.append("Cube_Input")
    if "Multiply(left=Square(child=Input()), right=MultConst" in ast_string or "Multiply(left=MultConst" in ast_string and "right=Square(child=Input())" in ast_string:
        patterns.append("Cube_Input")
        
    return patterns

def automate_sleep_phase(folder_path):
    files = glob.glob(f"{folder_path}/result_*.json")
    if not files:
        print("No files found.")
        return

    all_patterns = []
    valid_files = 0
    
    for filepath in files:
        with open(filepath, "r") as f:
            data = json.load(f)
            
            if 2.0 <= data["fitness"] <= 15.0:
                valid_files += 1
                all_patterns.extend(extract_patterns(data["found_ast"]))

    if valid_files == 0:
        print("No Goldilocks files found in this batch.")
        return

    counts = Counter(all_patterns)
    new_macros_code = "from dataclasses import dataclass\nfrom base import Expr, Literal\n\n"
    available_macros = ["MultConst", "AddConst", "Square"] # Keep the ones we already have

    print(f"=== SLEEP PHASE (Analyzing {valid_files} Goldilocks solutions) ===")
    for pattern, count in counts.items():
        frequency = count / valid_files
        utility = frequency 
        
        print(f"Pattern: {pattern} | Freq: {frequency:.2f} | Utility: {utility:.2f}")
        
        if utility > 0.15:
            if pattern == "Cube_Input" and "Cube" not in available_macros:
                new_macros_code += "@dataclass\nclass Cube(Expr):\n    child: Expr\n    def size(self) -> int: return 1 + self.child.size()\n\n"
                available_macros.append("Cube")
                print("  >> Compiled 'Cube'")

    # Rebuild the full macros.py file
    new_macros_code = "from dataclasses import dataclass\nfrom base import Expr, Literal\n\n"
    
    if "AddConst" in available_macros:
        new_macros_code += "@dataclass\nclass AddConst(Expr):\n    child: Expr\n    const: Literal\n    def size(self) -> int: return 1 + self.child.size()\n\n"
    if "MultConst" in available_macros:
        new_macros_code += "@dataclass\nclass MultConst(Expr):\n    child: Expr\n    const: Literal\n    def size(self) -> int: return 1 + self.child.size()\n\n"
    if "Square" in available_macros:
        new_macros_code += "@dataclass\nclass Square(Expr):\n    child: Expr\n    def size(self) -> int: return 1 + self.child.size()\n\n"
    if "Cube" in available_macros:
        new_macros_code += "@dataclass\nclass Cube(Expr):\n    child: Expr\n    def size(self) -> int: return 1 + self.child.size()\n\n"

    new_macros_code += f"AVAILABLE_MACROS = [{', '.join(available_macros)}]\n"

    with open("src/macros.py", "w") as f:
        f.write(new_macros_code)
    print("\nSuccessfully updated src/macros.py")

if __name__ == "__main__":
    automate_sleep_phase("data")