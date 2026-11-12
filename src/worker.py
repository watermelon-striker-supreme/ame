import sys
sys.path.append('src') 
import json
import random
import numpy as np
from dataclasses import dataclass
from geml.simplegp import SimpleGP
from geneticengine.grammar.grammar import extract_grammar
from scipy.optimize import curve_fit
import warnings
import time

from base import Expr, Input, Literal, Add, Multiply
from macros import AVAILABLE_MACROS

warnings.filterwarnings("ignore")

def count_nodes(expr: Expr) -> int:
    if isinstance(expr, (Input, Literal)): return 1
    if type(expr).__name__ in [m.__name__ for m in AVAILABLE_MACROS]:
        return 1 + count_nodes(expr.child)
    return 1 + count_nodes(expr.left) + count_nodes(expr.right)

def count_literals(expr: Expr) -> int:
    if isinstance(expr, Literal): return 1
    if isinstance(expr, Input): return 0
    if type(expr).__name__ in [m.__name__ for m in AVAILABLE_MACROS]: 
        return count_literals(expr.child) + 1
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
    
    raise ValueError(f"Unknown expression type: {expr_name}")

def fitness_function(expr: Expr, data) -> float:
    x_data = np.array([d[0] for d in data], dtype=float)
    y_data = np.array([d[1] for d in data], dtype=float)
    num_params = count_literals(expr)
    
    if num_params > 0:
        def quick_model(x, *params):
            return np.array([evaluate_tree(expr, xi, params, [0]) for xi in x])
        try:
            popt, _ = curve_fit(quick_model, x_data[:2], y_data[:2], p0=np.ones(num_params), maxfev=100)
            if np.sum(np.abs(y_data[:2] - quick_model(x_data[:2], *popt))) > 50:
                return 1000000 
        except Exception: return 1000000

    if num_params == 0:
        try:
            predictions = np.array([evaluate_tree(expr, x, [], [0]) for x in x_data])
            total_error = np.sum(np.abs(y_data - predictions))
        except Exception: return 1000000
    else:
        def model(x, *params):
            return np.array([evaluate_tree(expr, xi, params, [0]) for xi in x])
        try:
            popt, _ = curve_fit(model, x_data, y_data, p0=np.ones(num_params), maxfev=2000)
            predictions = model(x_data, *popt)
            total_error = np.sum(np.abs(y_data - predictions))
            if total_error > 1000: return 1000000
        except Exception: return 1000000
            
    return total_error + (count_nodes(expr) * 0.5)

if __name__ == "__main__":
    job_id = int(sys.argv[1])
    random.seed(job_id)
    
    a = random.randint(2, 8)
    b = random.randint(-10, 10)
    data = [(x, a * x + b) for x in range(1, 6)]
    
    grammar = extract_grammar([Input, Literal, Add, Multiply] + AVAILABLE_MACROS, Expr)
    
    start_time = time.time()
    alg = SimpleGP(
        grammar=grammar,
        fitness_function=lambda expr: fitness_function(expr, data),
        minimize=True,
        population_size=200,
        max_evaluations=2000,
        max_depth=4
    )
    
    best_individuals = alg.search()
    actual_expr = best_individuals[0].get_phenotype()
    duration = time.time() - start_time
    
    result = {"job_id": job_id, "target": f"{a}x + {b}", "ast": str(actual_expr), "time": duration}
    
    with open(f"data/result_{job_id}.json", "w") as f:
        json.dump(result, f)