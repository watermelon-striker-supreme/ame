import sys
sys.path.append('src') 
import json
import random
import numpy as np
from dataclasses import dataclass
from geml.simplegp import SimpleGP
from geneticengine.grammar.grammar import extract_grammar
from geneticengine.solutions.individual import Individual
from scipy.optimize import curve_fit
import warnings
import os

from base import Expr, Input, Literal, Add, Multiply
from macros import AVAILABLE_MACROS

warnings.filterwarnings("ignore")

def generate_target_tree(depth):
    if depth == 0:
        return Input()
    
    # 20% chance to stop early, but only if we are at depth 1
    if depth <= 1 or random.random() < 0.2:
        return random.choice([Add, Multiply])(generate_target_tree(0), random.choice([Input(), Literal()]))
    
    # Otherwise, keep branching
    op = random.choice([Add, Multiply])
    return op(generate_target_tree(depth - 1), generate_target_tree(depth - 1))

def get_literals(node):
    if isinstance(node, Literal): return [node]
    if isinstance(node, Input): return []
    expr_name = type(node).__name__
    if expr_name in ["AddConst", "MultConst"]:
        return get_literals(node.child) + get_literals(node.const)
    if expr_name == "Square":
        return get_literals(node.child)
    return get_literals(node.left) + get_literals(node.right)

def evaluate_target(node, x, params, param_idx):
    if isinstance(node, Input): return x
    if isinstance(node, Literal):
        val = params[param_idx[0]]
        param_idx[0] += 1
        return val
    expr_name = type(node).__name__
    if expr_name == "Add":
        return evaluate_target(node.left, x, params, param_idx) + evaluate_target(node.right, x, params, param_idx)
    if expr_name == "Multiply":
        return evaluate_target(node.left, x, params, param_idx) * evaluate_target(node.right, x, params, param_idx)
    if expr_name == "AddConst":
        return evaluate_target(node.child, x, params, param_idx) + evaluate_target(node.const, x, params, param_idx)
    if expr_name == "MultConst":
        return evaluate_target(node.child, x, params, param_idx) * evaluate_target(node.const, x, params, param_idx)
    if expr_name == "Square":
        val = evaluate_target(node.child, x, params, param_idx)
        return val * val
    raise ValueError("Unknown node")

def count_literals(expr: Expr) -> int:
    if isinstance(expr, Literal): return 1
    if isinstance(expr, Input): return 0
    expr_name = type(expr).__name__
    if expr_name in ["AddConst", "MultConst"]:
        return count_literals(expr.child) + count_literals(expr.const)
    if expr_name == "Square":
        return count_literals(expr.child)
    return count_literals(expr.left) + count_literals(expr.right)

def evaluate_tree(expr: Expr, x: float, params: list, param_idx: list) -> float:
    if isinstance(expr, Input): return x
    elif isinstance(expr, Literal):
        val = params[param_idx[0]]
        param_idx[0] += 1
        return val
    elif isinstance(expr, Add): return evaluate_tree(expr.left, x, params, param_idx) + evaluate_tree(expr.right, x, params, param_idx)
    elif isinstance(expr, Multiply): return evaluate_tree(expr.left, x, params, param_idx) * evaluate_tree(expr.right, x, params, param_idx)
    
    expr_name = type(expr).__name__
    if expr_name == "AddConst":
        return evaluate_tree(expr.child, x, params, param_idx) + evaluate_tree(expr.const, x, params, param_idx)
    elif expr_name == "MultConst":
        return evaluate_tree(expr.child, x, params, param_idx) * evaluate_tree(expr.const, x, params, param_idx)
    elif expr_name == "Square":
        val = evaluate_tree(expr.child, x, params, param_idx)
        return val * val
    raise ValueError(f"Unknown expression type: {expr_name}")

def fitness_function(expr: Expr, data) -> float:
    x_data = np.array([d[0] for d in data], dtype=float)
    y_data = np.array([d[1] for d in data], dtype=float)
    num_params = count_literals(expr)
    
    if num_params > 0:
        def quick_model(x, *params):
            return np.array([evaluate_tree(expr, xi, params, [0]) for xi in x])
        try:
            popt, _ = curve_fit(quick_model, x_data[:3], y_data[:3], p0=np.ones(num_params), maxfev=100)
            if np.sum(np.abs(y_data[:3] - quick_model(x_data[:3], *popt))) > 50:
                return 5000.0 # Penalty for bad early fit, but not infinity
        except Exception: return 5000.0

    if num_params == 0:
        try:
            predictions = np.array([evaluate_tree(expr, x, [], [0]) for x in x_data])
            total_error = np.sum(np.abs(y_data - predictions))
        except Exception: return 5000.0
    else:
        def model(x, *params):
            return np.array([evaluate_tree(expr, xi, params, [0]) for xi in x])
        try:
            popt, _ = curve_fit(model, x_data, y_data, p0=np.ones(num_params), maxfev=2000)
            predictions = model(x_data, *popt)
            total_error = np.sum(np.abs(y_data - predictions))
            if total_error > 1000: return 5000.0
        except Exception: return 5000.0
            
    return total_error + (expr.size() * 0.5)

if __name__ == "__main__":
    job_id = int(sys.argv[1])
    random.seed(job_id)

    # Generate a random depth, but guarantee it has Input()
    target_ast = generate_target_tree(depth=random.randint(2, 3))
    target_literals = [random.uniform(-5.0, 5.0) for _ in range(len(get_literals(target_ast)))]
    
    x_vals = [float(x) for x in range(1, 11)]
    data = []
    for x in x_vals:
        param_idx = [0]
        y = evaluate_target(target_ast, x, target_literals, param_idx)
        data.append((x, y))

    grammar = extract_grammar([Input, Literal, Add, Multiply] + AVAILABLE_MACROS, Expr)
    
    alg = SimpleGP(
        grammar=grammar,
        fitness_function=lambda expr: fitness_function(expr, data),
        minimize=True,
        population_size=200,
        max_evaluations=2000,
        max_depth=5
    )
    
    best_individuals = alg.search()
    actual_expr = best_individuals[0].get_phenotype()
    
    # We don't know exact evaluations, so we use the time relative to the max as a proxy
    # OR we can just save everything and look at the fitness of the best individual.
    # If the fitness is huge, it failed. If the fitness is tiny, it succeeded.
    final_fitness = fitness_function(actual_expr, data)
    
    os.makedirs("data", exist_ok=True)
    result = {
        "job_id": job_id, 
        "target_ast": str(target_ast),
        "target_size": target_ast.size(),
        "found_ast": str(actual_expr), 
        "found_size": actual_expr.size(),
        "fitness": final_fitness
    }
    with open(f"data/result_{job_id}.json", "w") as f:
        json.dump(result, f)