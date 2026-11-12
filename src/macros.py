from dataclasses import dataclass
from base import Expr, Literal, Input, Add, Multiply

def get_literal(params, param_idx):
    val = params[param_idx[0]]
    param_idx[0] += 1
    return val

AVAILABLE_MACROS = []