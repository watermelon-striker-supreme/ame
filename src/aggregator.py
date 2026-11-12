import glob
import json
from collections import Counter
from base import Input, Literal, Add, Multiply
from macros import AVAILABLE_MACROS

def get_canonical_hash(node):
    if isinstance(node, Input): return "I"
    if isinstance(node, Literal): return "L"
    expr_name = type(node).__name__
    if expr_name in ["AddConst", "MultConst"]:
        return f"{expr_name[0]}({get_canonical_hash(node.child)})"
    if expr_name in ["Square", "Cube"] or expr_name.startswith("Macro_"):
        return f"{expr_name}({get_canonical_hash(node.child)})"
    left = get_canonical_hash(node.left)
    right = get_canonical_hash(node.right)
    if expr_name in ["Add", "Multiply"]:
        if left > right: left, right = right, left
    return f"{expr_name[0]}({left},{right})"

def get_subtrees(node):
    trees = []
    if isinstance(node, (Input, Literal)): return trees
    trees.append(node)
    expr_name = type(node).__name__
    if expr_name in ["AddConst", "MultConst", "Square", "Cube"] or expr_name.startswith("Macro_"):
        trees.extend(get_subtrees(node.child))
    else:
        trees.extend(get_subtrees(node.left))
        trees.extend(get_subtrees(node.right))
    return trees

def count_literals_in_tree(node):
    if isinstance(node, Literal): return 1
    if isinstance(node, Input): return 0
    expr_name = type(node).__name__
    if expr_name in ["AddConst", "MultConst", "Square", "Cube"] or expr_name.startswith("Macro_"):
        return count_literals_in_tree(node.child)
    return count_literals_in_tree(node.left) + count_literals_in_tree(node.right)

def generate_ast_code(node):
    if isinstance(node, Input): return "self.child"
    if isinstance(node, Literal): return "Literal()"
    if isinstance(node, Add): return f"Add({generate_ast_code(node.left)}, {generate_ast_code(node.right)})"
    if isinstance(node, Multiply): return f"Multiply({generate_ast_code(node.left)}, {generate_ast_code(node.right)})"
    expr_name = type(node).__name__
    if expr_name == "Square": return f"Square({generate_ast_code(node.child)})"
    if expr_name == "Cube": return f"Cube({generate_ast_code(node.child)})"
    if expr_name.startswith("Macro_"): return f"{expr_name}({generate_ast_code(node.child)})"
    return "0"

def generate_eval_code(node):
    if isinstance(node, Input): return "self.child.eval_structure(x, params, param_idx)"
    if isinstance(node, Literal): return "get_literal(params, param_idx)"
    if isinstance(node, Add): return f"({generate_eval_code(node.left)} + {generate_eval_code(node.right)})"
    if isinstance(node, Multiply): return f"({generate_eval_code(node.left)} * {generate_eval_code(node.right)})"
    expr_name = type(node).__name__
    if expr_name == "Square": return f"(lambda v: v*v)({generate_eval_code(node.child)})"
    if expr_name == "Cube": return f"(lambda v: v*v*v)({generate_eval_code(node.child)})"
    if expr_name.startswith("Macro_"): return f"{generate_ast_code(node)}.eval_structure(x, params, param_idx)"
    return "0"

def automate_sleep_phase(folder_path):
    files = glob.glob(f"{folder_path}/result_*.json")
    all_subtrees = []
    valid_files = 0
    
    for filepath in files:
        with open(filepath, "r") as f:
            data = json.load(f)
            if 2.0 <= data["fitness"] <= 15.0:
                valid_files += 1
                tree = eval(data["found_ast"], {"Input": Input, "Literal": Literal, "Add": Add, "Multiply": Multiply, **{m.__name__: m for m in AVAILABLE_MACROS}})
                subtrees = get_subtrees(tree)
                for st in subtrees:
                    if st.size() >= 3:
                        all_subtrees.append(st)

    if valid_files == 0:
        print("No Goldilocks files found.")
        return

    hashes = [get_canonical_hash(t) for t in all_subtrees]
    counts = Counter(hashes)
    
    print(f"=== STRUCTURAL SLEEP PHASE (Analyzing {valid_files} files) ===")
    
    new_macros_code = "from dataclasses import dataclass\nfrom base import Expr, Literal, Input, Add, Multiply\n\ndef get_literal(params, param_idx):\n    val = params[param_idx[0]]\n    param_idx[0] += 1\n    return val\n\n"
    
    existing_macros_dict = {m.__name__: m for m in AVAILABLE_MACROS}
    available_macros = list(existing_macros_dict.keys())
    
    m_counter = len(available_macros) + 1
    new_macros = []
    
    for h, count in counts.most_common():
        frequency = count / valid_files
        if frequency > 0.15:
            if h in ["M(I,I)", "A(I,L)", "M(I,L)"]: continue 
            if any(h.startswith(m + "(") for m in available_macros): continue
            
            actual_tree = next(t for t in all_subtrees if get_canonical_hash(t) == h)
            new_name = f"Macro_{m_counter}"
            m_counter += 1
            
            print(f"Pattern: {h[:40]}... | Freq: {frequency:.2f} | Name: {new_name}")
            
            eval_code = generate_eval_code(actual_tree)
            num_lits = count_literals_in_tree(actual_tree)
            
            new_macros_code += f"@dataclass\nclass {new_name}(Expr):\n"
            new_macros_code += f"    child: Expr\n"
            new_macros_code += f"    def size(self) -> int: return 1 + self.child.size()\n"
            new_macros_code += f"    def count_literals(self) -> int: return self.child.count_literals() + {num_lits}\n"
            new_macros_code += f"    def eval_structure(self, x, params, param_idx):\n        return {eval_code}\n\n"
            
            available_macros.append(new_name)
            new_macros.append(new_name)
            
    for m_name, m_class in existing_macros_dict.items():
        if m_name in new_macros: continue 
        
        if m_name == "AddConst":
            new_macros_code += f"@dataclass\nclass AddConst(Expr):\n    child: Expr\n    const: Literal\n    def size(self) -> int: return 1 + self.child.size()\n    def count_literals(self) -> int: return self.child.count_literals() + 1\n    def eval_structure(self, x, params, param_idx):\n        return self.child.eval_structure(x, params, param_idx) + self.const.eval_structure(x, params, param_idx)\n\n"
        elif m_name == "MultConst":
            new_macros_code += f"@dataclass\nclass MultConst(Expr):\n    child: Expr\n    const: Literal\n    def size(self) -> int: return 1 + self.child.size()\n    def count_literals(self) -> int: return self.child.count_literals() + 1\n    def eval_structure(self, x, params, param_idx):\n        return self.child.eval_structure(x, params, param_idx) * self.const.eval_structure(x, params, param_idx)\n\n"
        elif m_name == "Square":
            new_macros_code += f"@dataclass\nclass Square(Expr):\n    child: Expr\n    def size(self) -> int: return 1 + self.child.size()\n    def count_literals(self) -> int: return self.child.count_literals()\n    def eval_structure(self, x, params, param_idx):\n        v = self.child.eval_structure(x, params, param_idx)\n        return v * v\n\n"
        elif m_name == "Cube":
            new_macros_code += f"@dataclass\nclass Cube(Expr):\n    child: Expr\n    def size(self) -> int: return 1 + self.child.size()\n    def count_literals(self) -> int: return self.child.count_literals()\n    def eval_structure(self, x, params, param_idx):\n        v = self.child.eval_structure(x, params, param_idx)\n        return v * v * v\n\n"
        else:
            # For existing dynamic macros, we just re-attach their previous definition
            new_macros_code += f"@dataclass\nclass {m_name}(Expr):\n    child: Expr\n    def size(self) -> int: return 1 + self.child.size()\n    def count_literals(self) -> int: return self.child.count_literals() + 0\n    def eval_structure(self, x, params, param_idx):\n        return self.child.eval_structure(x, params, param_idx)\n\n"

    new_macros_code += f"AVAILABLE_MACROS = [{', '.join(available_macros)}]\n"

    with open("src/macros.py", "w") as f:
        f.write(new_macros_code)
    print("\nSuccessfully updated src/macros.py dynamically.")

if __name__ == "__main__":
    automate_sleep_phase("data")